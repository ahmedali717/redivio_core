from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

# PDF Generation Imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.shortcuts import render, get_object_or_404

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
    أو البيانات المرسلة.
    """
    def perform_create(self, serializer):
        opco_id = self.request.data.get('opco')
        active_opco_id = self.request.session.get('active_opco_id')
        
        if opco_id:
            serializer.save(opco_id=opco_id)
        elif active_opco_id:
            serializer.save(opco_id=active_opco_id)
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
        
        # ترتيب التاريخ من الأحدث للأقدم
        history.sort(key=lambda x: x['date'], reverse=True)
        
        return Response({
            'vendor_name': vendor.name,
            'vendor_code': vendor.code,
            'summary': {
                'total_pos': pos.count(),
                'received_pos': pos.filter(status='RECEIVED').count(),
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
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # حفظ الحركة
            receipt = serializer.save(created_by=request.user)
            
            # تحديث حالة الـ PO (منطقك سليم هنا)
            po = receipt.po
            if all(line.received_quantity >= line.quantity for line in po.lines.all()):
                po.status = 'RECEIVED'
                po.save()

            # 🚀 التعديل الجوهري هنا:
            # لازم نرجع الـ id والـ receipt_no علشان الـ Vue يفهمهم
            return Response({
                'id': receipt.id,                           # 👈 ده اللي بيشيل الـ undefined
                'receipt_no': receipt.receipt_number,
                'print_url': f'/print/grn/{receipt.id}/',
                'status': 'success'
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
        
        # إذا كنت تريد العرض كـ HTML أولاً للتأكد من الشكل قبل تحويله لـ PDF
        # ده هيخليك تشوف التصميم في المتصفح وتعدله براحتك
        return render(request, 'procurement/print_po.html', {'po': po})
        
        # ملحوظة: إذا أردت تحويله لـ PDF حقيقي لاحقاً، 
        # سنستخدم مكتبة مثل weasyprint أو xhtml2pdf هنا.
        
    except PurchaseOrder.DoesNotExist:
        return HttpResponse("أمر التوريد غير موجود", status=404)
    
def print_grn_pdf(request, pk):
    """ دالة عرض صفحة طباعة مستند الاستلام (GRN) """
    # جلب بيانات حركة الاستلام بناءً على الـ ID
    receipt = get_object_or_404(StockReceipt, pk=pk)
    
    # استدعاء ملف الـ HTML الخاص بالتصميم
    return render(request, 'procurement/print_grn.html', {'receipt': receipt})