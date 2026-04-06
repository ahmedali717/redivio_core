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
                quant.quantity -= line.quantity
                quant.save()
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