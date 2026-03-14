from django.shortcuts import render
from django.views import View
from django.db import transaction  # <--- ضروري جداً
from django.http import JsonResponse # <--- ضروري جداً
from rest_framework import viewsets, status
from rest_framework.views import APIView # <--- ضروري جداً
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# استيراد الـ Mixin والـ Models
from apps.core.mixins import OpcoAwareMixin 
# تأكد من أن مسار PurchaseOrder صحيح (مهم جداً)
try:
    from apps.procurement.models import PurchaseOrder
except ImportError:
    from apps.item_master.models import PurchaseOrder # مسار احتياطي حسب هيكلة مشروعك

from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove
from .serializers import (
    PlantSerializer, StorageLocationSerializer, 
    StorageBinSerializer, StockQuantSerializer, StockMoveSerializer
)

# =========================================================
#  1. API Functions
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
#  2. Stock Receipt Logic (الجزئية اللي كانت بتضرب 404)
# =========================================================

class StockReceiptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        po_id = data.get('po_id')
        items = data.get('items', [])
        active_opco_id = request.session.get('active_opco_id')

        if not po_id:
            return Response({"error": "Missing PO ID"}, status=400)

        try:
            with transaction.atomic():
                po = PurchaseOrder.objects.get(id=po_id)
                
                for item in items:
                    # تحديث الرصيد في الرف
                    quant, created = StockQuant.objects.get_or_create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        storage_bin_id=item['bin_id'],
                        defaults={'quantity': 0}
                    )
                    quant.quantity += float(item['quantity'])
                    quant.save()

                    # تسجيل الحركة في السجل
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=item['quantity'],
                        move_type='RECEIPT',
                        reference=f"PO Receipt: {po.po_number}",
                        storage_bin_id=item['bin_id']
                    )

                # تحديث حالة الطلب
                po.status = 'RECEIVED'
                po.save()

                return Response({"success": True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_purchase_order_details(request, po_id):
    try:
        po = PurchaseOrder.objects.get(id=po_id)
        # جلب الأصناف المرتبطة بأمر التوريد
        items_data = []
        # ملاحظة: تأكد هل اسم العلاقة items أم po_items
        for item in po.items.all(): 
            items_data.append({
                'material_id': item.material.id,
                'material_name': item.material.name,
                'sku': item.material.sku or item.material.code,
                'ordered_qty': item.quantity,
                'received_qty': item.quantity,
            })
        return JsonResponse({'items': items_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

# =========================================================
#  3. ViewSets
# =========================================================

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
    queryset = StockMove.objects.all().order_by('-date')
    serializer_class = StockMoveSerializer

class WMSHomeView(View):
    def get(self, request):
        return render(request, 'wms/dashboard.html')