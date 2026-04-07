from django.db import models
from django.apps import apps # ✅ ضروري لاستدعاء الموديلات ديناميكياً

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
        self.tax_amount = self.total_amount * models.Decimal('0.15') # Example 15% VAT
        self.grand_total = self.total_amount + self.tax_amount
        self.save()

    def deliver_items(self, source_bin):
        if self.status in ['DELIVERED', 'SHIPPED']: return
        
        StockQuant = apps.get_model('wms', 'StockQuant')
        StockMove = apps.get_model('wms', 'StockMove')
        
        for line in self.lines.all():
            quant = StockQuant.objects.filter(storage_bin=source_bin, material=line.material).first()
            
            if quant:
                # لا نطرح من الرصيد يدوياً لأن حركة المخزون ستقوم بذلك
                pass
            else:
                StockQuant.objects.create(
                    opco=self.opco,
                    plant=source_bin.storage_location.plant,
                    storage_bin=source_bin,
                    material=line.material,
                    quantity= -line.quantity
                )

            StockMove.objects.create(
                opco=self.opco,
                material=line.material,
                quantity=line.quantity,
                move_type='OUT', 
                source_bin=source_bin,
                dest_bin=None,
                reference=f"SO: {self.so_number}"
            )
            
        self.status = 'DELIVERED'
        self.save()

class SalesOrderLine(models.Model):
    so = models.ForeignKey(SalesOrder, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    delivered_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def remaining_quantity(self):
        return self.quantity - self.delivered_quantity

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

import datetime
class StockDelivery(models.Model):
    """ إذن صرف للصنف (Delivery Note) """
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

    def __str__(self):
        return self.delivery_number

class StockDeliveryLine(models.Model):
    """ تفاصيل الأصناف المصروفة في كل إذن """
    delivery = models.ForeignKey(StockDelivery, related_name='items', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    storage_bin = models.ForeignKey('wms.StorageBin', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.delivery.delivery_number} - {self.material.name}"