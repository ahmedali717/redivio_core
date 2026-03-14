from django.shortcuts import render
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
#  2. Stock Receipt Logic (حل مشكلة الـ 404 لزر التأكيد)
# =========================================================

class StockReceiptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        po_id = data.get('po_id')
        items = data.get('items', [])
        active_opco_id = request.session.get('active_opco_id')

        if not active_opco_id:
            return Response({"error": "No active company found in session"}, status=400)

        try:
            with transaction.atomic():
                # جلب أمر التوريد
                po = PurchaseOrder.objects.get(id=po_id)
                
                for item in items:
                    # 1. تحديث الرصيد الحالي
                    quant, _ = StockQuant.objects.get_or_create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        storage_bin_id=item['bin_id'], # تأكد أن StockQuant لديه storage_bin
                        defaults={'quantity': 0}
                    )
                    quant.quantity += float(item.get('quantity', 0))
                    quant.save()

                    # 2. تسجيل الحركة التاريخية (تعديل الحقل لـ dest_bin)
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=item.get('quantity', 0),
                        move_type='RECEIPT',
                        reference=f"إذن استلام: {po.po_number}",
                        dest_bin_id=item['bin_id'] # ✅ تم التعديل هنا
                    )

                # تحديث حالة أمر التوريد (حسب نظامك)
                po.status = 'RECEIVED'
                po.save()

                return Response({"success": True, "message": "تم تحديث المخزون بنجاح"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# دالة جلب تفاصيل الـ PO لتعبئة الجدول (تمنع الـ 404 عند اختيار PO)
def get_purchase_order_details(request, po_id):
    try:
        po = PurchaseOrder.objects.get(id=po_id)
        # جلب الأصناف المرتبطة (تأكد من الـ related_name في موديل PurchaseOrder)
        # سنحاول الوصول إليها بمرونة
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
#  3. WMS ViewSets (الفلترة التلقائية عبر OpcoAwareMixin)
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