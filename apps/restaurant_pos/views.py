from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import POSOrder, POSSession, Recipe, RestaurantFloor, RestaurantTable, POSTerminal, PromoCode
from .serializers import POSOrderSerializer, RestaurantFloorSerializer, RestaurantTableSerializer, POSTerminalSerializer, PromoCodeSerializer
from django.utils import timezone

class POSOrderViewSet(viewsets.ModelViewSet):
    queryset = POSOrder.objects.all()
    serializer_class = POSOrderSerializer

    # الحقول الأساسية الموجودة دائماً (قبل أي migration جديد)
    _CORE_FIELDS = [
        'id', 'opco_id', 'session_id', 'order_ref', 'order_type',
        'table_number', 'guest_count', 'total_amount', 'payment_method',
        'status', 'created_at', 'inventory_deducted',
        'kitchen_received_at', 'kitchen_started_at', 'kitchen_done_at', 'kitchen_cancelled_at',
        'is_refunded',
    ]

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

    def list(self, request, *args, **kwargs):
        """Override list to gracefully handle missing DB columns (unapplied migrations)."""
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            err_str = str(e).lower()
            if 'no such column' in err_str or 'column' in err_str or 'does not exist' in err_str:
                # Fallback: return only core fields, ignore new columns
                qs = self.get_queryset().only(*self._CORE_FIELDS)
                from .serializers import POSOrderFallbackSerializer
                data = POSOrderFallbackSerializer(qs, many=True).data
                return Response(data)
            raise

    @action(detail=False, methods=['get'])
    def active_session(self, request):
        opco_id = request.query_params.get('opco')
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response({}, status=200)
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response({}, status=200)
            
        terminal_id = request.query_params.get('terminal')
        
        # Enforce terminal access permission check if a terminal is requested
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            try:
                t_id = int(terminal_id)
                terminal = POSTerminal.objects.filter(id=t_id).first()
                if terminal and terminal.allowed_users.exists():
                    user_to_check = request.user
                    if user_to_check and not user_to_check.is_superuser:
                        if not terminal.allowed_users.filter(id=user_to_check.id).exists():
                            is_ar = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
                            err_msg = 'ليس لديك صلاحية للدخول إلى نقطة البيع هذه.' if is_ar else 'You do not have permission to access this POS terminal.'
                            return Response({'error': err_msg}, status=status.HTTP_403_FORBIDDEN)
            except (ValueError, TypeError):
                pass

        session_qs = POSSession.objects.filter(opco_id=opco_id, is_closed=False)
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            session_qs = session_qs.filter(terminal_id=terminal_id)
            
        # Filter session_qs so non-superusers only see sessions for terminals they are allowed to access
        user = request.user
        if user and not user.is_superuser:
            from django.db.models import Q
            session_qs = session_qs.filter(
                Q(terminal__isnull=True) | Q(terminal__allowed_users__isnull=True) | Q(terminal__allowed_users=user)
            ).distinct()
            
        session = session_qs.first()
        if session:
            from .serializers import POSSessionSerializer
            return Response(POSSessionSerializer(session).data)
        return Response({}, status=200)

    @action(detail=False, methods=['get'])
    def session_history(self, request):
        opco_id = request.query_params.get('opco')
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response([])
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response([])
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
        opco_id = request.data.get('opco') or request.session.get('active_opco_id')
        if opco_id:
            try:
                opco_id = int(opco_id)
            except (ValueError, TypeError):
                opco_id = None

        if not opco_id:
            return Response({'error': 'اسم الشركة (OpCo) مطلوب لبدء الوردية.'}, status=status.HTTP_400_BAD_REQUEST)

        cashier_name = request.data.get('cashier_name', 'Admin')
        opening_balance = request.data.get('opening_balance', 0)
        
        terminal_id = request.data.get('terminal')
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            try:
                terminal_id = int(terminal_id)
            except (ValueError, TypeError):
                terminal_id = None
        else:
            terminal_id = None

        cashier_id = request.data.get('cashier_id')
        if cashier_id and cashier_id not in ['null', 'undefined', '']:
            try:
                cashier_id = int(cashier_id)
            except (ValueError, TypeError):
                cashier_id = None
        else:
            cashier_id = None
        
        # Resolve cashier_id (CompanyUser ID) to the actual Django User object
        from apps.core.models import CompanyUser
        cashier_user = None
        if cashier_id:
            cu = CompanyUser.objects.filter(id=cashier_id).first()
            if cu:
                cashier_user = cu.user
                
        # Enforce terminal access permission
        if terminal_id:
            terminal = POSTerminal.objects.filter(id=terminal_id).first()
            if not terminal:
                return Response({'error': 'نقطة البيع المحددة غير موجودة.'}, status=status.HTTP_400_BAD_REQUEST)
            if terminal.allowed_users.exists():
                user_to_check = cashier_user or request.user
                if user_to_check and not user_to_check.is_superuser:
                    if not terminal.allowed_users.filter(id=user_to_check.id).exists():
                        return Response({
                            'error': 'ليس لديك صلاحية لفتح نقطة البيع هذه.'
                        }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if there is already an active session for this terminal to prevent duplicate sessions
        if terminal_id:
            existing_session = POSSession.objects.filter(opco_id=opco_id, terminal_id=terminal_id, is_closed=False).first()
        else:
            existing_session = POSSession.objects.filter(opco_id=opco_id, terminal_id__isnull=True, is_closed=False).first()
            
        if existing_session:
            from .serializers import POSSessionSerializer
            return Response(POSSessionSerializer(existing_session).data)

        # Close previous sessions for this terminal / OpCo (as safety fallback)
        if terminal_id:
            POSSession.objects.filter(opco_id=opco_id, terminal_id=terminal_id, is_closed=False).update(is_closed=True, end_time=timezone.now())
        else:
            POSSession.objects.filter(opco_id=opco_id, is_closed=False).update(is_closed=True, end_time=timezone.now())
        
        session = POSSession.objects.create(
            opco_id=opco_id,
            cashier_name=cashier_name,
            opening_balance=opening_balance,
            terminal_id=terminal_id,
            is_closed=False
        )
        from .serializers import POSSessionSerializer
        return Response(POSSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        order = self.get_object()
        # Enforce inventory freeze
        if order.opco.is_inventory_active:
            is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
            err_msg = "لا يمكن إتمام البيع حالياً لوجود عملية جرد مخزني نشطة." if is_arabic else "Cannot process payment. Inventory count is currently active and stock movements are frozen."
            return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)

        # Allow processing payment for unpaid orders (draft, inprogress, done)
        if order.status in ['paid', 'refunded', 'cancelled']:
            return Response({'error': 'Order already processed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Allow updating payment method from request
        payment_method = request.data.get('payment_method')
        if payment_method:
            order.payment_method = payment_method

        # Update delivery customer info if provided
        customer_name = request.data.get('customer_name')
        customer_phone = request.data.get('customer_phone')
        customer_address = request.data.get('customer_address')
        delivery_notes = request.data.get('delivery_notes')
        if customer_name:
            order.customer_name = customer_name
        if customer_phone:
            order.customer_phone = customer_phone
        if customer_address:
            order.customer_address = customer_address
        if delivery_notes:
            order.delivery_notes = delivery_notes
        
        # Update status: only change to 'paid' if it wasn't already in progress or done in the kitchen
        if order.status not in ['inprogress', 'done']:
            order.status = 'paid'
            order.kitchen_received_at = timezone.now()
        
        order.save()
        
        # 🚚 إنشاء / ربط عميل في موديول المبيعات لطلبات التوصيل
        if order.order_type == 'DELIVERY' and order.customer_phone:
            try:
                from apps.sales.models import Customer
                import re
                # توليد كود العميل من رقم التليفون
                phone_clean = re.sub(r'\D', '', order.customer_phone)
                customer_code = f"POS-{phone_clean}"
                customer, created = Customer.objects.get_or_create(
                    opco=order.opco,
                    code=customer_code,
                    defaults={
                        'name': order.customer_name or order.customer_phone,
                        'phone': order.customer_phone,
                        'address': order.customer_address or '',
                    }
                )
                # تحديث البيانات لو العميل موجود مسبقاً
                if not created and order.customer_name:
                    customer.name = order.customer_name
                    customer.address = order.customer_address or customer.address
                    customer.save()
                order.sales_customer = customer
                order.save()
            except Exception as e:
                print(f"Warning: Could not link delivery customer to sales: {e}")

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

    @action(detail=False, methods=['post'])
    def save_dine_in(self, request):
        """
        Save a Dine-In order as DRAFT (send to kitchen) without processing payment.
        Links the order to the table. The order stays open until the customer requests the bill.
        """
        from .models import POSOrderLine
        data = request.data
        opco_id = data.get('opco')
        
        # Enforce inventory freeze
        if opco_id:
            try:
                opco = OpCo.objects.filter(id=opco_id).first()
                if opco and opco.is_inventory_active:
                    is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
                    err_msg = "لا يمكن إتمام العملية حالياً لوجود عملية جرد مخزني نشطة." if is_arabic else "Cannot perform operation. Inventory count is currently active and stock movements are frozen."
                    return Response({'error': err_msg}, status=status.HTTP_400_BAD_REQUEST)
            except:
                pass
        session_id = data.get('session')
        table_number = data.get('table_number')
        guest_count = data.get('guest_count', 1)
        lines_data = data.get('lines', [])
        existing_order_id = data.get('existing_order_id')  # If updating an existing draft

        if not opco_id or not session_id:
            return Response({'error': 'opco and session are required'}, status=status.HTTP_400_BAD_REQUEST)

        # If an existing draft order, update it
        if existing_order_id:
            try:
                order = POSOrder.objects.get(id=existing_order_id, status__in=['draft', 'inprogress', 'done'])
                # Delete old lines and replace
                order.lines.all().delete()
                total = 0
                for line_data in lines_data:
                    subtotal = float(line_data.get('subtotal', 0))
                    total += subtotal
                    POSOrderLine.objects.create(
                        order=order,
                        material_id=line_data['material'],
                        qty=line_data['qty'],
                        unit_price=line_data['unit_price'],
                        subtotal=subtotal,
                        kitchen_notes=line_data.get('kitchen_notes', '')
                    )
                order.total_amount = total
                order.guest_count = guest_count
                order.save()
                serializer = POSOrderSerializer(order)
                return Response(serializer.data)
            except POSOrder.DoesNotExist:
                pass  # Fall through to create new

        # Create a new draft order
        total = sum(float(l.get('subtotal', 0)) for l in lines_data)
        order = POSOrder.objects.create(
            opco_id=opco_id,
            session_id=session_id,
            order_type='DINE_IN',
            table_number=table_number,
            guest_count=guest_count,
            total_amount=total,
            payment_method='cash',  # Default, will be set on checkout
            status='draft'
        )
        for line_data in lines_data:
            POSOrderLine.objects.create(
                order=order,
                material_id=line_data['material'],
                qty=line_data['qty'],
                unit_price=line_data['unit_price'],
                subtotal=float(line_data.get('subtotal', 0)),
                kitchen_notes=line_data.get('kitchen_notes', '')
            )

        # Link order to table
        if table_number:
            try:
                table = RestaurantTable.objects.filter(opco_id=opco_id, number=table_number).first()
                if table:
                    table.active_order = order
                    table.status = 'occupied'
                    table.current_guests = guest_count
                    table.save()
            except Exception as e:
                print("Error linking order to table:", e)

        serializer = POSOrderSerializer(order)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def kds_orders(self, request):
        """جلب طلبات المطبخ الخاصة بمجموعة الطعام (Food)"""
        opco_id = request.query_params.get('opco')
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response([])
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response([])
        
        # فلترة الطلبات التي لم تنتهِ بعد (تشمل الطلبات غير المدفوعة للمحلي المسودة والطلبات الجاهزة خلال آخر ساعتين)
        from django.db.models import Q
        from django.utils import timezone
        import datetime
        two_hours_ago = timezone.now() - datetime.timedelta(hours=2)
        
        queryset = POSOrder.objects.filter(
            Q(status__in=['paid', 'inprogress']) | 
            Q(status='draft', order_type='DINE_IN') |
            Q(status='done', kitchen_done_at__gte=two_hours_ago),
            opco_id=opco_id
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
        terminal_id = request.data.get('terminal')
        session_qs = POSSession.objects.filter(opco_id=opco_id, is_closed=False)
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            session_qs = session_qs.filter(terminal_id=terminal_id)
        session = session_qs.first()
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
        
        default_stats = {
            'total_revenue': 0.0,
            'cash_sales': 0.0,
            'credit_sales': 0.0,
            'instapay_sales': 0.0,
            'total_expenses': 0.0,
            'total_inflows': 0.0,
            'total_purchases': 0.0,
            'total_cogs': 0.0,
            'opening_balance': 0.0,
            'gross_profit': 0.0,
            'net_income': 0.0,
            'net_profit': 0.0,
            'top_items': [],
            'ingredients': [],
            'cash_transactions': []
        }
        
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response(default_stats)
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response(default_stats)
            
        from django.db.models import Sum, Count, Q, F
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
        top_items_raw = POSOrderLine.objects.filter(order__in=orders).values(
            'material__name', 
            'material__sale_group__name'
        ).annotate(
            total_qty=Sum('qty'),
            total_sales=Sum('subtotal'),
            total_cost=Sum(F('qty') * F('material__standard_price'))
        ).order_by('-total_qty')
        
        top_items = []
        max_qty = top_items_raw[0]['total_qty'] if top_items_raw else 1
        for i, item in enumerate(top_items_raw):
            top_items.append({
                'rank': i + 1,
                'name': item['material__name'],
                'category': item['material__sale_group__name'] or 'عام',
                'qty': item['total_qty'],
                'total_sales': float(item['total_sales'] or 0),
                'total_cost': float(item['total_cost'] or 0),
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
        inflow_qs = POSCashTransaction.objects.filter(session__opco_id=opco_id, type='IN')
        if date_from:
            expenses_qs = expenses_qs.filter(created_at__date__gte=date_from)
            inflow_qs = inflow_qs.filter(created_at__date__gte=date_from)
        if date_to:
            expenses_qs = expenses_qs.filter(created_at__date__lte=date_to)
            inflow_qs = inflow_qs.filter(created_at__date__lte=date_to)
        if not date_from and not date_to:
            expenses_qs = expenses_qs.filter(created_at__date=today)
            inflow_qs = inflow_qs.filter(created_at__date=today)

        total_expenses = expenses_qs.aggregate(Sum('amount'))['amount__sum'] or 0
        total_inflow = inflow_qs.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Detailed Cash transactions list
        trans_qs = POSCashTransaction.objects.filter(session__opco_id=opco_id)
        if date_from:
            trans_qs = trans_qs.filter(created_at__date__gte=date_from)
        if date_to:
            trans_qs = trans_qs.filter(created_at__date__lte=date_to)
        if not date_from and not date_to:
            trans_qs = trans_qs.filter(created_at__date=today)
            
        cash_trans = [{
            'id': t.id,
            'type': t.type,
            'amount': float(t.amount),
            'reason': t.reason,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'cashier': t.session.cashier_name
        } for t in trans_qs.order_by('-created_at')]
        
        # Get opening balance for the first session in the range
        first_session = POSSession.objects.filter(opco_id=opco_id)
        if date_from:
            first_session = first_session.filter(start_time__date__gte=date_from)
        if date_to:
            first_session = first_session.filter(start_time__date__lte=date_to)
        if not date_from and not date_to:
            first_session = first_session.filter(start_time__date=today)
        
        opening_balance = first_session.order_by('start_time').first().opening_balance if first_session.exists() else 0
        
        from apps.wms.models import StockMove
        purchases_qs = StockMove.objects.filter(opco_id=opco_id, move_type='IN')
        if date_from:
            purchases_qs = purchases_qs.filter(created_at__date__gte=date_from)
        if date_to:
            purchases_qs = purchases_qs.filter(created_at__date__lte=date_to)
        if not date_from and not date_to:
            purchases_qs = purchases_qs.filter(created_at__date=today)
            
        total_purchases = purchases_qs.aggregate(
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
            'total_inflows': float(total_inflow),
            'total_purchases': float(total_purchases),
            'total_cogs': float(total_cogs),
            'opening_balance': float(opening_balance),
            'gross_profit': float(total_revenue) - float(total_cogs),
            'net_income': float(opening_balance) + float(cash_total) + float(total_inflow) - float(total_expenses) - float(total_purchases),
            'net_profit': float(total_revenue) - float(total_cogs) - float(total_expenses),
            'top_items': top_items,
            'ingredients': list(consumption.values()),
            'cash_transactions': cash_trans
        })

    @action(detail=False, methods=['get'])
    def cash_transactions(self, request):
        """جلب الحركات النقدية (المصروفات) للوردية الحالية أو لشركة معينة"""
        opco_id = request.query_params.get('opco')
        session_id = request.query_params.get('session')
        
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response([])
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response([])
            
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
        terminal_id = request.query_params.get('terminal')  # الـ terminal المحدد
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response({'last_balance': 0.0})
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response({'last_balance': 0.0})

        from .models import POSSession
        qs = POSSession.objects.filter(opco_id=opco_id, is_closed=True)

        # فلترة بالـ terminal لو اتبعت — كل POS يشوف وردياته هو بس
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            try:
                qs = qs.filter(terminal_id=int(terminal_id))
            except (ValueError, TypeError):
                pass

        last_session = qs.order_by('-end_time').first()
        balance = float(last_session.actual_closing_balance) if last_session else 0.0
        return Response({'last_balance': balance})

    @action(detail=False, methods=['get'])
    def session_preview(self, request):
        opco_id = request.query_params.get('opco')
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response({'error': 'No active session'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response({'error': 'No active session'}, status=status.HTTP_400_BAD_REQUEST)
            
        terminal_id = request.query_params.get('terminal')
        session_qs = POSSession.objects.filter(opco_id=opco_id, is_closed=False)
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            session_qs = session_qs.filter(terminal_id=terminal_id)
        session = session_qs.first()
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
        if not opco_id or opco_id in ['null', 'undefined']:
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)
            
        actual_balance = float(request.data.get('actual_balance', 0))
        terminal_id = request.data.get('terminal')
        session_qs = POSSession.objects.filter(opco_id=opco_id, is_closed=False)
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            session_qs = session_qs.filter(terminal_id=terminal_id)
        session = session_qs.first()
        
        if not session:
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)

        from django.db.models import Sum

        # ✋ منع إغلاق الوردية إذا كان هناك أوردر مفتوح (مسودة أو قيد التحضير)
        open_orders = POSOrder.objects.filter(session=session, status__in=['draft', 'inprogress'])
        if open_orders.exists():
            open_count = open_orders.count()
            return Response(
                {'error': f'لا يمكن إغلاق الوردية! يوجد {open_count} طلب مفتوح لم يتم تسويته بعد. يرجى إتمام أو إلغاء جميع الطلبات المفتوحة قبل إغلاق الوردية.'},
                status=status.HTTP_400_BAD_REQUEST
            )

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


class POSTerminalViewSet(viewsets.ModelViewSet):
    queryset = POSTerminal.objects.all()
    serializer_class = POSTerminalSerializer

    def get_queryset(self):
        if self.action in ['retrieve', 'update', 'partial_update', 'destroy'] or getattr(self, 'detail', False):
            return POSTerminal.objects.all()

        opco_id = self.request.query_params.get('opco')
        if not opco_id or opco_id in ['null', 'undefined']:
            return POSTerminal.objects.none()
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return POSTerminal.objects.none()
            
        queryset = POSTerminal.objects.filter(opco_id=opco_id)
        
        # Enforce terminal access permission filter
        user = self.request.user
        if user and not user.is_superuser:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(allowed_users__isnull=True) | Q(allowed_users=user)
            ).distinct()

        if not queryset.exists():
            # Auto-create a default terminal
            from apps.core.models import OpCo
            opco = OpCo.objects.filter(id=opco_id).first()
            if opco:
                POSTerminal.objects.create(
                    opco=opco,
                    name="Main Terminal (نقطة البيع الرئيسية)",
                    code="POS-01",
                    terminal_type="RESTAURANT"
                )
                queryset = POSTerminal.objects.filter(opco_id=opco_id)
                if user and not user.is_superuser:
                    queryset = queryset.filter(
                        Q(allowed_users__isnull=True) | Q(allowed_users=user)
                    ).distinct()
        return queryset.order_by('code')


class PromoCodeViewSet(viewsets.ModelViewSet):
    """
    إدارة أكواد العروض
    """
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer

    def get_queryset(self):
        opco_id = self.request.query_params.get('opco')
        if not opco_id or opco_id in ['null', 'undefined']:
            return PromoCode.objects.none()
        try:
            opco_id = int(opco_id)
        except (ValueError, TypeError):
            return PromoCode.objects.none()
        return PromoCode.objects.filter(opco_id=opco_id).order_by('code')

    @action(detail=False, methods=['post'])
    def validate_code(self, request):
        """
        التحقق من صحة كود العرض وإرجاع بيانات الخصم
        """
        from django.utils import timezone as tz
        opco_id = request.data.get('opco')
        code_text = (request.data.get('code') or '').strip().upper()
        order_total = float(request.data.get('order_total', 0))

        if not opco_id or not code_text:
            return Response({'error': 'بيانات ناقصة'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            promo = PromoCode.objects.get(opco_id=opco_id, code__iexact=code_text, is_active=True)
        except PromoCode.DoesNotExist:
            return Response({'error': 'كود العرض غير صحيح أو غير نشط.'}, status=status.HTTP_400_BAD_REQUEST)

        # التحقق من تاريخ انتهاء العرض
        if promo.expires_at and promo.expires_at < tz.now():
            return Response({'error': 'كود العرض منتهي الصلاحية.'}, status=status.HTTP_400_BAD_REQUEST)

        # التحقق من عدد الاستخدامات
        if promo.max_uses > 0 and promo.used_count >= promo.max_uses:
            return Response({'error': 'تم استخدام كود العرض بالكامل.'}, status=status.HTTP_400_BAD_REQUEST)

        # التحقق من الحد الأدنى للطلب
        if order_total < float(promo.min_order_amount):
            return Response({
                'error': f'الحد الأدنى لتطبيق هذا الكود هو {promo.min_order_amount} جنيه.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # حساب مبلغ الخصم
        if promo.discount_type == 'percentage':
            discount_amount = round(order_total * float(promo.discount_value) / 100, 2)
        else:
            discount_amount = float(promo.discount_value)
        discount_amount = min(discount_amount, order_total)  # لا يتجاوز الإجمالي

        return Response({
            'valid': True,
            'promo_id': promo.id,
            'code': promo.code,
            'description': promo.description or promo.code,
            'discount_type': promo.discount_type,
            'discount_value': float(promo.discount_value),
            'discount_amount': discount_amount,
        })
