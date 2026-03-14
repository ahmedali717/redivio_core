from django.shortcuts import render
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# استيراد الموديلات والـ Mixins
from apps.core.mixins import OpcoAwareMixin 
from apps.core.models import OpCo
from apps.procurement.models import PurchaseOrder

from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove
from .serializers import (
    PlantSerializer, StorageLocationSerializer, 
    StorageBinSerializer, StockQuantSerializer, StockMoveSerializer
)

# =========================================================
#  1. API Functions (إحصائيات موديول المخازن)
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wms_stats(request):
    """
    جلب إحصائيات سريعة للشركة النشطة لعرضها في لوحة التحكم
    """
    active_opco_id = request.session.get('active_opco_id')
    if not active_opco_id:
        return Response({"plants": 0, "items": 0})
    
    plants_count = Plant.objects.filter(opco_id=active_opco_id).count()
    # حساب عدد السجلات الفريدة في المخزون للشركة النشطة
    items_count = StockQuant.objects.filter(opco_id=active_opco_id).count()
    
    return Response({
        "plants": plants_count,
        "items": items_count
    })

# =========================================================
#  2. Stock Receipt Logic (معالجة استلام المشتريات)
# =========================================================

class StockReceiptAPI(APIView):
    """
    API لاستلام أصناف أمر التوريد وتحديث الأرصدة في الرفوف المختارة
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        po_id = data.get('po_id')
        items = data.get('items', [])
        active_opco_id = request.session.get('active_opco_id')

        if not active_opco_id:
            return Response({"error": "No active company session found"}, status=status.HTTP_400_BAD_REQUEST)

        if not po_id or not items:
            return Response({"error": "Missing PO ID or Items data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                # 1. التأكد من وجود أمر التوريد
                po = PurchaseOrder.objects.get(id=po_id)
                
                for item in items:
                    qty_to_receive = float(item.get('quantity', 0))
                    if qty_to_receive <= 0:
                        continue

                    # 2. جلب الـ Bin لمعرفة الـ Plant المرتبط به (لتفادي خطأ الـ 400)
                    # الموديل يتطلب Plant إجباري في StockQuant
                    target_bin = StorageBin.objects.select_related('storage_location__plant').get(id=item['bin_id'])
                    target_plant = target_bin.storage_location.plant

                    # 3. تحديث الرصيد الحالي (StockQuant)
                    # نستخدم get_or_create لضمان وجود سجل لهذا الصنف في هذا الرف
                    quant, created = StockQuant.objects.get_or_create(
                        opco_id=active_opco_id,
                        plant=target_plant,
                        storage_bin=target_bin,
                        material_id=item['material_id'],
                        defaults={'quantity': 0}
                    )
                    quant.quantity += qty_to_receive
                    quant.save()

                    # 4. تسجيل حركة مخزنية (StockMove) لتوثيق الاستلام
                    # ملاحظة: الموديل يستخدم 'dest_bin' للأصناف الواردة
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=qty_to_receive,
                        move_type='RECEIPT',
                        reference=f"PO Receipt: {po.po_number}",
                        dest_bin=target_bin,
                        vendor_name=getattr(po.vendor, 'name', 'Unknown Vendor'),
                        payment_term=getattr(po, 'extra_data', {}).get('payment_term', 'CASH')
                    )

                # 5. تحديث حالة أمر التوريد إلى "تم الاستلام"
                po.status = 'RECEIVED'
                po.save()

                return Response({
                    "success": True, 
                    "message": f"Successfully received {len(items)} items for PO {po.po_number}"
                }, status=status.HTTP_201_CREATED)

        except StorageBin.DoesNotExist:
            return Response({"error": "One or more selected storage bins do not exist"}, status=400)
        except PurchaseOrder.DoesNotExist:
            return Response({"error": "Purchase Order not found"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_purchase_order_details(request, po_id):
    """
    جلب أصناف أمر التوريد لعرضها في جدول الاستلام بالـ SKU والكميات المطلوبة
    """
    try:
        # استخدام prefetch_related لتحسين الأداء عند جلب البيانات المرتبطة
        po = PurchaseOrder.objects.prefetch_related('lines__material').get(id=po_id)
        
        # تصحيح: العلاقة في موديل المشتريات الخاص بك تسمى 'lines' وليس 'items'
        lines = po.lines.all()
        
        items_data = []
        for line in lines:
            items_data.append({
                'material_id': line.material.id,
                'material_name': line.material.name,
                # جلب الـ SKU أو الكود المتوفر في الماتريال
                'sku': line.material.sku or line.material.code or "N/A",
                'ordered_qty': float(line.quantity),
                'received_qty': float(line.quantity), # اقتراح استلام الكمية كاملة
            })
        
        return JsonResponse({'items': items_data})
    except PurchaseOrder.DoesNotExist:
        return JsonResponse({'error': 'Purchase Order not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# =========================================================
#  3. WMS ViewSets (إدارة بيانات المستودعات)
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
    """عرض الأرصدة الحالية مع بيانات الصنف والموقع"""
    queryset = StockQuant.objects.select_related('material', 'storage_bin', 'plant').all()
    serializer_class = StockQuantSerializer

class StockMoveViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """عرض سجل الحركات المخزنية مرتبة من الأحدث إلى الأقدم"""
    queryset = StockMove.objects.all().order_by('-created_at')
    serializer_class = StockMoveSerializer

class WMSHomeView(View):
    """عرض الصفحة الرئيسية لموديول المخازن (Dashboard)"""
    def get(self, request):
        return render(request, 'wms/dashboard.html')