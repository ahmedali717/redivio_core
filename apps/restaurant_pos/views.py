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
            return self.queryset.filter(opco_id=opco_id)
        return self.queryset

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

    @action(detail=False, methods=['post'])
    def close_session(self, request):
        opco_id = request.data.get('opco')
        actual_balance = float(request.data.get('actual_balance', 0))
        session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
        
        if not session:
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)
            
        session.actual_closing_balance = actual_balance
        session.expected_closing_balance = float(session.opening_balance) + float(session.total_sales) - float(session.total_expenses)
        
        session.is_closed = True
        session.end_time = timezone.now()
        session.save()
        
        return Response({
            'success': True, 
            'session_id': session.id,
            'opening_balance': session.opening_balance,
            'total_sales': session.total_sales,
            'total_expenses': session.total_expenses,
            'expected_balance': session.expected_closing_balance,
            'actual_balance': session.actual_closing_balance,
            'difference': session.actual_closing_balance - session.expected_closing_balance,
            'cashier': session.cashier_name
        })
