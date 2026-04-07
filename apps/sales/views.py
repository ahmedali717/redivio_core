from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.db import transaction
import decimal

# Models & Serializers
from .models import Customer, SalesOrder, SalesOrderLine, SalesInvoice, CustomerPayment
from .serializers import (
    CustomerSerializer, SalesOrderSerializer, SalesOrderLineSerializer,
    SalesInvoiceSerializer, CustomerPaymentSerializer
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
                # بنفلتر بـ opco (اسم الحقل) و opco_id (القيمة)
                # استخدام opco_id كـ argument بيخلي Django يفهم إننا بنبعت الـ ID مباشرة
                return queryset.filter(opco_id=int(opco_id))
            except (ValueError, TypeError):
                # لو الـ ID اللي مبعوت مش رقم (زي كلمة 'null') ميعملش Crash ويرجع الداتا كلها
                return queryset
        
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
        # ✅ التعديل المحوري: استخدام copy() للتعامل مع QueryDict و JSON معاً
        if hasattr(request.data, 'copy'):
            data_copy = request.data.copy()
        else:
            data_copy = dict(request.data)
            
        lines_data = data_copy.pop('lines', []) if 'lines' in data_copy else []
        
        opco_id = self._get_opco_id() or data_copy.get('opco')
        if opco_id and str(opco_id).isdigit():
            data_copy['opco'] = int(opco_id)

        with transaction.atomic():
            serializer = self.get_serializer(data=data_copy)
            serializer.is_valid(raise_exception=True)
            so = serializer.save()

            total = decimal.Decimal('0.00')
            for line in lines_data:
                if not line.get('material'):
                    continue
                
                # ✅ تصحيح: قبول الصفر وعدم إجبار القيمة على 1
                raw_qty = line.get('quantity')
                raw_price = line.get('unit_price')
                
                qty = decimal.Decimal(str(raw_qty)) if raw_qty is not None and str(raw_qty).strip() != '' else decimal.Decimal('0.00')
                price = decimal.Decimal(str(raw_price)) if raw_price is not None and str(raw_price).strip() != '' else decimal.Decimal('0.00')
                
                line_total = (qty * price).quantize(decimal.Decimal('0.01'))
                total += line_total
                
                SalesOrderLine.objects.create(
                    so=so,
                    material_id=line['material'],
                    quantity=qty,
                    unit_price=price,
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
            so.deliver_items(source_bin)
            return Response({'status': 'Delivered', 'so_number': so.so_number})
        except StorageBin.DoesNotExist:
            return Response({'error': 'Invalid Source Bin ID'}, status=404)
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