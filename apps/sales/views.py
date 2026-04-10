from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.db import transaction
import decimal

# Models & Serializers
from .models import Customer, SalesOrder, SalesOrderLine, SalesInvoice, CustomerPayment, StockDelivery
from .serializers import (
    CustomerSerializer, SalesOrderSerializer, SalesOrderLineSerializer,
    SalesInvoiceSerializer, CustomerPaymentSerializer, StockDeliverySerializer
)

# from apps.wms.models import StorageBin # ❌ إزالة لـمنع الـ Circular Import

# =========================================================
#  1. Helper Mixin
# =========================================================
class OpcoAwareMixin:
    def _get_opco_id(self):
        # بنحاول نجيب الـ ID من الرابط، لو مفيش بنجيبه من الجلسة (Session)
        return self.request.query_params.get('opco') or self.request.session.get('active_opco_id')

    def get_queryset(self):
        # 1. بنجيب الـ queryset الأصلية المعرفة في الـ ViewSet
        queryset = super().get_queryset()
        opco_id = self._get_opco_id()
        
        # 2. لو فيه opco_id، بنعمل فلترة
        if opco_id:
            try:
                queryset = queryset.filter(opco_id=int(opco_id))
            except (ValueError, TypeError):
                pass
        
        # 3. دعم الفلترة بالحالة (status)
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset

    def perform_create(self, serializer):
        opco_id = self._get_opco_id()
        if opco_id:
            # بنحفظ الـ opco_id مع الكائن الجديد
            serializer.save(opco_id=int(opco_id))
        else:
            serializer.save()

# =========================================================
#  2. Sales ViewSets
# =========================================================

class CustomerViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('name')
    serializer_class = CustomerSerializer

class SalesOrderViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all().order_by('-created_at')
    serializer_class = SalesOrderSerializer

    def create(self, request, *args, **kwargs):
        """Create SO with lines atomically."""
        # 🔒 تأمين جلب البيانات لمنع انهيار الـ Database
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        
        # استخراج الخطوط بدون حذفها من الداتا الأصلية في البداية
        lines_raw = data.get('lines', [])
        
        # التأكد التام من وجود OpCo و Customer كأرقام صحيحة
        opco_val = self._get_opco_id() or data.get('opco')
        customer_val = data.get('customer')
        
        try:
            if opco_val: data['opco'] = int(float(str(opco_val)))
            if customer_val: data['customer'] = int(float(str(customer_val)))
        except (ValueError, TypeError):
            pass # نترك الـ serializer يظهر خطأ التحقق (Validation Error)

        with transaction.atomic():
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            so = serializer.save()

            total = decimal.Decimal('0.00')
            for item in lines_raw:
                material_id = item.get('material')
                if not material_id: continue
                
                # تأمين القيم المالية (0 كقيمة افتراضية صريحة)
                raw_q = item.get('quantity', 0)
                raw_p = item.get('unit_price', 0)
                
                q = decimal.Decimal(str(raw_q)) if raw_q not in [None, ''] else decimal.Decimal('0.00')
                p = decimal.Decimal(str(raw_p)) if raw_p not in [None, ''] else decimal.Decimal('0.00')
                
                line_total = (q * p).quantize(decimal.Decimal('0.01'))
                total += line_total
                
                SalesOrderLine.objects.create(
                    so=so,
                    material_id=material_id,
                    quantity=q,
                    unit_price=p,
                    total=line_total
                )
            
            # Update totals with 15% VAT
            tax = (total * decimal.Decimal('0.15')).quantize(decimal.Decimal('0.01'))
            so.total_amount = total
            so.tax_amount = tax
            so.grand_total = total + tax
            so.save()

        return Response(SalesOrderSerializer(so).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        so = self.get_object()
        bin_id = request.data.get('bin_id')
        if not bin_id:
            return Response({'error': 'Source Bin ID is required for delivery.'}, status=400)
        
        try:
            from django.apps import apps
            StorageBin = apps.get_model('wms', 'StorageBin')
            source_bin = StorageBin.objects.get(id=bin_id)
            
            # Use the atomic method in the model
            so.deliver_items(source_bin)
            
            return Response({
                'status': 'Delivered', 
                'so_number': so.so_number,
                'message': 'Stock moves created and invoice generated.'
            })
        except StorageBin.DoesNotExist:
            return Response({'error': 'Invalid Source Bin ID'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def generate_invoice(self, request, pk=None):
        """ إصدار فاتورة يدوياً بناءً على ما تم صرفه مخزنياً """
        so = self.get_object()
        try:
            so.create_invoice()
            return Response({
                'status': 'success',
                'message': 'Invoice generated successfully for shipped items.'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class SalesOrderLineViewSet(viewsets.ModelViewSet):
    queryset = SalesOrderLine.objects.all()
    serializer_class = SalesOrderLineSerializer

class SalesInvoiceViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = SalesInvoice.objects.all().order_by('-date')
    serializer_class = SalesInvoiceSerializer

class CustomerPaymentViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = CustomerPayment.objects.all().order_by('-date')
    serializer_class = CustomerPaymentSerializer

class StockDeliveryViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StockDelivery.objects.all().order_by('-date')
    serializer_class = StockDeliverySerializer

    def create(self, request, *args, **kwargs):
        # Implementation similar to StockReceipt but for OUT
        response = super().create(request, *args, **kwargs)
        # Additional logic if needed (e.g. auto-invoice is already handled by deliver_items)
        return response

# =========================================================
#  3. Print Views
# =========================================================

def print_so_pdf(request, pk):
    """ دالة عرض صفحة طباعة أمر البيع (SO) """
    # جلب أمر البيع أو 404
    so = get_object_or_404(SalesOrder, pk=pk)
    
    # جلب السطور المرتبطة
    # استخدمنا hasattr كصمام أمان عشان لو الـ related_name مختلف
    lines = so.lines.all() if hasattr(so, 'lines') else so.salesorderline_set.all()
    
    context = {
        'so': so,
        'lines': lines,
        'company': so.opco,
    }
    
    # المسار ده لازم يطابق صورة ملفاتك اللي بعتها (sales/sales_order_print.html)
    return render(request, 'sales/sales_order_print.html', context)

def print_delivery_pdf(request, pk):
    """ دالة عرض صفحة طباعة إذن الصرف (Delivery Note) """
    delivery = get_object_or_404(StockDelivery, pk=pk)
    
    # جلب الحركات المخزنية المرتبطة بهذا الإذن
    from apps.wms.models import StockMove
    moves = StockMove.objects.filter(reference=delivery.delivery_number)
    
    context = {
        'delivery': delivery,
        'moves': moves,
    }
    return render(request, 'sales/print_delivery.html', context)

def print_invoice_pdf(request, pk):
    """ دالة عرض صفحة طباعة الفاتورة (Invoice) """
    invoice = get_object_or_404(SalesInvoice, pk=pk)
    
    # جلب سطور أمر البيع المرتبط
    lines = []
    if invoice.sales_order:
        lines = invoice.sales_order.lines.all()
    
    context = {
        'invoice': invoice,
        'lines': lines,
        'company': invoice.opco,
        'qr_data': f"Seller: {invoice.opco.name}\nVAT: {invoice.opco.tax_id or '310123456700003'}\nTotal: {invoice.total_amount}\nDate: {invoice.date}"
    }
    return render(request, 'sales/print_invoice.html', context)