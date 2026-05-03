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
        if opco_id:
            return self.queryset.filter(opco_id=opco_id)
        return self.queryset

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
