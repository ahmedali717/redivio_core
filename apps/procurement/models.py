from django.db import models
from django.apps import apps  # ✅ ضروري لاستدعاء الموديلات داخل الدوال

class Vendor(models.Model):
    # ربط نصي لتجنب المشاكل
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    extra_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.name

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [('DRAFT', 'Draft'), ('CONFIRMED', 'Confirmed'), ('RECEIVED', 'Received'), ('CANCELLED', 'Cancelled')]
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    po_number = models.CharField(max_length=50, unique=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.po_number

    def receive_items(self, target_bin):
        """ 
        منطق استلام البضاعة وزيادة المخزون.
        يستخدم apps.get_model لمنع مشاكل الـ Circular Import.
        """
        if self.status == 'RECEIVED': return
        
        # ✅ استدعاء الموديلات ديناميكياً (Lazy Loading)
        StockQuant = apps.get_model('wms', 'StockQuant')
        StockMove = apps.get_model('wms', 'StockMove')
        
        for line in self.lines.all():
            # 1. تحديث/إنشاء رصيد (Quant)
            # نستخدم target_bin.location.plant للوصول للمخزن
            quant, created = StockQuant.objects.get_or_create(
                opco=self.opco,
                plant=target_bin.location.plant,
                storage_bin=target_bin, 
                material=line.material,
                defaults={'quantity': 0}
            )
            quant.quantity += line.quantity
            quant.save()

            # 2. تسجيل الحركة (Move)
            # لاحظ: قمنا بتحديث أسماء الحقول لتطابق موديل WMS الجديد
            StockMove.objects.create(
                opco=self.opco,
                material=line.material,
                quantity=line.quantity,
                move_type='IN',  # أو 'Receipt' حسب الـ choices في WMS
                dest_bin=target_bin, # استخدمنا dest_bin بدلاً من dest_loc
                source_bin=None,     # لا يوجد مصدر محدد (لأنها من مورد خارجي)
                reference=f"PO: {self.po_number}"
            )
        
        self.status = 'RECEIVED'
        self.save()

class PurchaseOrderLine(models.Model):
    po = models.ForeignKey(PurchaseOrder, related_name='lines', on_delete=models.CASCADE)
    # ربط نصي بـ item_master
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.po.po_number} - {self.material}"