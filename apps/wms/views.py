from django.shortcuts import render
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# استيراد الموديلات الأساسية في التطبيق نفسه
from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove
from .serializers import (
    PlantSerializer, StorageLocationSerializer, 
    StorageBinSerializer, StockQuantSerializer, StockMoveSerializer
)

# =========================================================
#  1. إحصائيات المخزن
# =========================================================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wms_stats(request):
    active_opco_id = request.session.get('active_opco_id')
    if not active_opco_id:
        return Response({"plants": 0, "items": 0})
    
    plants_count = Plant.objects.filter(opco_id=active_opco_id).count()
    items_count = StockQuant.objects.filter(opco_id=active_opco_id).count()
    
    return Response({
        "plants": plants_count,
        "items": items_count
    })

# =========================================================
#  2. تنفيذ استلام المشتريات
# =========================================================
class StockReceiptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # استيراد داخلي لمنع الـ Circular Import أو وقوع السيرفر
        try:
            from apps.procurement.models import PurchaseOrder
        except ImportError:
            from procurement.models import PurchaseOrder

        data = request.data
        po_id = data.get('po_id')
        items = data.get('items', [])
        active_opco_id = request.session.get('active_opco_id')

        if not active_opco_id:
            return Response({"error": "No active company"}, status=400)

        try:
            with transaction.atomic():
                po = PurchaseOrder.objects.get(id=po_id)
                
                for item in items:
                    target_bin = StorageBin.objects.get(id=item['bin_id'])

                    # ✅ بنسجل الحركة فقط، والموديل (ملف 27) هيحدث الرصيد تلقائياً في الـ save
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=float(item.get('quantity', 0)),
                        move_type='RECEIPT',
                        reference=f"PO Receipt: {po.po_number}",
                        dest_bin=target_bin,
                        vendor_name=getattr(po.vendor, 'name', '')
                    )

                po.status = 'RECEIVED'
                po.save()

                return Response({"success": True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# =========================================================
#  3. جلب تفاصيل الـ PO (المتوافق مع Related Name 'lines')
# =========================================================
def get_purchase_order_details(request, po_id):
    try:
        try:
            from apps.procurement.models import PurchaseOrder
        except ImportError:
            from procurement.models import PurchaseOrder

        po = PurchaseOrder.objects.get(id=po_id)
        
        # ✅ بنستخدم lines لأنك معرفها كدة في موديل الـ PurchaseOrderLine
        items_data = []
        for line in po.lines.all():
            items_data.append({
                'material_id': line.material.id,
                'material_name': line.material.name,
                'sku': getattr(line.material, 'sku', line.material.code),
                'ordered_qty': line.quantity,
                'received_qty': line.quantity,
            })
        
        return JsonResponse({'items': items_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

# =========================================================
#  4. الـ ViewSets (مع تصحيح حقل الترتيب)
# =========================================================
from apps.core.mixins import OpcoAwareMixin 

class PlantViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer

class StorageLocationViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer

class StorageBinViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StorageBin.objects.all()
    serializer_class = StorageBinSerializer

class StockQuantViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StockQuant.objects.select_related('material', 'storage_bin', 'plant').all()
    serializer_class = StockQuantSerializer

class StockMoveViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    # ✅ تم التغيير من date (غير موجود) إلى created_at (موجود)
    queryset = StockMove.objects.all().order_by('-created_at')
    serializer_class = StockMoveSerializer

class WMSHomeView(View):
    def get(self, request):
        return render(request, 'wms/dashboard.html')