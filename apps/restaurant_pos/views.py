from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import POSOrder, POSSession, Recipe
from .serializers import POSOrderSerializer
from django.utils import timezone

class POSOrderViewSet(viewsets.ModelViewSet):
    queryset = POSOrder.objects.all()
    serializer_class = POSOrderSerializer

    def get_queryset(self):
        opco_id = self.request.query_params.get('opco')
        active_session = self.request.query_params.get('active_session')
        
        if active_session == 'true':
            return POSSession.objects.filter(opco_id=opco_id, is_closed=False)
            
        if opco_id:
            queryset = self.queryset.filter(opco_id=opco_id)
            session_id = self.request.query_params.get('session')
            if session_id:
                queryset = queryset.filter(session_id=session_id)
            return queryset
        return self.queryset

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
        order.save()
        
        # Update session total sales
        session = order.session
        session.total_sales += order.total_amount
        session.save()
        
        try:
            order.deduct_inventory()
            return Response({'success': True, 'order_ref': order.order_ref})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def add_transaction(self, request):
        """إضافة حركة نقدية (مصاريف / مرتجع)"""
        opco_id = request.data.get('opco')
        session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
        if not session:
            return Response({'error': 'No active session'}, status=status.HTTP_400_BAD_REQUEST)
            
        from .models import POSCashTransaction
        trans = POSCashTransaction.objects.create(
            session=session,
            type=request.data.get('type'), # 'IN' or 'OUT'
            amount=request.data.get('amount'),
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
        from django.db.models import Sum, Count
        from django.utils import timezone
        
        today = timezone.now().date()
        orders = POSOrder.objects.filter(opco_id=opco_id, status='paid', created_at__date=today)
        
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
            recipe = getattr(line.material, 'recipe', None)
            if recipe:
                for ing in recipe.ingredients.all():
                    name = ing.ingredient.name
                    if name not in consumption:
                        consumption[name] = {'name': name, 'total_qty': 0, 'uom': ing.uom}
                    consumption[name]['total_qty'] += ing.quantity * line.qty
        
        return Response({
            'total_revenue': total_revenue,
            'cash_total': cash_total,
            'credit_total': credit_total,
            'instapay_total': instapay_total,
            'top_items': top_items,
            'ingredients': list(consumption.values())
        })

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
        orders = POSOrder.objects.filter(session=session, status='paid')
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
        orders = POSOrder.objects.filter(session=session, status='paid')
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
