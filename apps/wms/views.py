from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
from django.db import transaction, models
from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from decimal import Decimal
from django.db.models import Sum, F
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps

# Mixin & Models
from apps.core.mixins import OpcoAwareMixin 
from apps.core.models import OpCo
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
            "plants": 0, "items": 0, "total_value": 0, "low_stock": 0,
            "capacity": 0, "pending_operations": []
        })
    
    # 1. الإحصائيات الأساسية
    quants = StockQuant.objects.filter(opco_id=active_opco_id)
    plants_count = Plant.objects.filter(opco_id=active_opco_id).count()
    items_count = quants.values('material_id').distinct().count()
    
    # 2. حساب القيمة الإجمالية
    total_value = 0
    try:
        agg = quants.annotate(
            val=F('quantity') * F('material__standard_price')
        ).aggregate(total=Sum('val'))
        total_value = agg['total'] if agg['total'] is not None else 0
    except Exception: total_value = 0
        
    # 3. حساب نسبة الإشغال (Capacity)
    total_bins = StorageBin.objects.filter(storage_location__plant__opco_id=active_opco_id).count()
    occupied_bins = quants.filter(quantity__gt=0).values('storage_bin').distinct().count()
    capacity_pct = int((occupied_bins / total_bins * 100)) if total_bins > 0 else 0

    # 4. طابور العمليات (Operations Queue)
    # جلب أوامر الشراء المؤكدة (لم تستلم بالكامل بعد)
    PurchaseOrder = apps.get_model('procurement', 'PurchaseOrder')
    pending_pos = PurchaseOrder.objects.filter(opco_id=active_opco_id, status='CONFIRMED').order_by('-created_at')[:5]
    
    # جلب أوامر البيع المؤكدة (لم تشحن بالكامل بعد)
    SalesOrder = apps.get_model('sales', 'SalesOrder')
    pending_sos = SalesOrder.objects.filter(opco_id=active_opco_id, status='CONFIRMED').order_by('-created_at')[:5]
    
    lang = getattr(request, 'LANGUAGE_CODE', 'en')
    operations = [] # ✅ تهيئة القائمة
    for po in pending_pos:
        operations.append({
            "id": po.id,
            "ref": po.po_number,
            "type": "IN",
            "type_label": "استلام مشتريات" if lang == 'ar' else "PO Receipt",
            "owner": po.vendor.name,
            "status": "Pending"
        })
    for so in pending_sos:
        operations.append({
            "id": so.id,
            "ref": so.so_number,
            "type": "OUT",
            "type_label": "صرف مبيعات" if lang == 'ar' else "SO Delivery",
            "owner": so.customer.name,
            "status": "Pending"
        })

    return Response({
        "plants": plants_count,
        "items": items_count,
        "total_value": float(total_value),
        "low_stock": quants.filter(quantity__lte=5).count(),
        "capacity": capacity_pct,
        "total_bins": total_bins,
        "occupied_bins": occupied_bins,
        "pending_operations": sorted(operations, key=lambda x: x['ref'], reverse=True)
    })

# =========================================================
#  2. ViewSets
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
    queryset = StockQuant.objects.all()
    serializer_class = StockQuantSerializer

    @action(detail=False, methods=['get'])
    def print_audit(self, request):
        """ توليد تقرير جرد للأصناف الحالية """
        from django.utils import timezone
        active_opco = self.get_active_opco()
        quants = StockQuant.objects.filter(opco=active_opco).select_related('material', 'storage_bin')
        
        data = [{
            "material": q.material.name,
            "sku": getattr(q.material, 'sku', q.material.code),
            "bin": q.storage_bin.code,
            "quantity": float(q.quantity)
        } for q in quants]
        
        return Response({
            "report_date": timezone.now(),
            "opco_name": active_opco.name,
            "items": data
        })

class StockMoveViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StockMove.objects.all().order_by('-id')
    serializer_class = StockMoveSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # دعم الفلترة المرسلة من الواجهة الأمامية
        material_id = self.request.query_params.get('material_id')
        if material_id:
            queryset = queryset.filter(material_id=material_id)
            
        location_id = self.request.query_params.get('location_id')
        if location_id and location_id.strip():
            # إذا تم تحديد موقع، نفلتر الحركات الصادرة (source) أو الواردة (dest) المرتبطة بهذا الموقع
            queryset = queryset.filter(
                models.Q(source_bin__storage_location_id=location_id) | 
                models.Q(dest_bin__storage_location_id=location_id)
            )
            
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
            
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
            
        return queryset

    @action(detail=False, methods=['get'])
    def last_price(self, request):
        """ جلب آخر سعر (شراء أو بيع) للصنف بناءً على نوع الحركة والشركة والطرف الثاني """
        material_id = request.query_params.get('material_id')
        move_type = request.query_params.get('move_type', 'IN')
        opco_id = self._get_opco_id()
        
        if not material_id:
            return Response({"price": 0})
            
        last_move = StockMove.objects.filter(
            opco_id=opco_id,
            material_id=material_id,
            move_type=move_type
        ).order_by('-created_at').first()
        
        if last_move:
            price = last_move.unit_cost if move_type == 'IN' else last_move.sales_price
            return Response({"price": float(price)})
            
        return Response({"price": 0})

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        
        # Mapping from SaaS Frontend payload to Backend expected variables
        receipt_type = data.get('receipt_type')
        move_type = data.get('move_type') or ('IN' if receipt_type == 'PURCHASE' else 'OUT' if receipt_type == 'ISSUE' else 'TRANSFER')
        items = data.get('items', [])
        
        po_id = data.get('po_id')
        so_id = data.get('so_id')
        opco_id = self._get_opco_id()
        
        contact_id = data.get('contact_id')
        manual_contact_name = data.get('manual_contact_name')

        if not items:
            return Response({"error": "No items provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 🚀 0. Auto-Create Contact for Standalone Users
        reference_text = "Manual Move"
        if move_type == 'IN' and manual_contact_name:
            try:
                Vendor = apps.get_model('procurement', 'Vendor')
                vendor, _ = Vendor.objects.get_or_create(
                    opco_id=opco_id, 
                    name=manual_contact_name,
                    defaults={'code': f'V-MANUAL-{opco_id}'}
                )
                reference_text = f"Receipt from {vendor.name}"
            except Exception:
                reference_text = f"Receipt from {manual_contact_name}"
        elif move_type == 'IN' and contact_id:
            reference_text = f"Receipt from Vendor #{contact_id}"
            
        if move_type == 'OUT' and manual_contact_name:
            try:
                Customer = apps.get_model('sales', 'Customer')
                customer, _ = Customer.objects.get_or_create(
                    opco_id=opco_id, 
                    name=manual_contact_name,
                    defaults={'code': f'C-MANUAL-{opco_id}'}
                )
                reference_text = f"Issue to {customer.name}"
            except Exception:
                reference_text = f"Issue to {manual_contact_name}"
        elif move_type == 'OUT' and contact_id:
            reference_text = f"Issue to Customer #{contact_id}"

        # 🚀 1. Process Material Inbound (Receipt)
        if move_type == 'IN':
            for item in items:
                qty = Decimal(str(item.get('received_qty', item.get('quantity', 0))))
                unit_cost = Decimal(str(item.get('unit_cost', 0)))
                pay_method = data.get('payment_method', 'CASH')
                
                if qty <= 0: continue
                
                material_id = item.get('material_id') or item.get('material')
                
                # Auto-resolve Bin if missing
                bin_id = item.get('bin_id')
                dest_bin = None
                if bin_id:
                    dest_bin = StorageBin.objects.get(id=bin_id)
                else:
                    dest_bin = StorageBin.objects.filter(storage_location__plant__opco_id=opco_id).first()
                
                if not dest_bin:
                    return Response({"error": "No storage bin configured"}, status=400)
                
                # --- 📈 WAC Calculation (Weighted Average Cost) ---
                try:
                    Material = apps.get_model('item_master', 'Material')
                    mat_obj = Material.objects.get(id=material_id)
                    
                    qty_before = Decimal(str(mat_obj.total_on_hand))
                    cost_before = mat_obj.standard_price
                    
                    total_val_before = qty_before * cost_before
                    total_val_new = qty * unit_cost
                    total_qty_after = qty_before + qty
                    
                    if total_qty_after > 0:
                        new_wac = (total_val_before + total_val_new) / total_qty_after
                        mat_obj.standard_price = new_wac.quantize(Decimal('0.01'))
                        mat_obj.save()
                except Exception as e:
                    print(f"WAC Update Error: {e}")

                # Create StockMove
                move = StockMove.objects.create(
                    opco_id=opco_id,
                    material_id=material_id,
                    quantity=qty,
                    unit_cost=unit_cost,
                    payment_method=pay_method,
                    move_type='IN',
                    dest_bin=dest_bin,
                    reference=f"PO {po_id}" if po_id else reference_text,
                    vendor_name=manual_contact_name
                )
                
                # Update StockQuant
                quant, created = StockQuant.objects.get_or_create(
                    opco_id=opco_id,
                    material_id=material_id,
                    storage_bin=dest_bin,
                    defaults={'plant': dest_bin.storage_location.plant}
                )
                quant.quantity += qty
                quant.save()

        # 🚚 2. Process Material Outbound (Delivery)
        elif move_type == 'OUT':
            for item in items:
                qty = Decimal(str(item.get('received_qty', item.get('quantity', 0))))
                sales_price = Decimal(str(item.get('sales_price', 0)))
                coll_method = data.get('payment_method', 'CASH')

                if qty <= 0: continue

                material_id = item.get('material_id') or item.get('material')
                
                # Auto-resolve Bin if missing
                bin_id = item.get('bin_id')
                source_bin = None
                if bin_id:
                    source_bin = StorageBin.objects.get(id=bin_id)
                else:
                    best_quant = StockQuant.objects.filter(
                        opco_id=opco_id, material_id=material_id, quantity__gte=qty
                    ).order_by('-quantity').first()
                    if best_quant:
                        source_bin = best_quant.storage_bin
                    else:
                        source_bin = StorageBin.objects.filter(storage_location__plant__opco_id=opco_id).first()

                if not source_bin:
                    return Response({"error": "No storage bin configured"}, status=400)

                # Check Availability
                quant = StockQuant.objects.filter(
                    opco_id=opco_id, material_id=material_id, storage_bin=source_bin
                ).first()
                
                if not quant or quant.quantity < qty:
                    return Response({"error": f"Insufficient stock for Material ID {material_id}"}, status=400)

                # Create StockMove
                move = StockMove.objects.create(
                    opco_id=opco_id,
                    material_id=material_id,
                    quantity=qty,
                    sales_price=sales_price,
                    payment_method=coll_method,
                    move_type='OUT',
                    source_bin=source_bin,
                    reference=f"SO {so_id}" if so_id else reference_text,
                    vendor_name=manual_contact_name
                )

                # Update StockQuant
                quant.quantity -= qty
                quant.save()

        return Response({"status": "success"}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_sales_order_details(request, so_id):
    """ جلب تفاصيل أمر البيع مع الكميات المنصرفة سابقاً بشكل آمن """
    if not so_id or so_id == 'null' or so_id == 'undefined':
        return Response({'items': []})
        
    try:
        SalesOrder = apps.get_model('sales', 'SalesOrder')
        so = SalesOrder.objects.get(id=int(so_id))
        lines = so.lines.select_related('material').all()
        
        items_data = []
        for line in lines:
            if not line.material: continue
            items_data.append({
                'material_id': line.material.id,
                'material_name': line.material.name,
                'sku': getattr(line.material, 'sku', line.material.code if hasattr(line.material, 'code') else f"MAT-{line.material.id}"),
                'ordered_qty': float(line.quantity),
                'received_before': float(getattr(line, 'shipped_quantity', 0) or 0),
                'received_qty': 0,
            })
            
        return Response({
            'so_id': so.id,
            'so_number': so.so_number,
            'customer_name': so.customer.name,
            'items': items_data
        })
    except (ObjectDoesNotExist, ValueError):
        return Response({'error': 'Sales Order not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_purchase_order_details(request, po_id):
    """ جلب تفاصيل أمر التوريد مع الكميات المستلمة سابقاً """
    if not po_id or po_id == 'null' or po_id == 'undefined':
        return Response({'items': []})
        
    try:
        PurchaseOrder = apps.get_model('procurement', 'PurchaseOrder')
        po = PurchaseOrder.objects.get(id=int(po_id))
        lines = po.lines.select_related('material').all()
        
        items_data = []
        for line in lines:
            if not line.material: continue
            items_data.append({
                'material_id': line.material.id,
                'material_name': line.material.name,
                'sku': getattr(line.material, 'sku', line.material.code if hasattr(line.material, 'code') else f"MAT-{line.material.id}"),
                'ordered_qty': float(line.quantity),
                'received_before': float(getattr(line, 'received_qty', 0) or 0),
                'received_qty': 0,
            })
            
        return Response({
            'po_id': po.id,
            'po_number': po.po_number,
            'vendor_name': po.vendor.name,
            'items': items_data
        })
    except (ObjectDoesNotExist, ValueError):
        return Response({'error': 'Purchase Order not found'}, status=404)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

class StockReceiptViewSet(viewsets.ModelViewSet):
    """ هذا الـ ViewSet قديم وسيتم استبداله مستقبلاً بـ StockMoveViewSet لكنه ضروري للتوافق حالياً """
    queryset = StockMove.objects.all()
    serializer_class = StockMoveSerializer

    def create(self, request, *args, **kwargs):
        # توجيه الطلب لـ StockMoveViewSet.create
        move_view = StockMoveViewSet()
        move_view.request = request
        move_view.format_kwarg = None
        return move_view.create(request, *args, **kwargs)

class WMSHomeView(TemplateView):
    template_name = 'wms/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # يمكنك إضافة بيانات إضافية هنا للـ Dashboard
        return context

class StockReceiptAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response({"status": "deprecated, use StockMoveViewSet"}, status=200)

class StockDeliveryAPI(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response({"status": "deprecated, use StockMoveViewSet"}, status=200)