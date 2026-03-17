import datetime
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
    
    extra_data = models.JSONField(default=dict, blank=True, null=True)
    
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
    
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def remaining_quantity(self):
        return self.quantity - self.received_quantity

    def __str__(self):
        return f"{self.po.po_number} - {self.material}"
    
    def __str__(self):
        return f"{self.po.po_number} - {self.material}"
    
class StockReceipt(models.Model):
    """ مستند إيصال الاستلام (GRN) """
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    # رقم مسلسل تلقائي GRN-2026-0001
    receipt_number = models.CharField(max_length=50, unique=True, blank=True)
    po = models.ForeignKey('PurchaseOrder', on_delete=models.CASCADE, related_name='receipts')
    date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            year = datetime.date.today().year
            # البحث عن آخر رقم مسلسل لهذا العام
            last_receipt = StockReceipt.objects.filter(receipt_number__contains=f'GRN-{year}').order_by('id').last()
            if last_receipt:
                # استخراج الرقم الأخير وزيادته
                last_no = int(last_receipt.receipt_number.split('-')[-1])
                new_no = last_no + 1
            else:
                new_no = 1
            self.receipt_number = f"GRN-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number

class StockReceiptLine(models.Model):
    """ تفاصيل الأصناف المستلمة في كل حركة """
    receipt = models.ForeignKey(StockReceipt, related_name='items', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2) # الكمية المستلمة "الآن"
    # الرف الذي تم التخزين فيه
    storage_bin = models.ForeignKey('wms.StorageBin', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.receipt.receipt_number} - {self.material.name}"