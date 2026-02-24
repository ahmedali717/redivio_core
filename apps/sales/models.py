from django.db import models
from django.apps import apps # ✅ ضروري لاستدعاء الموديلات ديناميكياً

class Customer(models.Model):
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    
    def __str__(self): return self.name

class SalesOrder(models.Model):
    STATUS_CHOICES = [('DRAFT', 'Draft'), ('CONFIRMED', 'Confirmed'), ('DELIVERED', 'Delivered')]
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    so_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self): return self.so_number

    def deliver_items(self, source_bin):
        """ 
        منطق صرف البضاعة وخصم المخزون.
        """
        if self.status == 'DELIVERED': return
        
        # ✅ استدعاء الموديلات ديناميكياً
        StockQuant = apps.get_model('wms', 'StockQuant')
        StockMove = apps.get_model('wms', 'StockMove')
        
        for line in self.lines.all():
            # ✅ تصحيح 1: استخدام storage_bin بدلاً من bin
            quant = StockQuant.objects.filter(storage_bin=source_bin, material=line.material).first()
            
            # حساب الكمية الجديدة
            current_qty = quant.quantity if quant else 0
            new_qty = current_qty - line.quantity
            
            if quant:
                quant.quantity = new_qty
                quant.save()
            else:
                # ✅ تصحيح 2: استخدام الحقول الصحيحة للموديل (storage_bin فقط)
                StockQuant.objects.create(
                    opco=self.opco,
                    plant=source_bin.storage_location.plant, # الوصول للمصنع عبر العلاقات
                    storage_bin=source_bin,                  # الحقل الصحيح
                    material=line.material,
                    quantity= -line.quantity
                )

            # تسجيل الحركة (Move)
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