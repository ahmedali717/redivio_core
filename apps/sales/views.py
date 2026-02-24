from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

# Models & Serializers
from .models import Customer, SalesOrder, SalesOrderLine
from .serializers import CustomerSerializer, SalesOrderSerializer, SalesOrderLineSerializer

# ✅ التصحيح: استيراد StorageBin باستخدام apps.wms
from apps.wms.models import StorageBin

# =========================================================
#  1. Helper Mixin
# =========================================================
class OpcoAwareMixin:
    """
    يقوم تلقائياً بربط السجل بالشركة (OpCo) بناءً على الجلسة الحالية
    """
    def perform_create(self, serializer):
        opco_id = self.request.data.get('opco')
        active_opco_id = self.request.session.get('active_opco_id')
        
        if opco_id:
            serializer.save(opco_id=opco_id)
        elif active_opco_id:
            serializer.save(opco_id=active_opco_id)
        else:
            serializer.save()

# =========================================================
#  2. Sales ViewSets
# =========================================================

class CustomerViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة العملاء """
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class SalesOrderViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة أوامر البيع (SO) """
    queryset = SalesOrder.objects.all().order_by('-created_at')
    serializer_class = SalesOrderSerializer

    # --- Custom Action: Deliver Items (Delivery Note) ---
    # يقوم بتحويل الحالة إلى DELIVERED وخصم المخزون
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        so = self.get_object()
        
        # 1. تحديد الرف الذي سيتم الصرف منه (Source Bin)
        bin_id = request.data.get('bin_id')
        if not bin_id:
            return Response({'error': 'Source Bin ID is required for delivery.'}, status=400)
        
        try:
            source_bin = StorageBin.objects.get(id=bin_id)
            
            # 2. استدعاء دالة الصرف من الموديل
            if hasattr(so, 'deliver_items'):
                so.deliver_items(source_bin)
            else:
                # Fallback logic
                so.status = 'DELIVERED'
                so.save()
            
            return Response({'status': 'Delivered', 'so_number': so.so_number})
            
        except StorageBin.DoesNotExist:
            return Response({'error': 'Invalid Source Bin ID'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class SalesOrderLineViewSet(viewsets.ModelViewSet):
    queryset = SalesOrderLine.objects.all()
    serializer_class = SalesOrderLineSerializer