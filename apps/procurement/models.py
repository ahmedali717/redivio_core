import datetime
from django.db import models
from django.apps import apps
from django.conf import settings

class Vendor(models.Model):
    """ موديل الموردين """
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ('opco', 'code')

    def __str__(self):
        return f"{self.code} - {self.name}"


class PurchaseRequisition(models.Model):
    """ طلب شراء داخلي (PR - Purchase Requisition) """
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة'),
        ('SUBMITTED', 'مقدم للمراجعة'),
        ('APPROVED', 'معتمد'),
        ('REJECTED', 'مرفوض'),
        ('CONVERTED', 'تم تحويله لطلب أسعار / أمر توريد'),
        ('CANCELLED', 'ملغى'),
    ]
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    requisition_number = models.CharField(max_length=50, unique=True, blank=True)
    plant = models.ForeignKey('wms.Plant', on_delete=models.SET_NULL, null=True, blank=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date = models.DateField(auto_now_add=True)
    required_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.requisition_number:
            year = datetime.date.today().year
            last_pr = PurchaseRequisition.objects.filter(requisition_number__contains=f'PR-{year}').order_by('id').last()
            new_no = (int(last_pr.requisition_number.split('-')[-1]) + 1) if last_pr else 1
            self.requisition_number = f"PR-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.requisition_number


class PurchaseRequisitionLine(models.Model):
    """ سطور طلب الشراء """
    requisition = models.ForeignKey(PurchaseRequisition, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.requisition.requisition_number} - {self.material.name}"


class RequestForQuotation(models.Model):
    """ طلب عروض أسعار للموردين (RFQ - Request For Quotation) """
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة'),
        ('SENT', 'مرسل للموردين'),
        ('RESPONSES_RECEIVED', 'تم تلقي عروض الأسعار'),
        ('CLOSED', 'مغلق'),
        ('CANCELLED', 'ملغى'),
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    rfq_number = models.CharField(max_length=50, unique=True, blank=True)
    pr = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True, related_name='rfqs')
    date = models.DateField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    vendors = models.ManyToManyField(Vendor, related_name='rfqs', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.rfq_number:
            year = datetime.date.today().year
            last_rfq = RequestForQuotation.objects.filter(rfq_number__contains=f'RFQ-{year}').order_by('id').last()
            new_no = (int(last_rfq.rfq_number.split('-')[-1]) + 1) if last_rfq else 1
            self.rfq_number = f"RFQ-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.rfq_number


class RFQLine(models.Model):
    rfq = models.ForeignKey(RequestForQuotation, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    target_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)

    def __str__(self):
        return f"{self.rfq.rfq_number} - {self.material.name}"


class SupplierQuotation(models.Model):
    """ عرض سعر مسجل من مورد (Supplier Quotation / Offer) """
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    quotation_number = models.CharField(max_length=50, unique=True, blank=True)
    rfq = models.ForeignKey(RequestForQuotation, related_name='supplier_quotations', on_delete=models.CASCADE)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='quotations')
    date = models.DateField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)
    delivery_lead_time_days = models.IntegerField(default=1)
    payment_terms = models.CharField(max_length=100, default="CASH")
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.quotation_number:
            year = datetime.date.today().year
            last_sq = SupplierQuotation.objects.filter(quotation_number__contains=f'SQ-{year}').order_by('id').last()
            new_no = (int(last_sq.quotation_number.split('-')[-1]) + 1) if last_sq else 1
            self.quotation_number = f"SQ-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.quotation_number} ({self.vendor.name})"


class SupplierQuotationLine(models.Model):
    quotation = models.ForeignKey(SupplierQuotation, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15)
    line_total = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        subtotal = self.quantity * self.unit_price * (1 - (self.discount_rate / 100))
        self.line_total = subtotal * (1 + (self.tax_rate / 100))
        super().save(*args, **kwargs)


