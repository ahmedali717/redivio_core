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

def parse_csv_file(file):
    import csv
    content = file.read()
    try:
        decoded_content = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            decoded_content = content.decode('windows-1256')
        except UnicodeDecodeError:
            decoded_content = content.decode('utf-8', errors='ignore')
            
    lines = decoded_content.splitlines()
    reader = csv.DictReader(lines)
    fieldnames = [f.strip() for f in (reader.fieldnames or [])]
    rows = []
    for row in reader:
        cleaned_row = {}
        for k, v in row.items():
            if k is not None:
                cleaned_row[k.strip()] = v.strip() if v else ''
        rows.append(cleaned_row)
    return fieldnames, rows

# =========================================================
#  1. API Functions
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wms_stats(request):
    def _get_opco_id():
        # 1. Check Query Params
        # 2. Check Request Data (JSON/FormData)
        # 3. Check Session
        return (request.query_params.get('opco') or 
                request.data.get('opco') or 
                request.session.get('active_opco_id'))

    active_opco_id = _get_opco_id()
    
    if not active_opco_id:
        return Response({
            "plants": 0, "items": 0, "total_value": 0, "low_stock": 0,
            "capacity": 0, "pending_operations": []
        })
    
    # 1. الإحصائيات الأساسية
    Material = apps.get_model('item_master', 'Material')
    quants = StockQuant.objects.filter(opco_id=active_opco_id)
    plants_count = Plant.objects.filter(opco_id=active_opco_id).count()
    items_count = quants.values('material_id').distinct().count()

    # 2. حساب الأصناف الحرجة (Low Stock based on reorder_level)
    from django.db.models import Sum, F
    from django.db.models.functions import Coalesce
    
    low_stock_qs = Material.objects.filter(
        opco_id=active_opco_id,
        reorder_level__gt=0
    ).annotate(
        current_qty=Coalesce(Sum('stockquant__quantity'), Decimal('0'))
    ).filter(
        current_qty__lte=F('reorder_level')
    )
    
    low_stock_count = low_stock_qs.count()
    low_stock_list = []
    for m in low_stock_qs[:5]: # نأخذ أول 5 للتنبيهات
        low_stock_list.append({
            "id": m.id,
            "sku": m.sku,
            "name": m.name,
            "current_qty": float(m.current_qty),
            "reorder_level": float(m.reorder_level),
            "max_level": float(m.max_level)
        })

    # 3. حساب القيمة الإجمالية
    total_value = 0
    try:
        agg = quants.annotate(
            val=F('quantity') * F('material__standard_price')
        ).aggregate(total=Sum('val'))
        total_value = agg['total'] if agg['total'] is not None else 0
    except Exception: total_value = 0
        
    # 4. حساب نسبة الإشغال (Capacity)
    total_bins = StorageBin.objects.filter(storage_location__plant__opco_id=active_opco_id).count()
    occupied_bins = quants.filter(quantity__gt=0).values('storage_bin').distinct().count()
    capacity_pct = int((occupied_bins / total_bins * 100)) if total_bins > 0 else 0

    # 5. الأصناف الراكدة (Stagnant Items > 90 days)
    from django.utils import timezone
    from datetime import timedelta
    ninety_days_ago = timezone.now() - timedelta(days=90)
    
    stagnant_count = items_count - StockMove.objects.filter(
        opco_id=active_opco_id, created_at__gte=ninety_days_ago
    ).values('material_id').distinct().count()
    stagnant_count = max(0, stagnant_count)

    # 6. معدل التلبية (Fulfillment Rate)
    SalesOrder = apps.get_model('sales', 'SalesOrder')
    total_sos = SalesOrder.objects.filter(opco_id=active_opco_id).exclude(status='CANCELLED').count()
    shipped_sos = SalesOrder.objects.filter(opco_id=active_opco_id, status__in=['SHIPPED', 'DELIVERED']).count()
    fulfillment_rate = round((shipped_sos / total_sos * 100), 1) if total_sos > 0 else 0

    # 7. طابور العمليات (Operations Queue)
    PurchaseOrder = apps.get_model('procurement', 'PurchaseOrder')
    pending_pos = PurchaseOrder.objects.filter(opco_id=active_opco_id, status='CONFIRMED').order_by('-created_at')[:5]
    pending_sos = SalesOrder.objects.filter(opco_id=active_opco_id, status='CONFIRMED').order_by('-created_at')[:5]
    
    lang = getattr(request, 'LANGUAGE_CODE', 'en')
    operations = []
    for po in pending_pos:
        operations.append({
            "id": po.id, "ref": po.po_number, "type": "IN",
            "type_label": "استلام مشتريات" if lang == 'ar' else "PO Receipt",
            "owner": po.vendor.name if po.vendor else "Unknown", "status": "Pending"
        })
    for so in pending_sos:
        operations.append({
            "id": so.id, "ref": so.so_number, "type": "OUT",
            "type_label": "صرف مبيعات" if lang == 'ar' else "SO Delivery",
            "owner": so.customer.name if so.customer else "Unknown", "status": "Pending"
        })

    return Response({
        "plants": plants_count,
        "items": items_count,
        "total_value": float(total_value),
        "low_stock": low_stock_count,
        "low_stock_list": low_stock_list, # قائمة الأصناف للتنبيهات
        "stagnant_count": stagnant_count,
        "fulfillment_rate": fulfillment_rate,
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

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        if StockQuant.objects.filter(plant=instance, quantity__gt=0).exists():
            return Response(
                {"error": "لا يمكن حذف المنشأة لوجود رصيد بضاعة بها." if is_arabic else "Cannot delete plant because it has stock balance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='import')
    def import_plants(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        active_opco = self.get_active_opco()
        
        try:
            if file.name.endswith('.csv'):
                headers, rows = parse_csv_file(file)
            else:
                try:
                    import pandas as pd
                    df = pd.read_excel(file)
                    headers = [str(c).strip() for c in df.columns]
                    rows = []
                    for _, r in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            val = r[col]
                            row_dict[str(col).strip()] = str(val).strip() if pd.notna(val) else ''
                        rows.append(row_dict)
                except ImportError:
                    return Response({"error": "Excel import is not supported because 'pandas' is not installed. Please save your file as CSV (.csv) and try again."}, status=status.HTTP_400_BAD_REQUEST)
                
            success_count = 0
            skipped_count = 0
            
            # Map Arabic and English headers
            code_col = 'الكود' if 'الكود' in headers else ('كود المنشأة' if 'كود المنشأة' in headers else ('Plant Code' if 'Plant Code' in headers else 'Code'))
            name_col = 'الاسم' if 'الاسم' in headers else ('اسم المنشأة' if 'اسم المنشأة' in headers else ('Plant Name' if 'Plant Name' in headers else 'Name'))
            
            if code_col not in headers or name_col not in headers:
                return Response({"error": f"Missing required columns. Ensure '{code_col}' and '{name_col}' exist."}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                for row in rows:
                    code = str(row.get(code_col, '')).strip()
                    name = str(row.get(name_col, '')).strip()
                    
                    if not code or not name or str(code).lower() == 'nan' or str(name).lower() == 'nan':
                        continue
                        
                    # Check uniqueness
                    if Plant.objects.filter(opco=active_opco, code=code).exists() or Plant.objects.filter(opco=active_opco, name=name).exists():
                        skipped_count += 1
                        continue
                        
                    Plant.objects.create(
                        opco=active_opco,
                        code=code[:5],
                        name=name[:100]
                    )
                    success_count += 1
                    
            return Response({
                "message": "Import successful",
                "success_count": success_count,
                "skipped_count": skipped_count
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StorageLocationViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        if StockQuant.objects.filter(storage_bin__storage_location=instance, quantity__gt=0).exists():
            return Response(
                {"error": "لا يمكن حذف موقع التخزين لوجود رصيد بضاعة به." if is_arabic else "Cannot delete storage location because it has stock balance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='import')
    def import_locations(self, request):
        file = request.FILES.get('file')
        if not file: return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        active_opco = self.get_active_opco()
        if not active_opco: return Response({"error": "No active company"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                headers, rows = parse_csv_file(file)
            else:
                try:
                    import pandas as pd
                    df = pd.read_excel(file)
                    headers = [str(c).strip() for c in df.columns]
                    rows = []
                    for _, r in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            val = r[col]
                            row_dict[str(col).strip()] = str(val).strip() if pd.notna(val) else ''
                        rows.append(row_dict)
                except ImportError:
                    return Response({"error": "Excel import is not supported because 'pandas' is not installed. Please save your file as CSV (.csv) and try again."}, status=status.HTTP_400_BAD_REQUEST)

            success_count, skipped_count = 0, 0
            
            pcode_col = 'كود المنشأة' if 'كود المنشأة' in headers else 'Plant Code'
            code_col = 'كود الموقع' if 'كود الموقع' in headers else 'Location Code'
            name_col = 'اسم الموقع' if 'اسم الموقع' in headers else 'Location Name'
            
            if not all(col in headers for col in [pcode_col, code_col, name_col]):
                return Response({"error": "Missing columns. Ensure Plant Code, Location Code, and Location Name exist."}, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                for row in rows:
                    pcode = str(row.get(pcode_col, '')).strip()
                    code = str(row.get(code_col, '')).strip()
                    name = str(row.get(name_col, '')).strip()
                    
                    if not pcode or not code or not name or str(code).lower() == 'nan': continue
                        
                    plant = Plant.objects.filter(opco=active_opco, code=pcode).first()
                    if not plant:
                        skipped_count += 1
                        continue
                        
                    if StorageLocation.objects.filter(plant=plant, code=code).exists() or StorageLocation.objects.filter(plant=plant, name=name).exists():
                        skipped_count += 1
                        continue
                        
                    StorageLocation.objects.create(plant=plant, code=code[:10], name=name[:100])
                    success_count += 1
                    
            return Response({"message": "Import successful", "success_count": success_count, "skipped_count": skipped_count})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StorageBinViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StorageBin.objects.all()
    serializer_class = StorageBinSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        if StockQuant.objects.filter(storage_bin=instance, quantity__gt=0).exists():
            return Response(
                {"error": "لا يمكن حذف الرف لوجود رصيد بضاعة به." if is_arabic else "Cannot delete bin because it has stock balance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='import')
    def import_bins(self, request):
        file = request.FILES.get('file')
        if not file: return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        active_opco = self.get_active_opco()
        if not active_opco: return Response({"error": "No active company"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                headers, rows = parse_csv_file(file)
            else:
                try:
                    import pandas as pd
                    df = pd.read_excel(file)
                    headers = [str(c).strip() for c in df.columns]
                    rows = []
                    for _, r in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            val = r[col]
                            row_dict[str(col).strip()] = str(val).strip() if pd.notna(val) else ''
                        rows.append(row_dict)
                except ImportError:
                    return Response({"error": "Excel import is not supported because 'pandas' is not installed. Please save your file as CSV (.csv) and try again."}, status=status.HTTP_400_BAD_REQUEST)

            success_count, skipped_count = 0, 0
            
            lcode_col = 'كود الموقع' if 'كود الموقع' in headers else 'Location Code'
            code_col = 'كود الرف' if 'كود الرف' in headers else 'Bin Code'
            
            if not all(col in headers for col in [lcode_col, code_col]):
                return Response({"error": "Missing columns. Ensure Location Code and Bin Code exist."}, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                for row in rows:
                    lcode = str(row.get(lcode_col, '')).strip()
                    code = str(row.get(code_col, '')).strip()
                    
                    if not lcode or not code or str(code).lower() == 'nan': continue
                        
                    loc = StorageLocation.objects.filter(plant__opco=active_opco, code=lcode).first()
                    if not loc:
                        skipped_count += 1
                        continue
                        
                    if StorageBin.objects.filter(storage_location=loc, code=code).exists():
                        skipped_count += 1
                        continue
                        
                    StorageBin.objects.create(storage_location=loc, code=code[:20])
                    success_count += 1
                    
            return Response({"message": "Import successful", "success_count": success_count, "skipped_count": skipped_count})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StockQuantViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StockQuant.objects.all()
    serializer_class = StockQuantSerializer

    @action(detail=False, methods=['get'])
    def print_audit(self, request):
        """ توليد تقرير جرد للأصناف الحالية """
        from django.utils import timezone
        from redivio_project.utils.pdf import render_to_pdf
        
        active_opco = self.get_active_opco()
        quants = StockQuant.objects.filter(opco=active_opco).select_related('material', 'storage_bin')
        
        data = [{
            "material": q.material.name,
            "sku": getattr(q.material, 'sku', "N/A"),
            "bin": q.storage_bin.code,
            "quantity": float(q.quantity)
        } for q in quants]
        
        context = {
            "report_date": timezone.now(),
            "opco": active_opco,
            "items": data
        }

        if request.query_params.get('pdf') == '1':
            # ✅ Fix: Use standard render instead of render_to_pdf for perfect Arabic support via Browser Print
            return render(request, 'wms/print_audit.html', context)
        
        return Response({
            "report_date": context["report_date"],
            "opco_name": active_opco.name,
            "items": data
        })

class StockMoveViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StockMove.objects.all().order_by('-id')
    serializer_class = StockMoveSerializer

    def create(self, request, *args, **kwargs):
        active_opco_id = self._get_opco_id()
        if active_opco_id:
            opco = OpCo.objects.filter(id=active_opco_id).first()
            if opco and opco.is_inventory_active:
                is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
                err_msg = "لا يمكن إجراء حركات مخزنية أثناء عملية الجرد النشطة." if is_arabic else "Cannot perform stock moves. Inventory count is currently active and stock movements are frozen."
                return Response({"error": err_msg}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        from django.db.models import Q
        queryset = super().get_queryset()
        
        material_id = self.request.query_params.get('material_id')
        if material_id and material_id != 'null':
            queryset = queryset.filter(material_id=material_id)
            
        location_id = self.request.query_params.get('location_id')
        if location_id and location_id.strip() and location_id != 'null':
            queryset = queryset.filter(
                Q(source_bin__storage_location_id=location_id) | 
                Q(dest_bin__storage_location_id=location_id)
            )
            
        date_from = self.request.query_params.get('date_from')
        if date_from and date_from != 'null':
            queryset = queryset.filter(created_at__date__gte=date_from)
            
        date_to = self.request.query_params.get('date_to')
        if date_to and date_to != 'null':
            queryset = queryset.filter(created_at__date__lte=date_to)

        contact_id = self.request.query_params.get('contact_id')
        if contact_id and contact_id != 'null':
            queryset = queryset.filter(
                Q(customer_id=contact_id) | 
                Q(vendor_id=contact_id)
            )

        return queryset

    @action(detail=False, methods=['get'])
    def by_contact(self, request):
        """ تجميع الحركات حسب العميل/المورد """
        from django.db.models import Sum, Count, Q
        active_opco_id = self._get_opco_id()
        if not active_opco_id:
            return Response({"error": "OpCo ID required"}, status=400)

        # تجميع حركات الصادر (OUT) للعملاء
        customers = StockMove.objects.filter(
            opco_id=active_opco_id, customer__isnull=False, move_type='OUT'
        ).values('customer_id', 'customer__name').annotate(
            total_qty=Sum('quantity'),
            total_value=Sum(models.F('quantity') * models.F('sales_price')),
            move_count=Count('id')
        )

        # تجميع حركات الوارد (IN) من الموردين
        vendors = StockMove.objects.filter(
            opco_id=active_opco_id, vendor__isnull=False, move_type='IN'
        ).values('vendor_id', 'vendor__name').annotate(
            total_qty=Sum('quantity'),
            total_value=Sum(models.F('quantity') * models.F('unit_cost')),
            move_count=Count('id')
        )

        return Response({
            "customers": list(customers),
            "vendors": list(vendors)
        })


    @action(detail=False, methods=['get'])
    def last_price(self, request):
        """ جلب آخر سعر (شراء أو بيع) للصنف بناءً على نوع الحركة والشركة والطرف الثاني """
        material_id = request.query_params.get('material_id')
        move_type = request.query_params.get('move_type', 'IN')
        opco_id = self.get_active_opco().id
        
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

    @action(detail=True, methods=['get'])
    def print(self, request, pk=None):
        """ توليد صفحة طباعة مخصصة للحركة المخزنية اليدوية (تدعم تعدد الأصناف) """
        current_move = self.get_object()
        
        # جلب كل الحركات اللي ليها نفس المرجع وفي نفس التوقيت تقريباً
        all_moves = StockMove.objects.filter(
            reference=current_move.reference,
            opco=current_move.opco,
            move_type=current_move.move_type
        ).filter(created_at__gte=current_move.created_at - models.DurationField().to_python('00:01:00')) # في حدود دقيقة
        
        # حساب الإجماليات
        total_val = sum(
            (m.quantity * (m.unit_cost if m.move_type == 'IN' else m.sales_price))
            for m in all_moves
        )
        
        from django.shortcuts import render
        context = {
            'main_move': current_move,
            'moves': all_moves,
            'is_receipt': current_move.move_type == 'IN',
            'opco': current_move.opco,
            'total_val': total_val,
            'vat_amount': total_val * Decimal('0.15'),
            'grand_total': total_val * Decimal('1.15')
        }
        return render(request, 'wms/print_move.html', context)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data
        opco_id = self.get_active_opco().id
        
        receipt_type = data.get('receipt_type')
        move_type = data.get('move_type') or ('IN' if receipt_type == 'PURCHASE' else 'OUT' if receipt_type in ['ISSUE', 'SALE'] else 'TRANSFER')
        items = data.get('items', [])
        
        po_id = data.get('po_id')
        so_id = data.get('so_id')
        contact_id = data.get('contact_id')
        manual_contact_name = data.get('manual_contact_name')

        if not items:
            return Response({"error": "No items provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 🚀 0. Auto-Create/Resolve Contact logic
        reference_text = "Manual Move"
        resolved_vendor = None
        resolved_customer = None
        
        if move_type == 'IN':
            if manual_contact_name:
                try:
                    Vendor = apps.get_model('procurement', 'Vendor')
                    manual_code = f"V-MAN-{manual_contact_name[:10].upper()}-{opco_id}"
                    resolved_vendor, _ = Vendor.objects.get_or_create(
                        opco_id=opco_id, name=manual_contact_name,
                        defaults={'code': manual_code}
                    )
                    reference_text = f"Receipt from {resolved_vendor.name}"
                    manual_contact_name = resolved_vendor.name # Sync name
                except Exception: reference_text = f"Receipt from {manual_contact_name}"
            elif contact_id:
                try:
                    Vendor = apps.get_model('procurement', 'Vendor')
                    resolved_vendor = Vendor.objects.get(id=contact_id)
                    manual_contact_name = resolved_vendor.name
                    reference_text = f"Receipt from {resolved_vendor.name}"
                except Exception: pass

        elif move_type == 'OUT':
            if manual_contact_name:
                try:
                    Customer = apps.get_model('sales', 'Customer')
                    manual_code = f"C-MAN-{manual_contact_name[:10].upper()}-{opco_id}"
                    resolved_customer, _ = Customer.objects.get_or_create(
                        opco_id=opco_id, name=manual_contact_name,
                        defaults={'code': manual_code}
                    )
                    reference_text = f"Issue to {resolved_customer.name}"
                    manual_contact_name = resolved_customer.name # Sync name
                except Exception: reference_text = f"Issue to {manual_contact_name}"
            elif contact_id:
                try:
                    Customer = apps.get_model('sales', 'Customer')
                    resolved_customer = Customer.objects.get(id=contact_id)
                    manual_contact_name = resolved_customer.name
                    reference_text = f"Issue to {resolved_customer.name}"
                except Exception: pass

        # 🚀 1. Process Material Inbound (Receipt)
        if move_type == 'IN':
            for item in items:
                qty = Decimal(str(item.get('quantity', 0)))
                unit_cost = Decimal(str(item.get('unit_cost', 0)))
                pay_method = data.get('payment_method', 'CASH')
                if qty <= 0: continue
                material_id = item.get('material_id')
                
                # Auto-resolve Bin
                bin_id = item.get('bin_id')
                dest_bin = None
                if bin_id: dest_bin = StorageBin.objects.get(id=bin_id)
                else: dest_bin = StorageBin.objects.filter(storage_location__plant__opco_id=opco_id).first()
                if not dest_bin: return Response({"error": "No storage bin configured"}, status=400)
                
                # --- 📈 WAC Calculation ---
                try:
                    Material = apps.get_model('item_master', 'Material')
                    mat_obj = Material.objects.get(id=material_id)
                    qty_before = StockQuant.objects.filter(opco_id=opco_id, material_id=material_id).aggregate(total=Sum('quantity'))['total'] or Decimal('0')
                    cost_before = Decimal(str(mat_obj.standard_price or 0))
                    total_qty_after = qty_before + qty
                    
                    if total_qty_after > 0 and unit_cost > 0:
                        new_wac = ((qty_before * cost_before) + (qty * unit_cost)) / total_qty_after
                        mat_obj.standard_price = new_wac.quantize(Decimal('0.0001')) # Higher precision for WAC
                        mat_obj.save()
                except Exception as e: print(f"WAC Update Error: {e}")

                move = StockMove.objects.create(
                    opco_id=opco_id, material_id=material_id, quantity=qty, unit_cost=unit_cost,
                    payment_method=pay_method, move_type='IN', dest_bin=dest_bin,
                    vendor=resolved_vendor, # Set Foreign Key!
                    vendor_name=manual_contact_name, # Set Display Name
                    tax_rate=Decimal(str(data.get('tax_rate', 15))),
                    reference=f"PO {po_id}" if po_id else reference_text
                )

        # 🚀 3. Link to POS Cash Flow if payment is CASH
        if move_type == 'IN' and data.get('payment_method') == 'CASH':
            try:
                POSSession = apps.get_model('restaurant_pos', 'POSSession')
                POSCashTransaction = apps.get_model('restaurant_pos', 'POSCashTransaction')
                session = POSSession.objects.filter(opco_id=opco_id, is_closed=False).first()
                if session:
                    total_purchase_val = sum(Decimal(str(i.get('quantity', 0))) * Decimal(str(i.get('unit_cost', 0))) for i in items)
                    if total_purchase_val > 0:
                        POSCashTransaction.objects.create(
                            session=session,
                            type='OUT',
                            amount=total_purchase_val,
                            reason=f"Stock Purchase: {reference_text}"
                        )
                        session.total_expenses += total_purchase_val
                        session.save()
            except Exception as e: 
                print(f"POS Link Error: {e}")

        # 🚚 2. Process Material Outbound (Delivery)
        elif move_type == 'OUT':
            for item in items:
                qty = Decimal(str(item.get('quantity', 0)))
                sales_price = Decimal(str(item.get('sales_price', 0)))
                coll_method = data.get('payment_method', 'CASH')
                if qty <= 0: continue
                material_id = item.get('material_id')
                
                # Auto-resolve Bin
                bin_id = item.get('bin_id')
                source_bin = None
                if bin_id: source_bin = StorageBin.objects.get(id=bin_id)
                else:
                    best_quant = StockQuant.objects.filter(opco_id=opco_id, material_id=material_id, quantity__gte=qty).order_by('-quantity').first()
                    source_bin = best_quant.storage_bin if best_quant else StorageBin.objects.filter(storage_location__plant__opco_id=opco_id).first()
                if not source_bin: return Response({"error": "No storage bin configured"}, status=400)

                # Allow negative stock for manual moves to avoid blocking user setup
                # quant.save() is handled by model.save()
                move = StockMove.objects.create(
                    opco_id=opco_id, material_id=material_id, quantity=qty, sales_price=sales_price,
                    payment_method=coll_method, move_type='OUT', source_bin=source_bin,
                    customer=resolved_customer, # Set Foreign Key!
                    vendor_name=manual_contact_name, # Set Display Name
                    tax_rate=Decimal(str(data.get('tax_rate', 15))),
                    reference=f"SO {so_id}" if so_id else reference_text
                )

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

class OpeningInventoryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_opco_id(self, request):
        val = (request.query_params.get('opco') or 
               request.data.get('opco') or 
               request.session.get('active_opco_id'))
        if val == 'null' or val == 'undefined':
            return None
        return val

    def check_manager_permissions(self, request, opco_id):
        if request.user.is_superuser:
            return True
        if OpCo.objects.filter(id=opco_id, owner=request.user).exists():
            return True
        from apps.core.models import CompanyUser
        return CompanyUser.objects.filter(
            user=request.user, 
            company_id=opco_id, 
            role__in=['admin', 'administrator', 'manager']
        ).exists()

    def get(self, request):
        opco_id = self._get_opco_id(request)
        if not opco_id:
            return Response({"error": "OpCo ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not self.check_manager_permissions(request, opco_id):
            return Response({"error": "Only Administrators or Managers are authorized to perform this operation."}, status=status.HTTP_403_FORBIDDEN)

        opco = OpCo.objects.filter(id=opco_id).first()
        if not opco:
            return Response({"error": "OpCo not found"}, status=status.HTTP_404_NOT_FOUND)

        action_param = request.query_params.get('action', 'status')

        if action_param == 'status':
            return Response({
                "is_inventory_active": opco.is_inventory_active
            })

        elif action_param == 'print_sheet':
            from apps.item_master.models import Material
            from django.utils import timezone
            from django.db.models import Q
            materials = Material.all_objects.filter(opco=opco).filter(
                Q(recipe__isnull=True) | Q(recipe__ingredients__isnull=True)
            ).distinct().order_by('name')
            
            items_data = []
            for m in materials:
                from apps.item_master.models import MaterialLocation
                loc = MaterialLocation.objects.filter(material=m, material__opco=opco, is_primary=True).first()
                if not loc:
                    loc = MaterialLocation.objects.filter(material=m, material__opco=opco).first()
                
                bin_code = loc.storage_bin.code if loc and loc.storage_bin else "---"
                items_data.append({
                    "name": m.name,
                    "sku": m.sku,
                    "bin_code": bin_code
                })

            context = {
                "report_date": timezone.now(),
                "opco": opco,
                "items": items_data
            }
            return render(request, 'wms/print_opening_sheet.html', context)

        elif action_param == 'export_excel':
            from apps.item_master.models import Material
            import csv
            import io
            from django.http import HttpResponse
            from django.db.models import Q

            materials = Material.all_objects.filter(opco=opco).filter(
                Q(recipe__isnull=True) | Q(recipe__ingredients__isnull=True)
            ).distinct().order_by('name')
            
            output = io.StringIO()
            output.write('\ufeff')  # UTF-8 BOM
            writer = csv.writer(output)
            
            writer.writerow([
                "رمز الصنف (SKU)",
                "اسم الصنف (Material Name)",
                "الرف / الموقع الافتراضي (Bin Code)",
                "الكمية الفعلية (Physical Qty)"
            ])
            
            for m in materials:
                from apps.item_master.models import MaterialLocation
                loc = MaterialLocation.objects.filter(material=m, material__opco=opco, is_primary=True).first()
                if not loc:
                    loc = MaterialLocation.objects.filter(material=m, material__opco=opco).first()
                
                bin_code = loc.storage_bin.code if loc and loc.storage_bin else "MAIN"
                writer.writerow([
                    m.sku,
                    m.name,
                    bin_code,
                    ""
                ])
                
            response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="opening_inventory_sheet_{opco.code}.csv"'
            return response

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        opco_id = self._get_opco_id(request)
        if not opco_id:
            return Response({"error": "OpCo ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        if not self.check_manager_permissions(request, opco_id):
            return Response({"error": "Only Administrators or Managers are authorized to perform this operation."}, status=status.HTTP_403_FORBIDDEN)

        opco = OpCo.objects.filter(id=opco_id).first()
        if not opco:
            return Response({"error": "OpCo not found"}, status=status.HTTP_404_NOT_FOUND)

        action_param = request.data.get('action')

        if action_param == 'start':
            opco.is_inventory_active = True
            opco.save()
            return Response({"success": True, "is_inventory_active": True})

        elif action_param == 'cancel':
            opco.is_inventory_active = False
            opco.save()
            return Response({"success": True, "is_inventory_active": False})

        elif action_param == 'upload':
            file = request.FILES.get('file')
            if not file:
                return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                import pandas as pd
                if file.name.endswith('.csv'):
                    content = file.read()
                    try:
                        decoded = content.decode('utf-8-sig')
                    except UnicodeDecodeError:
                        decoded = content.decode('windows-1256', errors='ignore')
                    
                    import csv
                    reader = csv.DictReader(decoded.splitlines())
                    rows = [r for r in reader]
                    headers = reader.fieldnames or []
                else:
                    df = pd.read_excel(file)
                    rows = df.to_dict(orient='records')
                    headers = [str(c).strip() for c in df.columns]

                sku_col = None
                bin_col = None
                qty_col = None

                for h in headers:
                    h_clean = str(h).strip().lower()
                    if 'sku' in h_clean or 'صنف' in h_clean or 'رمز' in h_clean:
                        sku_col = h
                    elif 'bin' in h_clean or 'رف' in h_clean:
                        bin_col = h
                    elif 'qty' in h_clean or 'quant' in h_clean or 'كمية' in h_clean or 'عدد' in h_clean:
                        qty_col = h

                if not sku_col:
                    return Response({"error": "تعذر العثور على عمود الصنف/SKU. يرجى التأكد من احتواء الملف على عمود 'SKU'."}, status=status.HTTP_400_BAD_REQUEST)
                if not bin_col:
                    return Response({"error": "تعذر العثور على عمود الرف/Bin. يرجى التأكد من احتواء الملف على عمود 'Bin Code'."}, status=status.HTTP_400_BAD_REQUEST)
                if not qty_col:
                    return Response({"error": "تعذر العثور على عمود الكمية/Quantity. يرجى التأكد من احتواء الملف على عمود 'Quantity'."}, status=status.HTTP_400_BAD_REQUEST)

                from apps.item_master.models import Material

                comparison_items = []
                uploaded_keys = set()
                errors = []

                for idx, r in enumerate(rows):
                    sku_val = str(r.get(sku_col, '')).strip()
                    bin_val = str(r.get(bin_col, '')).strip()
                    qty_val = r.get(qty_col)

                    if not sku_val or sku_val.lower() == 'nan':
                        continue

                    try:
                        counted_qty = float(qty_val) if qty_val is not None and str(qty_val).lower() != 'nan' else 0.0
                    except:
                        counted_qty = 0.0

                    material = Material.all_objects.filter(sku=sku_val, opco=opco).first()
                    if not material:
                        errors.append(f"السطر {idx + 2}: الصنف ذو الرمز ({sku_val}) غير موجود بالنظام.")
                        continue

                    has_recipe = False
                    try:
                        has_recipe = material.recipe and material.recipe.ingredients.exists()
                    except ObjectDoesNotExist:
                        pass
                    bin_obj = StorageBin.objects.filter(code=bin_val, storage_location__plant__opco=opco).first()
                    
                    system_qty = 0.0
                    if bin_obj:
                        quant = StockQuant.objects.filter(storage_bin=bin_obj, material=material, opco=opco).first()
                        if quant:
                            system_qty = float(quant.quantity)

                    comparison_items.append({
                        "sku": sku_val,
                        "material_name": material.name,
                        "bin_code": bin_val,
                        "system_qty": system_qty,
                        "counted_qty": counted_qty,
                        "difference": counted_qty - system_qty,
                        "has_recipe": has_recipe
                    })
                    uploaded_keys.add((sku_val, bin_val))

                all_quants = StockQuant.objects.filter(opco=opco).select_related('material', 'storage_bin')
                for q in all_quants:
                    key = (q.material.sku, q.storage_bin.code)
                    if key not in uploaded_keys:
                        has_recipe = False
                        try:
                            has_recipe = q.material.recipe and q.material.recipe.ingredients.exists()
                        except ObjectDoesNotExist:
                            pass
                        comparison_items.append({
                            "sku": q.material.sku,
                            "material_name": q.material.name,
                            "bin_code": q.storage_bin.code,
                            "system_qty": float(q.quantity),
                            "counted_qty": 0.0,
                            "difference": -float(q.quantity),
                            "has_recipe": has_recipe
                        })

                return Response({
                    "success": True,
                    "items": comparison_items,
                    "errors": errors
                })

            except Exception as e:
                return Response({"error": f"Error parsing file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        elif action_param == 'commit':
            items = request.data.get('items', [])
            if not items:
                return Response({"error": "No items to commit"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                from apps.item_master.models import Material
                with transaction.atomic():
                    opco.is_inventory_active = False
                    opco.save()

                    for item in items:
                        sku = item.get('sku')
                        bin_code = item.get('bin_code')
                        counted_qty = float(item.get('counted_qty', 0))

                        material = Material.all_objects.filter(sku=sku, opco=opco).first()
                        if not material:
                            continue

                        bin_obj = StorageBin.objects.filter(code=bin_code, storage_location__plant__opco=opco).first()
                        if not bin_obj:
                            loc = StorageLocation.objects.filter(plant__opco=opco).first()
                            if not loc:
                                plant = Plant.objects.filter(opco=opco).first()
                                if not plant:
                                    plant = Plant.objects.create(opco=opco, code="MAIN", name=f"{opco.name} Warehouse")
                                loc = StorageLocation.objects.create(plant=plant, code="IN-1", name="Receiving")
                            bin_obj = StorageBin.objects.create(storage_location=loc, code=bin_code)

                        quant = StockQuant.objects.filter(storage_bin=bin_obj, material=material, opco=opco).first()
                        system_qty = float(quant.quantity) if quant else 0.0

                        diff = counted_qty - system_qty
                        if diff == 0:
                            continue

                        if diff > 0:
                            StockMove.objects.create(
                                opco=opco,
                                material=material,
                                source_bin=None,
                                dest_bin=bin_obj,
                                quantity=diff,
                                reference="Opening Inventory Count (IN Adjustment)",
                                move_type='IN'
                            )
                        else:
                            StockMove.objects.create(
                                opco=opco,
                                material=material,
                                source_bin=bin_obj,
                                dest_bin=None,
                                quantity=abs(diff),
                                reference="Opening Inventory Count (OUT Adjustment)",
                                move_type='OUT'
                            )

                return Response({"success": True, "message": "Opening inventory count saved and adjusted successfully."})

            except Exception as e:
                return Response({"error": f"Failed to commit inventory count: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)