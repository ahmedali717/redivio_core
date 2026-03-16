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
from .models import Vendor, PurchaseOrder, PurchaseOrderLine
from .serializers import VendorSerializer, PurchaseOrderSerializer, PurchaseOrderLineSerializer

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