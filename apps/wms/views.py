from django.shortcuts import render
from django.views import View
from django.db import transaction
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import Decimal
from django.db.models import Sum, F

# استيراد الـ Mixin والـ Models والـ Serializers
from apps.core.mixins import OpcoAwareMixin 
from apps.core.models import OpCo
# جلب الموديل هنا بشكل عام أو جوا الدوال
from django.apps import apps
from apps.procurement.models import PurchaseOrder

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
    active_opco_id = request.query_params.get('opco') or request.session.get('active_opco_id')
    
    if not active_opco_id:
        return Response({
            "plants": 0, "items": 0, "total_value": 0, "low_stock": 0
        })
    
    quants = StockQuant.objects.filter(opco_id=active_opco_id)
    plants_count = StorageLocation.objects.filter(plant__opco_id=active_opco_id).count()
    items_count = quants.values('material_id').distinct().count()
    
    total_value = 0
    try:
        agg = quants.annotate(
            val=F('quantity') * F('material__standard_price')
        ).aggregate(total=Sum('val'))
        total_value = agg['total'] if agg['total'] is not None else 0
    except Exception as e:
        total_value = 0
        
    low_stock = quants.filter(quantity__lte=0).count()
    
    return Response({
        "plants": plants_count,
        "items": items_count,
        "total_value": round(float(total_value), 2),
        "low_stock": low_stock
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
                StockReceipt = apps.get_model('procurement', 'StockReceipt')
                StockReceiptLine = apps.get_model('procurement', 'StockReceiptLine')
                
                # إنشاء إذن استلام
                receipt = StockReceipt.objects.create(
                    opco_id=active_opco_id,
                    po=po,
                    created_by=request.user if request.user.is_authenticated else None
                )
                
                for item in items:
                    target_bin = StorageBin.objects.select_related('storage_location__plant').get(id=item['bin_id'])
                    target_plant = target_bin.storage_location.plant

                    qty_val = item.get('quantity', 0)
                    qty_decimal = Decimal(str(qty_val))

                    # لا نقوم بإنشاء/تحديث StockQuant يدوياً لأن StockMove.save يقوم بذلك تلقائياً
                    # لضمان عدم التكرار

                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=qty_decimal,
                        move_type='RECEIPT',  # أو IN
                        reference=f"PO Receipt: {po.po_number}",
                        dest_bin=target_bin,
                        vendor_name=getattr(po.vendor, 'name', '') 
                    )
                    
                    StockReceiptLine.objects.create(
                        receipt=receipt,
                        material_id=item['material_id'],
                        quantity=qty_decimal,
                        storage_bin=target_bin
                    )
                    
                    # تحديث الكمية المستلمة في تفاصيل أمر التوريد
                    po_line = po.lines.filter(material_id=item['material_id']).first()
                    if po_line:
                        po_line.received_quantity += qty_decimal
                        po_line.save()

                po.status = 'RECEIVED'
                po.save()

                return Response({
                    "success": True, 
                    "receipt_id": receipt.id, 
                    "receipt_number": receipt.receipt_number
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StockDeliveryAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        so_id = data.get('so_id')
        items = data.get('items', [])
        active_opco_id = request.session.get('active_opco_id')

        if not active_opco_id:
            return Response({"error": "No active company"}, status=400)

        try:
            with transaction.atomic():
                SalesOrder = apps.get_model('sales', 'SalesOrder')
                StockDelivery = apps.get_model('sales', 'StockDelivery')
                StockDeliveryLine = apps.get_model('sales', 'StockDeliveryLine')
                
                so = SalesOrder.objects.get(id=so_id)
                
                # إنشاء إذن صرف
                delivery = StockDelivery.objects.create(
                    opco_id=active_opco_id,
                    so=so,
                    created_by=request.user if request.user.is_authenticated else None
                )
                
                for item in items:
                    source_bin = StorageBin.objects.select_related('storage_location__plant').get(id=item['bin_id'])
                    
                    qty_val = item.get('quantity', 0)
                    qty_decimal = Decimal(str(qty_val))
                    
                    if qty_decimal <= 0:
                        continue
                        
                    # التحقق من وجود رصيد كافٍ
                    quant = StockQuant.objects.filter(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        storage_bin=source_bin
                    ).first()
                    
                    if not quant or quant.quantity < qty_decimal:
                        raise ValueError(f"Insufficient stock for {item['material_name']} in bin {source_bin.code}")

                    # تسجيل الحركة (والتي ستقوم بخصم الكمية تلقائياً من StockQuant)
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=qty_decimal,
                        move_type='OUT', 
                        reference=f"SO Delivery: {so.so_number}",
                        source_bin=source_bin
                    )
                    
                    StockDeliveryLine.objects.create(
                        delivery=delivery,
                        material_id=item['material_id'],
                        quantity=qty_decimal,
                        storage_bin=source_bin
                    )
                    
                    # تحديث الكمية المصروفة في أمر البيع
                    so_line = so.lines.filter(material_id=item['material_id']).first()
                    if so_line:
                        so_line.delivered_quantity += qty_decimal
                        so_line.save()

                so.status = 'DELIVERED'
                so.save()

                return Response({
                    "success": True, 
                    "delivery_id": delivery.id, 
                    "delivery_number": delivery.delivery_number
                }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

def get_sales_order_details(request, so_id):
    try:
        SalesOrder = apps.get_model('sales', 'SalesOrder')
        so = SalesOrder.objects.get(id=so_id)
        
        items_data = []
        for line in so.lines.all():
            items_data.append({
                'material_id': line.material.id,
                'material_name': line.material.name,
                'sku': getattr(line.material, 'sku', line.material.code),
                'ordered_qty': float(line.quantity),
                'received_qty': float(getattr(line, 'delivered_quantity', 0)),
            })
        
        return JsonResponse({'items': items_data})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)


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
                'ordered_qty': float(item.quantity),
                'received_qty': float(item.quantity),
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
    queryset = StockMove.objects.none() # سطر أمان عشان الـ Router
    serializer_class = StockMoveSerializer

    def get_queryset(self):
        qs = StockMove.objects.all().select_related('material', 'dest_bin', 'source_bin').order_by('-date')
        
        m_id = self.request.query_params.get('material_id')
        d_from = self.request.query_params.get('date_from')
        d_to = self.request.query_params.get('date_to')

        if m_id:
            qs = qs.filter(material_id=m_id)
        if d_from:
            qs = qs.filter(date__date__gte=d_from)
        if d_to:
            qs = qs.filter(date__date__lte=d_to)
            
        return qs

class WMSHomeView(View):
    def get(self, request):
        return render(request, 'wms/dashboard.html')