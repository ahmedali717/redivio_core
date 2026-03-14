from django.shortcuts import render
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.mixins import OpcoAwareMixin 
from apps.core.models import OpCo
from apps.procurement.models import PurchaseOrder

from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove
from .serializers import (
    PlantSerializer, StorageLocationSerializer, 
    StorageBinSerializer, StockQuantSerializer, StockMoveSerializer
)

class StockReceiptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        po_id = data.get('po_id')
        items = data.get('items', [])
        active_opco_id = request.session.get('active_opco_id')

        if not active_opco_id:
            return Response({"error": "لا توجد شركة نشطة"}, status=400)

        try:
            with transaction.atomic():
                po = PurchaseOrder.objects.get(id=po_id)
                
                for item in items:
                    # ✅ بناءً على موديل StockMove عندك، الدالة save() بتحدث الرصيد تلقائياً
                    # إحنا بس محتاجين نسجل الحركة صح
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=float(item.get('quantity', 0)),
                        move_type='RECEIPT',
                        reference=f"PO Receipt: {po.po_number}",
                        dest_bin_id=item['bin_id'], # ✅ تم التصحيح ليتوافق مع الموديل
                        vendor_name=getattr(po.vendor, 'name', '')
                    )

                # تحديث حالة أمر التوريد
                po.status = 'RECEIVED'
                po.save()

                return Response({"success": True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            # إرجاع الخطأ الفعلي للمساعدة في التشخيص
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_purchase_order_details(request, po_id):
    try:
        po = PurchaseOrder.objects.get(id=po_id)
        # ✅ التصحيح: العلاقة في الموديل اسمها 'lines' وليس 'items'
        items_data = [{
            'material_id': line.material.id,
            'material_name': line.material.name,
            'sku': getattr(line.material, 'sku', line.material.code),
            'ordered_qty': line.quantity,
            'received_qty': line.quantity,
        } for line in po.lines.all()]
        
        return JsonResponse({'items': items_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)

# باقي الـ ViewSets (Plant, Location, etc.) تظل كما هي في ملفك الأصلي
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