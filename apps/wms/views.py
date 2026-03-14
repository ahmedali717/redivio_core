from django.shortcuts import render
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import traceback  # 👈 أضفنا المكتبة دي عشان تصطاد العطل بالظبط

# استيراد الـ Mixin والـ Models والـ Serializers
from apps.core.mixins import OpcoAwareMixin 
from apps.core.models import OpCo
from apps.procurement.models import PurchaseOrder

# تأكد أن هذه الموديلات موجودة في نفس تطبيق الـ WMS
from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove
from .serializers import (
    PlantSerializer, StorageLocationSerializer, 
    StorageBinSerializer, StockQuantSerializer, StockMoveSerializer
)

# =========================================================
#  1. API Functions (إحصائيات الموديول)
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
#  2. Stock Receipt Logic
# =========================================================

class StockReceiptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
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
                    # 1. التأكد من وجود الـ Bin
                    bin_id = item.get('bin_id')
                    if not bin_id:
                        raise ValueError(f"الرف غير محدد للصنف {item.get('material_id')}")

                    target_bin = StorageBin.objects.select_related('storage_location__plant').get(id=bin_id)
                    target_plant = target_bin.storage_location.plant

                    # 2. تحديث الرصيد (StockQuant)
                    quant, created = StockQuant.objects.get_or_create(
                        opco_id=active_opco_id,
                        plant=target_plant, 
                        material_id=item['material_id'],
                        storage_bin=target_bin,
                        defaults={'quantity': 0}
                    )
                    quant.quantity += float(item.get('quantity', 0))
                    quant.save()

                    # 3. تسجيل الحركة التاريخية (StockMove)
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=float(item.get('quantity', 0)),
                        move_type='RECEIPT', # ⚠️ لو الـ DB رافضة الكلمة دي، الخطأ هيظهرلنا
                        reference=f"PO Receipt: {po.po_number}",
                        dest_bin=target_bin,
                        # أوقفنا حقل المورد مؤقتاً لاحتمال عدم وجوده في قاعدة البيانات
                        # vendor_name=getattr(po.vendor, 'name', '') 
                    )

                po.status = 'RECEIVED'
                po.save()

                return Response({"success": True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            # 🚀 هنا السحر: هنرجع تفاصيل المشكلة (Traceback) كاملة للفرونت إند!
            error_details = traceback.format_exc()
            return Response({
                "error": str(e),
                "trace": error_details
            }, status=status.HTTP_400_BAD_REQUEST)

# دالة جلب تفاصيل الـ PO
def get_purchase_order_details(request, po_id):
    try:
        po = PurchaseOrder.objects.get(id=po_id)
        items_source = getattr(po, 'items', None) or po.purchaseorderitem_set
        
        items_data = []
        for item in items_source.all():
            items_data.append({
                'material_id': item.material.id,
                'material_name': item.material.name,
                'sku': getattr(item.material, 'sku', item.material.code),
                'ordered_qty': item.quantity,
                'received_qty': item.quantity,
            })
        
        return JsonResponse({'items': items_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

# =========================================================
#  3. WMS ViewSets 
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