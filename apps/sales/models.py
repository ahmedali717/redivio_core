from django.db import models, transaction
from django.apps import apps
import decimal

class Customer(models.Model):
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    def __str__(self): return f"{self.code} - {self.name}"

class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'), 
        ('CONFIRMED', 'Confirmed'), 
        ('SHIPPED', 'Shipped'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled')
    ]
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    so_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    notes = models.TextField(blank=True, null=True)

    def __str__(self): return self.so_number

    def calculate_totals(self):
        self.total_amount = sum(line.total for line in self.lines.all())
        self.tax_amount = (self.total_amount * decimal.Decimal('0.15')).quantize(decimal.Decimal('0.01'))
        self.grand_total = self.total_amount + self.tax_amount
        self.save()

    def deliver_items(self, source_bin):
        """ Robust delivery logic with invoice generation. """
        if self.status in ['DELIVERED', 'SHIPPED']:
            return
        
        StockMove = apps.get_model('wms', 'StockMove')
        StockQuant = apps.get_model('wms', 'StockQuant')

        with transaction.atomic():
            for line in self.lines.all():
                # التحقق من الرصيد في الرف المصدر
                quant = StockQuant.objects.filter(storage_bin=source_bin, material=line.material).first()
                if not quant or quant.quantity < line.quantity:
                    raise Exception(f"Insufficient stock for {line.material.name} in bin {source_bin.code}")

                # تسجيل الحركة
                StockMove.objects.create(
                    opco=self.opco,
                    material=line.material,
                    quantity=line.quantity,
                    move_type='OUT',
                    source_bin=source_bin,
                    dest_bin=None,
                    reference=f"SO: {self.so_number}"
                )
                # تحديث الكمية المشحونة
                line.shipped_quantity += line.quantity
                line.save()

            self.status = 'SHIPPED'
            self.save()
            
            # إنشاء فاتورة تلقائياً
            self.create_invoice()

    def create_invoice(self, delivery=None):
        """ 
        Creates a Sales Invoice. 
        If 'delivery' is provided, it bills only the items in that delivery.
        Otherwise, it bills all shipped items that haven't been invoiced yet.
        """
        import datetime
        invoice_number = f"INV-{self.so_number}-MAN"
        if delivery:
            invoice_number = f"INV-{delivery.delivery_number}"
        else:
            # إضافة ختم زمني للفاتورة اليدوية لضمان التفرد
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            invoice_number = f"INV-{self.so_number}-{timestamp}"
        
        # التأكد من عدم تكرار الفاتورة
        if SalesInvoice.objects.filter(invoice_number=invoice_number).exists():
            return
        
        total_amount = decimal.Decimal('0.00')
        lines_to_update = []

        if delivery:
            # حساب القيمة بناءً على ما تم صرفه فعلياً في هذا الإذن
            for item in delivery.items.all():
                so_line = self.lines.filter(material=item.material).first()
                if so_line:
                    qty_to_bill = item.quantity
                    total_amount += qty_to_bill * so_line.unit_price
                    so_line.billed_quantity += qty_to_bill
                    lines_to_update.append(so_line)
        else:
            # إصدار فاتورة يدوية بما تم صرفه ولم يُفوتر بعد
            for line in self.lines.all():
                unbilled_qty = line.shipped_quantity - line.billed_quantity
                if unbilled_qty > 0:
                    total_amount += unbilled_qty * line.unit_price
                    line.billed_quantity += unbilled_qty
                    lines_to_update.append(line)

        if total_amount <= 0:
            # لا يوجد شيء ليتم فوترته (إما لم يتم الصرف أو تم فوترة كل المنصرف)
            raise Exception("No shipped items available for invoicing.")

        tax_amount = (total_amount * decimal.Decimal('0.15')).quantize(decimal.Decimal('0.01'))
        grand_total = total_amount + tax_amount

        with transaction.atomic():
            SalesInvoice.objects.create(
                opco=self.opco,
                invoice_number=invoice_number,
                sales_order=self,
                customer=self.customer,
                due_date=datetime.date.today() + datetime.timedelta(days=30),
                total_amount=grand_total,
                status='UNPAID'
            )
            # تحديث الكميات المفوترة في سطور الأوردر
            for l in lines_to_update:
                l.save()

class SalesOrderLine(models.Model):
    so = models.ForeignKey(SalesOrder, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipped_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    billed_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def remaining_quantity(self):
        return self.quantity - self.shipped_quantity

    @property
    def unbilled_quantity(self):
        return self.shipped_quantity - self.billed_quantity

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class SalesInvoice(models.Model):
    STATUS_CHOICES = [('UNPAID', 'Unpaid'), ('PARTIAL', 'Partial'), ('PAID', 'Paid')]
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    due_date = models.DateField()
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')

    def __str__(self): return self.invoice_number

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            # زيادة مديونية العميل عند إصدار فاتورة جديدة
            self.customer.balance += self.total_amount
            self.customer.save()
        super().save(*args, **kwargs)

class CustomerPayment(models.Model):
    PAYMENT_METHODS = [('CASH', 'Cash'), ('BANK', 'Bank Transfer'), ('CHECK', 'Check')]
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    payment_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='CASH')
    reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self): return self.payment_number

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new:
            # تقليل مديونية العميل عند استلام دفعة
            self.customer.balance -= self.amount
            self.customer.save()
            
            # لو الدفعة مرتبطة بفاتورة، نحدث المبالغ في الفاتورة
            if self.invoice:
                self.invoice.paid_amount += self.amount
                if self.invoice.paid_amount >= self.invoice.total_amount:
                    self.invoice.status = 'PAID'
                elif self.invoice.paid_amount > 0:
                    self.invoice.status = 'PARTIAL'
                self.invoice.save()
                
        super().save(*args, **kwargs)

import datetime
class StockDelivery(models.Model):
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    delivery_number = models.CharField(max_length=50, unique=True, blank=True)
    so = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='deliveries')
    date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            year = datetime.date.today().year
            last_delivery = StockDelivery.objects.filter(delivery_number__contains=f'DN-{year}').order_by('id').last()
            if last_delivery:
                last_no = int(last_delivery.delivery_number.split('-')[-1])
                new_no = last_no + 1
            else:
                new_no = 1
            self.delivery_number = f"DN-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def __str__(self): return self.delivery_number

class StockDeliveryLine(models.Model):
    delivery = models.ForeignKey(StockDelivery, related_name='items', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    storage_bin = models.ForeignKey('wms.StorageBin', on_delete=models.CASCADE)

    def __str__(self): return f"{self.delivery.delivery_number} - {self.material.name}"