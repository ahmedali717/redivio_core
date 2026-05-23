from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import POSOrder, POSSession, Recipe, RestaurantFloor, RestaurantTable
from .serializers import POSOrderSerializer, RestaurantFloorSerializer, RestaurantTableSerializer
from django.utils import timezone

class POSOrderViewSet(viewsets.ModelViewSet):
    queryset = POSOrder.objects.all()
    serializer_class = POSOrderSerializer

    def get_queryset(self):
        opco_id = self.request.query_params.get('opco')
        
        # Safe opco_id conversion
        clean_opco_id = None
        if opco_id and opco_id != 'null':
            try:
                clean_opco_id = int(opco_id)
            except (ValueError, TypeError):
                pass

        queryset = self.queryset
        if clean_opco_id:
            queryset = queryset.filter(opco_id=clean_opco_id)
            
        session_id = self.request.query_params.get('session')
        if session_id and session_id != 'null':
            queryset = queryset.filter(session_id=session_id)
            
        return queryset

    @action(detail=False, methods=['get'])
    def active_session(self, request):
        opco_id = request.query_params.get('opco')
        session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
        if session:
            from .serializers import POSSessionSerializer
            return Response(POSSessionSerializer(session).data)
        return Response(None, status=200)

    @action(detail=False, methods=['get'])
    def session_history(self, request):
        opco_id = request.query_params.get('opco')
        sessions = POSSession.objects.filter(opco_id=opco_id).order_by('-start_time')
        data = []
        for s in sessions:
            data.append({
                'id': s.id,
                'cashier': s.cashier_name,
                'start_time': s.start_time,
                'end_time': s.end_time,
                'is_closed': s.is_closed,
                'total_sales': s.total_sales,
                'opening_balance': s.opening_balance,
                'actual_balance': s.actual_closing_balance,
                'order_count': s.orders.count()
            })
        return Response(data)

    @action(detail=False, methods=['post'])
    def start_session(self, request):
        opco_id = request.data.get('opco')
        cashier_name = request.data.get('cashier_name', 'Admin')
        opening_balance = request.data.get('opening_balance', 0)
        
        # Close previous sessions for this OpCo
        POSSession.objects.filter(opco_id=opco_id, is_closed=False).update(is_closed=True, end_time=timezone.now())
        
        session = POSSession.objects.create(
            opco_id=opco_id,
            cashier_name=cashier_name,
            opening_balance=opening_balance,
            is_closed=False
        )
        from .serializers import POSSessionSerializer
        return Response(POSSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        order = self.get_object()
        if order.status != 'draft':
            return Response({'error': 'Order already processed'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.status = 'paid'
        order.kitchen_received_at = timezone.now()
        order.save()
        
        # Update session total sales
        session = order.session
        session.total_sales += order.total_amount
        session.save()
        
        # Free the table if this was a Dine-In order
        if order.order_type == 'DINE_IN' and order.table_number:
            try:
                table = RestaurantTable.objects.filter(opco=order.opco, number=order.table_number).first()
                if table:
                    table.status = 'cleaning'
                    table.active_order = None
                    table.current_guests = 0
                    table.save()
            except Exception as e:
                print("Error freeing table during checkout:", e)
        
        try:
            order.deduct_inventory()
            return Response({'success': True, 'order_ref': order.order_ref})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def kds_orders(self, request):
        """جلب طلبات المطبخ الخاصة بمجموعة الطعام (Food)"""
        opco_id = request.query_params.get('opco')
        
        # فلترة الطلبات التي لم تنتهِ بعد
        queryset = POSOrder.objects.filter(
            opco_id=opco_id, 
            status__in=['paid', 'inprogress']
        ).prefetch_related('lines', 'lines__material', 'lines__material__sale_group').order_by('created_at')
        
        data = []
        for order in queryset:
            # فلترة الأصناف التي تنتمي لمجموعة الطعام باللغة العربية أو الإنجليزية
            from django.db.models import Q
            food_lines = order.lines.filter(
                Q(material__sale_group__name__icontains='Food') |
                Q(material__sale_group__name__icontains='طعام')
            )
            
            if food_lines.exists():
                lines = []
                for line in food_lines:
                    lines.append({
                        'id': line.id,
                        'name': line.material.name,
                        'qty': line.qty,
                        'notes': line.kitchen_notes,
                        'group': line.material.sale_group.name if line.material.sale_group else 'Other'
                    })
                
                data.append({
                    'id': order.id,
                    'order_ref': order.order_ref,
                    'status': order.status,
                    'order_type': order.order_type,
                    'table': order.table_number,
                    'created_at': order.created_at,
                    'received_at': order.kitchen_received_at,
                    'started_at': order.kitchen_started_at,
                    'lines': lines
                })
        return Response(data)

    @action(detail=True, methods=['post'])
    def update_kitchen_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in ['inprogress', 'done', 'cancelled']:
            return Response({'error': 'Invalid status'}, status=400)
            
        order.status = new_status
        if new_status == 'inprogress':
            order.kitchen_started_at = timezone.now()
        elif new_status == 'done':
            order.kitchen_done_at = timezone.now()
        elif new_status == 'cancelled':
            order.kitchen_cancelled_at = timezone.now()
            
        order.save()
        return Response({'success': True})

    @action(detail=False, methods=['post'])
    def add_transaction(self, request):
        """تسجيل حركة نقدية (مصروفات / توريد)"""
        opco_id = request.data.get('opco')
        session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
        if not session:
            return Response({'error': 'No active session'}, status=status.HTTP_400_BAD_REQUEST)
            
        from .models import POSCashTransaction
        from decimal import Decimal
        
        try:
            amount = Decimal(str(request.data.get('amount', 0)))
        except:
            return Response({'error': 'Invalid amount'}, status=400)

        trans = POSCashTransaction.objects.create(
            session=session,
            type=request.data.get('type'), # 'IN' or 'OUT'
            amount=amount,
            reason=request.data.get('reason')
        )
        
        if trans.type == 'OUT':
            session.total_expenses += trans.amount
        session.save()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def refund_order(self, request, pk=None):
        """إرجاع فاتورة بالكامل"""
        order = self.get_object()
        if order.is_refunded:
            return Response({'error': 'Order already refunded'}, status=status.HTTP_400_BAD_REQUEST)
            
        order.status = 'refunded'
        order.is_refunded = True
        order.save()
        
        # إذا كان الدفع كاش، نقوم بإخراج المبلغ من الدرج وتسجيل حركة
        if order.payment_method == 'cash':
            from .models import POSCashTransaction
            POSCashTransaction.objects.create(
                session=order.session,
                type='OUT',
                amount=order.total_amount,
                reason=f"Refund Order {order.order_ref}"
            )
            order.session.total_expenses += order.total_amount
            order.session.save()
            
        return Response({'success': True})

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        opco_id = request.query_params.get('opco')
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        
        from django.db.models import Sum, Count, Q
        from django.utils import timezone
        
        today = timezone.now().date()
        # Inclusion of all successful statuses to prevent sales disappearing from analytics
        valid_statuses = ['paid', 'inprogress', 'done']
        orders = POSOrder.objects.filter(opco_id=opco_id, status__in=valid_statuses)
        
        if date_from:
            orders = orders.filter(created_at__date__gte=date_from)
        if date_to:
            orders = orders.filter(created_at__date__lte=date_to)
        if not date_from and not date_to:
            orders = orders.filter(created_at__date=today)
        
        # 1. Financial Stats
        total_revenue = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        cash_total = orders.filter(payment_method='cash').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        credit_total = orders.filter(payment_method='credit').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        instapay_total = orders.filter(payment_method='instapay').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # 2. Top Items
        from .models import POSOrderLine
        top_items_raw = POSOrderLine.objects.filter(order__in=orders).values('material__name').annotate(total_qty=Sum('qty')).order_by('-total_qty')[:5]
        top_items = []
        max_qty = top_items_raw[0]['total_qty'] if top_items_raw else 1
        for i, item in enumerate(top_items_raw):
            top_items.append({
                'rank': i + 1,
                'name': item['material__name'],
                'qty': item['total_qty'],
                'percentage': (item['total_qty'] / max_qty) * 100
            })

        # 3. Ingredient Consumption (BOM)
        from .models import RecipeItem
        consumption = {}
        for line in POSOrderLine.objects.filter(order__in=orders):
            recipe = None
            try:
                recipe = line.material.recipe
            except:
                recipe = None

            if recipe and recipe.ingredients.exists():
                for ing in recipe.ingredients.all():
                    name = ing.ingredient.name
                    if name not in consumption:
                        consumption[name] = {'name': name, 'total_qty': 0, 'uom': ing.uom}
                    consumption[name]['total_qty'] += float(ing.quantity) * float(line.qty)
            else:
                # المنتجات التي ليس لها وصفة (أو وصفة فارغة مثل بيبسي/مياه)
                if line.material.is_pos_item:
                    name = line.material.name
                    if name not in consumption:
                        consumption[name] = {'name': name, 'total_qty': 0, 'uom': line.material.base_uom}
                    consumption[name]['total_qty'] += float(line.qty)
        
        # 4. Expenses & Profitability Stats
        from .models import POSCashTransaction
        expenses_qs = POSCashTransaction.objects.filter(session__opco_id=opco_id, type='OUT')
        if date_from:
            expenses_qs = expenses_qs.filter(created_at__date__gte=date_from)
        if date_to:
            expenses_qs = expenses_qs.filter(created_at__date__lte=date_to)
        if not date_from and not date_to:
            expenses_qs = expenses_qs.filter(created_at__date=today)

        total_expenses = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Get opening balance for the first session in the range
        first_session = POSSession.objects.filter(opco_id=opco_id)
        if date_from:
            first_session = first_session.filter(start_time__date__gte=date_from)
        if date_to:
            first_session = first_session.filter(start_time__date__lte=date_to)
        if not date_from and not date_to:
            first_session = first_session.filter(start_time__date=today)
        
        opening_balance = first_session.order_by('start_time').first().opening_balance if first_session.exists() else 0
        
        from django.db.models import F
        from apps.wms.models import StockMove
        total_purchases = StockMove.objects.filter(opco_id=opco_id, move_type='IN', created_at__date=today).aggregate(
            total=Sum(F('quantity') * F('unit_cost'))
        )['total'] or 0

        total_cogs = POSOrderLine.objects.filter(order__in=orders).aggregate(
            total=Sum(F('qty') * F('material__standard_price'))
        )['total'] or 0

        return Response({
            'total_revenue': float(total_revenue),
            'cash_sales': float(cash_total),
            'credit_sales': float(credit_total),
            'instapay_sales': float(instapay_total),
            'total_expenses': float(total_expenses),
            'total_purchases': float(total_purchases),
            'total_cogs': float(total_cogs),
            'opening_balance': float(opening_balance),
            'gross_profit': float(total_revenue) - float(total_cogs),
            'net_income': float(opening_balance) + float(cash_total) - float(total_expenses) - float(total_purchases),
            'net_profit': float(total_revenue) - float(total_cogs) - float(total_expenses),
            'top_items': top_items,
            'ingredients': list(consumption.values())
        })

    @action(detail=False, methods=['get'])
    def cash_transactions(self, request):
        """جلب الحركات النقدية (المصروفات) للوردية الحالية أو لشركة معينة"""
        opco_id = request.query_params.get('opco')
        session_id = request.query_params.get('session')
        
        from .models import POSCashTransaction
        queryset = POSCashTransaction.objects.filter(session__opco_id=opco_id)
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        else:
            # افتراضياً نجلب حركات الوردية المفتوحة
            queryset = queryset.filter(session__is_closed=False)
            
        data = [{
            'id': t.id,
            'type': t.type,
            'amount': float(t.amount),
            'reason': t.reason,
            'created_at': t.created_at,
            'cashier': t.session.cashier_name,
            'is_transaction': True # علم لتمييزها في الواجهة
        } for t in queryset.order_by('-created_at')]
        
        return Response(data)

    @action(detail=False, methods=['get'])
    def last_session_balance(self, request):
        opco_id = request.query_params.get('opco')
        from .models import POSSession
        last_session = POSSession.objects.filter(opco_id=opco_id, is_closed=True).order_by('-end_time').first()
        balance = last_session.actual_closing_balance if last_session else 0
        return Response({'last_balance': balance})

    @action(detail=False, methods=['get'])
    def session_preview(self, request):
        opco_id = request.query_params.get('opco')
        session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
        if not session:
            return Response({'error': 'No active session'}, status=status.HTTP_400_BAD_REQUEST)
        
        from .models import POSOrder
        from django.db.models import Sum
        valid_statuses = ['paid', 'inprogress', 'done']
        orders = POSOrder.objects.filter(session=session, status__in=valid_statuses)
        total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        cash_sales = orders.filter(payment_method='cash').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        instapay_sales = orders.filter(payment_method='instapay').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        credit_sales = orders.filter(payment_method='credit').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        return Response({
            'opening_balance': session.opening_balance,
            'total_sales': total_sales,
            'cash_sales': cash_sales,
            'instapay_sales': instapay_sales,
            'credit_sales': credit_sales,
            'total_expenses': session.total_expenses,
            'expected_cash': float(session.opening_balance) + float(cash_sales) - float(session.total_expenses),
            'cashier': session.cashier_name
        })

    @action(detail=False, methods=['post'])
    def close_session(self, request):
        opco_id = request.data.get('opco')
        actual_balance = float(request.data.get('actual_balance', 0))
        session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
        
        if not session:
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)

        from .models import POSOrder
        from django.db.models import Sum
        valid_statuses = ['paid', 'inprogress', 'done']
        orders = POSOrder.objects.filter(session=session, status__in=valid_statuses)
        cash_sales = orders.filter(payment_method='cash').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_sales = orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        session.actual_closing_balance = actual_balance
        session.total_sales = total_sales
        session.expected_closing_balance = float(session.opening_balance) + float(cash_sales) - float(session.total_expenses)
        
        session.is_closed = True
        session.end_time = timezone.now()
        session.save()
        
        return Response({
            'success': True, 
            'session_id': session.id,
            'opening_balance': session.opening_balance,
            'total_sales': total_sales,
            'cash_sales': cash_sales,
            'total_expenses': session.total_expenses,
            'expected_balance': session.expected_closing_balance,
            'actual_balance': session.actual_closing_balance,
            'difference': float(session.actual_closing_balance) - float(session.expected_closing_balance),
            'cashier': session.cashier_name
        })


class RestaurantFloorViewSet(viewsets.ModelViewSet):
    queryset = RestaurantFloor.objects.all()
    serializer_class = RestaurantFloorSerializer

    def get_queryset(self):
        opco_id = self.request.query_params.get('opco')
        queryset = self.queryset
        if opco_id and opco_id != 'null':
            try:
                queryset = queryset.filter(opco_id=int(opco_id))
            except ValueError:
                pass
        return queryset.order_by('number')


class RestaurantTableViewSet(viewsets.ModelViewSet):
    queryset = RestaurantTable.objects.all()
    serializer_class = RestaurantTableSerializer

    def get_queryset(self):
        opco_id = self.request.query_params.get('opco')
        queryset = self.queryset
        if opco_id and opco_id != 'null':
            try:
                queryset = queryset.filter(opco_id=int(opco_id))
            except ValueError:
                pass
        return queryset.order_by('number')

    @action(detail=True, methods=['post'])
    def assign_order(self, request, pk=None):
        table = self.get_object()
        order_id = request.data.get('order_id')
        current_guests = request.data.get('current_guests', 0)
        table.status = 'occupied'
        if order_id:
            table.active_order_id = int(order_id)
        if current_guests:
            table.current_guests = int(current_guests)
        table.save()
        return Response({'success': True})

    @action(detail=True, methods=['post'])
    def release_table(self, request, pk=None):
        table = self.get_object()
        table.status = 'available'
        table.active_order = None
        table.current_guests = 0
        table.save()
        return Response({'success': True})

