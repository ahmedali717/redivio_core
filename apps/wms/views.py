from django.shortcuts import render
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import Decimal  # 👈 1. إضافة مكتبة حل الأرقام
from django.db.models import Sum, F

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
        return Response({
            "plants": 0, "items": 0, "total_value": 0, "low_stock": 0
        })
    
    quants = StockQuant.objects.filter(opco_id=active_opco_id)
    
    # 🚀 التصحيح 1: حساب المنشآت (أو المخازن)
    # هنجيب عدد الـ Locations لأنها تمثل المخازن الفعلية
    plants_count = StorageLocation.objects.filter(opco_id=active_opco_id).count()
    
    # لو إنت عايز تعدد الـ Plant مش الـ Location، استخدم دي بدل اللي فوق:
    # plants_count = Plant.objects.filter(opco_id=active_opco_id).count()
    
    # 🚀 التصحيح 2: عدد الأصناف الفريدة (مش إجمالي القطع)
    items_count = quants.values('material_id').distinct().count()
    
    # 🚀 التصحيح 3: حساب الفلوس بأمان
    # لازم نتأكد إن material__standard_price موجود ومبيعملش error لو القيمة Null
    total_value = quants.annotate(
        val=F('quantity') * F('material__standard_price')
    ).aggregate(total=Sum('val'))['total']
    
    # لو النتيجة طلعت None، خليها 0
    if total_value is None:
        total_value = 0
        
    low_stock = quants.filter(quantity__lte=0).count()
    
    return Response({
        "plants": plants_count,
        "items": items_count,
        "total_value": round(total_value, 2), # تقريب لرقمين عشريين
        "low_stock": low_stock
    }),

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
            return Response({"error": "No active company"}, status=400)

        try:
            with transaction.atomic():
                # 1. جلب أمر التوريد
                from apps.procurement.models import PurchaseOrder
                po = PurchaseOrder.objects.get(id=po_id)
                
                for item in items:
                    # 🚀 التعديل الجوهري: جلب الـ Bin أولاً لمعرفة الـ Plant المرتبط به
                    target_bin = StorageBin.objects.select_related('storage_location__plant').get(id=item['bin_id'])
                    target_plant = target_bin.storage_location.plant

                    # 👈 2. تحويل الكمية بشكل آمن لتجنب خطأ الـ TypeError
                    qty_val = item.get('quantity', 0)
                    try:
                        qty_decimal = Decimal(str(qty_val))
                    except:
                        qty_decimal = Decimal('0')

                    # 2. تحديث الرصيد الحالي (StockQuant) - أضفنا الـ plant_id هنا
                    quant, created = StockQuant.objects.get_or_create(
                        opco_id=active_opco_id,
                        plant=target_plant, 
                        material_id=item['material_id'],
                        storage_bin=target_bin,
                        defaults={'quantity': Decimal('0.00')} # 👈 تم إضافة Decimal هنا
                    )
                    quant.quantity += qty_decimal # 👈 الجمع الآمن
                    quant.save()

                    # 3. تسجيل الحركة التاريخية (StockMove)
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=qty_decimal, # 👈 التمرير الآمن كـ Decimal
                        move_type='RECEIPT',
                        reference=f"PO Receipt: {po.po_number}",
                        dest_bin=target_bin,
                        vendor_name=getattr(po.vendor, 'name', '') 
                    )

                # 4. تحديث حالة الـ PO
                po.status = 'RECEIVED'
                po.save()

                return Response({"success": True}, status=status.HTTP_201_CREATED)
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