class QuotationComparison(models.Model):
    """ مصفوفة مقارنة عروض الأسعار واختيار العرض الفائز """
    STATUS_CHOICES = [
        ('DRAFT', 'تحت المقارنة'),
        ('APPROVED', 'تم الاعتماد واختيار المورد'),
        ('PO_GENERATED', 'تم إنشاء امر التوريد'),
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    comparison_number = models.CharField(max_length=50, unique=True, blank=True)
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.CASCADE, related_name='comparisons')
    date = models.DateField(auto_now_add=True)
    winning_vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    winning_quotation = models.ForeignKey(SupplierQuotation, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.comparison_number:
            year = datetime.date.today().year
            last_comp = QuotationComparison.objects.filter(comparison_number__contains=f'COMP-{year}').order_by('id').last()
            new_no = (int(last_comp.comparison_number.split('-')[-1]) + 1) if last_comp else 1
            self.comparison_number = f"COMP-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def generate_purchase_order(self):
        """ تحويل المقارنة المعتمدة إلى أمر توريد تلقائياً """
        if self.status == 'PO_GENERATED' or not self.winning_quotation:
            return None
        
        po = PurchaseOrder.objects.create(
            opco=self.opco,
            vendor=self.winning_vendor,
            rfq=self.rfq,
            comparison=self,
            status='APPROVED',
            extra_data={'generated_from': self.comparison_number}
        )
        
        for q_line in self.winning_quotation.lines.all():
            PurchaseOrderLine.objects.create(
                po=po,
                material=q_line.material,
                quantity=q_line.quantity,
                unit_price=q_line.unit_price
            )
            
        self.status = 'PO_GENERATED'
        self.save()
        return po

    def __str__(self):
        return self.comparison_number


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة'),
        ('PENDING_APPROVAL', 'بانتظار الاعتماد'),
        ('APPROVED', 'معتمد'),
        ('PARTIAL_RECEIVED', 'استلام جزئي'),
        ('RECEIVED', 'تم الاستلام بالكامل'),
        ('CANCELLED', 'ملغى')
    ]
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    po_number = models.CharField(max_length=50, unique=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    pr = models.ForeignKey(PurchaseRequisition, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    rfq = models.ForeignKey(RequestForQuotation, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    comparison = models.ForeignKey(QuotationComparison, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_orders')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='DRAFT')
    
    extra_data = models.JSONField(default=dict, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.po_number:
            year = datetime.date.today().year
            last_po = PurchaseOrder.objects.filter(po_number__contains=f'PO-{year}').order_by('id').last()
            new_no = (int(last_po.po_number.split('-')[-1]) + 1) if last_po else 1
            self.po_number = f"PO-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return sum(line.quantity * line.unit_price for line in self.lines.all())

    def __str__(self):
        return self.po_number


    def receive_items(self, target_bin, items_data=None):
        """ 
        استلام البضاعة وزيادة رصيد المخزون في الرف المحدد.
        items_data format: [{'line_id': 1, 'qty': 10}, ...]
        """
        if self.status == 'RECEIVED': 
            return
        
        StockMove = apps.get_model('wms', 'StockMove')
        
        receipt = StockReceipt.objects.create(
            opco=self.opco,
            po=self
        )

        all_received = True
        
        for line in self.lines.all():
            qty_to_receive = line.remaining_quantity
            if items_data:
                item_spec = next((item for item in items_data if item.get('line_id') == line.id), None)
                if item_spec:
                    qty_to_receive = min(decimal.Decimal(str(item_spec.get('qty'))), line.remaining_quantity)

            if qty_to_receive > 0:
                StockMove.objects.create(
                    opco=self.opco,
                    material=line.material,
                    quantity=qty_to_receive,
                    move_type='IN',
                    dest_bin=target_bin,
                    source_bin=None,
                    vendor=self.vendor,
                    unit_cost=line.unit_price,
                    reference=f"PO: {self.po_number} (GRN: {receipt.receipt_number})"
                )
                
                StockReceiptLine.objects.create(
                    receipt=receipt,
                    material=line.material,
                    quantity=qty_to_receive,
                    storage_bin=target_bin
                )
                
                line.received_quantity += qty_to_receive
                line.save()

            if line.received_quantity < line.quantity:
                all_received = False

        self.status = 'RECEIVED' if all_received else 'PARTIAL_RECEIVED'
        self.save()


class PurchaseOrderLine(models.Model):
    po = models.ForeignKey(PurchaseOrder, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    received_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def remaining_quantity(self):
        return self.quantity - self.received_quantity

    def __str__(self):
        return f"{self.po.po_number} - {self.material.name}"


class StockReceipt(models.Model):
    """ مستند إيصال الاستلام (GRN) """
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='receipts', null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            year = datetime.date.today().year
            last_receipt = StockReceipt.objects.filter(receipt_number__contains=f'GRN-{year}').order_by('id').last()
            new_no = (int(last_receipt.receipt_number.split('-')[-1]) + 1) if last_receipt else 1
            self.receipt_number = f"GRN-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number


class StockReceiptLine(models.Model):
    """ تفاصيل الأصناف المستلمة في كل حركة """
    receipt = models.ForeignKey(StockReceipt, related_name='items', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    storage_bin = models.ForeignKey('wms.StorageBin', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.receipt.receipt_number} - {self.material.name}"


class PurchaseReturn(models.Model):
    """ مردودات مشتريات (Return To Vendor - RTV) """
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة'),
        ('APPROVED', 'معتمد للمرتجع'),
        ('COMPLETED', 'تم إرجاع البضاعة خصماً'),
        ('CANCELLED', 'ملغى')
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    return_number = models.CharField(max_length=50, unique=True, blank=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='returns')
    po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns')
    grn = models.ForeignKey(StockReceipt, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    reason = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.return_number:
            year = datetime.date.today().year
            last_ret = PurchaseReturn.objects.filter(return_number__contains=f'RTV-{year}').order_by('id').last()
            new_no = (int(last_ret.return_number.split('-')[-1]) + 1) if last_ret else 1
            self.return_number = f"RTV-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def process_return(self, storage_bin):
        """ تنفذ حركة الخروج المخزنية وتعديل حساب المورد """
        if self.status == 'COMPLETED':
            return
        
        StockMove = apps.get_model('wms', 'StockMove')
        total_ret = 0

        for line in self.lines.all():
            StockMove.objects.create(
                opco=self.opco,
                material=line.material,
                quantity=line.quantity,
                move_type='OUT',
                source_bin=storage_bin,
                dest_bin=None,
                vendor=self.vendor,
                unit_cost=line.unit_price,
                reference=f"RTV: {self.return_number}"
            )
            total_ret += line.quantity * line.unit_price

        self.total_amount = total_ret
        self.status = 'COMPLETED'
        self.save()
        
        # خصم مديونية / مستحقات المورد
        self.vendor.balance -= total_ret
        self.vendor.save()

    def __str__(self):
        return self.return_number


class PurchaseReturnLine(models.Model):
    return_doc = models.ForeignKey(PurchaseReturn, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.return_doc.return_number} - {self.material.name}"