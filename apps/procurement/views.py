from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

# PDF Generation Imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.shortcuts import render, get_object_or_404
from redivio_project.utils.pdf import render_to_pdf

# Models & Serializers
# الاستيراد النسبي (.) صحيح لأننا داخل نفس التطبيق
from .models import Vendor, PurchaseOrder, PurchaseOrderLine , StockReceipt
from .serializers import VendorSerializer, PurchaseOrderSerializer, PurchaseOrderLineSerializer , StockReceiptSerializer

# ✅ التصحيح: يجب استخدام apps.wms بدلاً من wms مباشرة
from apps.wms.models import StorageBin

# =========================================================
#  1. Helper Mixin
# =========================================================
class OpcoAwareMixin:
    """
    يقوم تلقائياً بربط السجل بالشركة (OpCo) بناءً على الجلسة الحالية
    أو البيانات المرسلة، وتصفية السجلات للشركة النشطة فقط.
    """
    def _get_opco_id(self):
        return (self.request.query_params.get('opco') or 
                self.request.data.get('opco') or 
                self.request.session.get('active_opco_id'))

    def get_queryset(self):
        queryset = super().get_queryset()
        opco_id = self._get_opco_id()
        if opco_id:
            try:
                queryset = queryset.filter(opco_id=int(opco_id))
            except (ValueError, TypeError):
                pass
        return queryset

    def perform_create(self, serializer):
        opco_id = self._get_opco_id()
        if opco_id:
            serializer.save(opco_id=int(opco_id))
        else:
            serializer.save()

# =========================================================
#  2. Procurement ViewSets
# =========================================================

class VendorViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة الموردين (Suppliers) """
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    @action(detail=True, methods=['get'])
    def ledger(self, request, pk=None):
        vendor = self.get_object()
        pos = PurchaseOrder.objects.filter(vendor=vendor).order_by('-date')
        
        # تجميع الحركات (Orders & Receipts)
        history = []
        for po in pos:
            # إضافة أمر التوريد نفسه كحركة
            history.append({
                'id': po.id,
                'date': po.date,
                'type': 'PURCHASE_ORDER',
                'number': po.po_number,
                'status': po.status,
                'amount': po.extra_data.get('grand_total', 0) if po.extra_data else 0,
                'doc_type': 'PO'
            })
            
            # إضافة أذون الاستلام المرتبطة بهذا الـ PO
            for receipt in po.receipts.all():
                history.append({
                    'id': receipt.id,
                    'date': receipt.date.date(),
                    'type': 'STOCK_RECEIPT',
                    'number': receipt.receipt_number,
                    'status': 'RECEIVED',
                    'amount': 0, # الاستلام ليس له قيمة مالية مباشرة هنا
                    'doc_type': 'GRN'
                })

        # إضافة الحركات المخزنية المباشرة (مثل الاستلام المباشر من نقاط البيع)
        from apps.wms.models import StockMove
        import datetime
        moves = StockMove.objects.filter(vendor=vendor).order_by('-created_at')
        for move in moves:
            amount = move.quantity * move.unit_cost
            history.append({
                'id': move.id,
                'date': move.created_at.date() if move.created_at else None,
                'type': 'DIRECT_STOCK_MOVE_IN' if move.move_type == 'IN' else 'DIRECT_STOCK_MOVE_OUT',
                'number': move.reference or f"MOVE-{move.id}",
                'status': 'RECEIVED' if move.move_type == 'IN' else 'RETURNED',
                'amount': float(amount),
                'doc_type': 'DIRECT_GRN' if move.move_type == 'IN' else 'DIRECT_GDN'
            })
        
        # ترتيب التاريخ من الأحدث للأقدم
        history.sort(key=lambda x: x['date'] if x['date'] is not None else datetime.date.min, reverse=True)
        
        return Response({
            'vendor_name': vendor.name,
            'vendor_code': vendor.code,
            'summary': {
                'total_pos': pos.count() + moves.count(),
                'received_pos': pos.filter(status='RECEIVED').count() + moves.filter(move_type='IN').count(),
            },
            'transactions': history
        })

class PurchaseOrderViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة أوامر الشراء (PO) """
    queryset = PurchaseOrder.objects.all().order_by('-created_at')
    serializer_class = PurchaseOrderSerializer

    # --- Custom Action: Receive Goods (GR) ---
    # يقوم بتحويل حالة الطلب إلى RECEIVED وزيادة المخزون
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        po = self.get_object()
        
        # 1. التحقق من وجود رقم الصندوق (Bin ID) المستهدف
        bin_id = request.data.get('bin_id')
        if not bin_id:
            return Response({'error': 'Target Bin ID is required for receiving goods.'}, status=400)
        
        try:
            target_bin = StorageBin.objects.get(id=bin_id)
            
            # 2. استدعاء دالة الاستلام الموجودة داخل الموديل
            if hasattr(po, 'receive_items'):
                po.receive_items(target_bin)
            else:
                # Fallback logic
                po.status = 'RECEIVED'
                po.save()
            
            return Response({'status': 'Received', 'po_number': po.po_number})
            
        except StorageBin.DoesNotExist:
            return Response({'error': 'Invalid Bin ID'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        
class StockReceiptViewSet(viewsets.ModelViewSet):
    queryset = StockReceipt.objects.all().order_by('-date')
    serializer_class = StockReceiptSerializer

    def create(self, request, *args, **kwargs):
        # 1. استلام معرف أمر البيع (لو موجود)
        so_id = request.data.get('so_id')
        po_id = request.data.get('po') # للمشتريات
        
        # 2. تحديد نوع الحركة: لو فيه SO تبقى OUT (صرف)، لو فيه PO تبقى IN (إضافة)
        move_type = 'OUT' if so_id else 'IN'
        request.data['move_type'] = move_type

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # حفظ حركة المخزن (الـ Receipt والـ Moves)
                receipt = serializer.save(created_by=request.user)
                
                # ✅ حالة المشتريات: تحديث الـ PO لـ RECEIVED
                if receipt.po:
                    po = receipt.po
                    if all(line.received_quantity >= line.quantity for line in po.lines.all()):
                        po.status = 'RECEIVED'
                        po.save()

                # ✅ حالة المبيعات (الربط الجديد): تحديث الـ SO لـ DELIVERED
                if so_id:
                    from apps.sales.models import SalesOrder
                    try:
                        so = SalesOrder.objects.get(id=so_id)
                        so.status = 'DELIVERED'
                        so.save()
                    except SalesOrder.DoesNotExist:
                        pass

                # الرد للـ Vue ببيانات النجاح والطباعة
                return Response({
                    'id': receipt.id,
                    'receipt_no': receipt.receipt_number,
                    'move_type': move_type,
                    'status': 'success',
                    'print_url': f'/print/grn/{receipt.id}/' # أو رابط مستند الصرف
                }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class PurchaseOrderLineViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderLine.objects.all()
    serializer_class = PurchaseOrderLineSerializer

# =========================================================
#  3. PDF Generation View
# =========================================================

def print_po_pdf(request, pk):
    """ دالة محسنة لطباعة أمر الشراء بتنسيق HTML شيك """
    try:
        po = PurchaseOrder.objects.get(pk=pk)
        return render_to_pdf('procurement/print_po.html', {'po': po})
    except PurchaseOrder.DoesNotExist:
        return HttpResponse("أمر التوريد غير موجود", status=404)
    
def print_grn_pdf(request, pk):
    """ دالة عرض صفحة طباعة مستند الاستلام (GRN) """
    receipt = get_object_or_404(StockReceipt, pk=pk)
    return render_to_pdf('procurement/print_grn.html', {'receipt': receipt})