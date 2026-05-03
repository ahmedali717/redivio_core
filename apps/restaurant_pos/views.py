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
        
        # Close previous sessions for this OpCo just in case
        POSSession.objects.filter(opco_id=opco_id, is_closed=False).update(is_closed=True, end_time=timezone.now())
        
        session = POSSession.objects.create(
            opco_id=opco_id,
            cashier_name=cashier_name,
            is_closed=False
        )
        from .serializers import POSSessionSerializer
        return Response(POSSessionSerializer(session).data)

    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        order = self.get_object()
        if order.status != 'draft':
            return Response({'error': 'Order already processed'}, status=status.HTTP_400_BAD_REQUEST)
        
        # تحديث الحالة والدفع
        order.status = 'paid'
        order.save()
        
        # 🚀 تشغيل محرك خصم المخزون (تلقائياً من الوصفة)
        try:
            order.deduct_inventory()
            return Response({'success': True, 'order_ref': order.order_ref})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def close_session(self, request):
        opco_id = request.data.get('opco')
        session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
        
        if not session:
            return Response({'error': 'No active session found'}, status=status.HTTP_400_BAD_REQUEST)
            
        # حساب الإيرادات (تسميع الإيراد)
        from django.db.models import Sum
        total_revenue = POSOrder.objects.filter(session=session, status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        session.is_closed = True
        session.end_time = timezone.now()
        session.save()
        
        return Response({
            'success': True, 
            'session_id': session.id,
            'total_revenue': total_revenue,
            'cashier': session.cashier_name
        })
