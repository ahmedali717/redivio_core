from django.db import models

# ❌ لا تضع أي import هنا من apps.core أو apps.item_master
# سنعتمد على الإشارة النصية (String References) لمنع الأخطاء

class Plant(models.Model):
    # ربطنا هنا بـ 'core.OpCo' نصياً
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='plants')
    code = models.CharField(max_length=5) 
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=3, default='WH')
    
    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if StockQuant.objects.filter(plant=self, quantity__gt=0).exists():
            raise ValidationError("لا يمكن حذف المصنع نظراً لوجود رصيد مخزني متبقي فيه.")
        if StockMove.objects.filter(models.Q(source_bin__plant=self) | models.Q(dest_bin__plant=self)).exists():
            raise ValidationError("لا يمكن حذف المصنع نظراً لوجود حركات مخزنية وتكاليف مرتبطة به.")
        super().delete(*args, **kwargs)

    def __str__(self): return self.name

    class Meta:
        unique_together = (('opco', 'code'), ('opco', 'name'))

class StorageLocation(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='locations') 
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    extra_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self): return f"{self.plant.code} - {self.code}"

    class Meta:
        unique_together = (('plant', 'code'), ('plant', 'name'))

class StorageBin(models.Model):
    # ✅ تعديل 1: تغيير الاسم إلى plant ليتطابق مع الـ Serializer والـ Frontend
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='bins')
    
    # ✅ تعديل 2: استخدام code بسيط بدلاً من rack/shelf/cell (لأن المودال الحالي يرسل code فقط)
    code = models.CharField(max_length=20)
    
    # يمكنك إعادة rack/shelf لاحقاً إذا طورت الواجهة الأمامية لتدعمها
    is_active = models.BooleanField(default=True)
    
    def __str__(self): return f"{self.plant.code} - {self.code}"

    class Meta:
        # هذا السطر يضمن عدم تكرار الكود على مستوى قاعدة البيانات
        unique_together = ('code', 'plant')

class StockQuant(models.Model):
    # ربطنا هنا بـ 'core.OpCo' نصياً
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE)
    
    # ✅ هنا الاسم storage_bin صحيح ومتوافق
    storage_bin = models.ForeignKey(StorageBin, on_delete=models.PROTECT)
    
    # ربطنا هنا بـ 'item_master.Material' نصياً
    material = models.ForeignKey('item_master.Material', on_delete=models.PROTECT)
    
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta: 
        unique_together = ('storage_bin', 'material')

class StockMove(models.Model):
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.PROTECT)
    source_bin = models.ForeignKey(StorageBin, related_name='out_moves', null=True, blank=True, on_delete=models.SET_NULL)
    dest_bin = models.ForeignKey(StorageBin, related_name='in_moves', null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100)
    move_type = models.CharField(max_length=10, choices=[('IN', 'In'), ('OUT', 'Out')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # أضف الحقول دي عشان السيريالايزر يشتغل صح
    vendor = models.ForeignKey('procurement.Vendor', on_delete=models.SET_NULL, null=True, blank=True)
    customer = models.ForeignKey('sales.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    vendor_name = models.CharField(max_length=200, null=True, blank=True)
    payment_term = models.CharField(max_length=50, default="CASH")
    payment_method = models.CharField(max_length=50, default="CASH") # 🚀 طريقة الدفع/التحصيل
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0) # سعر الشراء
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, default=0) # سعر البيع
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15) # 🚀 معدل الضريبة
    receipt_type = models.CharField(max_length=50, null=True, blank=True)

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        is_new = self.pk is None
        if is_new and self.opco.is_inventory_active:
            raise ValidationError("لا يمكن إجراء حركات مخزنية أثناء عملية الجرد النشطة.")
        
        # 🚀 Item 10: حظر الحركة للأصناف غير النشطة
        if self.material and not getattr(self.material, 'is_active', True):
            raise ValidationError(f"الصنف [{self.material.sku}] معطل وغير متاح للتعاملات المخزنية.")
            
        # 🚀 Item 14: حظر الحركة للرفوف غير النشطة
        if self.source_bin and not self.source_bin.is_active:
            raise ValidationError(f"الرف المصدر ({self.source_bin.code}) معطل وغير متاح للحركة.")
        if self.dest_bin and not self.dest_bin.is_active:
            raise ValidationError(f"الرف الهدف ({self.dest_bin.code}) معطل وغير متاح للحركة.")
            
        super().save(*args, **kwargs)
        
        if is_new:
            # تحديث الأرصدة عند الحركات الجديدة
            if self.dest_bin: # removed extra checks for simplicity, assuming integrity
                # ملاحظة: يجب التأكد أن dest_bin مرتبط بـ location و plant
                # لكن للكود الحالي، سنبسطه:
                 plant_obj = self.dest_bin.plant
                 q, _ = StockQuant.objects.get_or_create(
                    opco=self.opco, plant=plant_obj, 
                    storage_bin=self.dest_bin, material=self.material
                )
                 q.quantity += self.quantity
                 q.save()
            
            if self.source_bin:
                plant_obj = self.source_bin.plant
                q, _ = StockQuant.objects.get_or_create(
                    opco=self.opco, plant=plant_obj, 
                    storage_bin=self.source_bin, material=self.material
                )
                q.quantity -= self.quantity
                q.save()

import datetime
from django.conf import settings

class WarehouseTransfer(models.Model):
    """ أمر نقل / تحويل مخزني بين الفروع والرفوف (TO - Warehouse Transfer) """
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة'),
        ('APPROVED', 'معتمد'),
        ('DISPATCHED', 'تم الصرف من المصدر (قيد النقل)'),
        ('RECEIVED', 'تم الاستلام في الهدف'),
        ('CANCELLED', 'ملغى')
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    transfer_number = models.CharField(max_length=50, unique=True, blank=True)
    source_bin = models.ForeignKey(StorageBin, related_name='outgoing_transfers', on_delete=models.CASCADE)
    dest_bin = models.ForeignKey(StorageBin, related_name='incoming_transfers', on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_transfers')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_transfers')

    def save(self, *args, **kwargs):
        if not self.transfer_number:
            year = datetime.date.today().year
            last_tr = WarehouseTransfer.objects.filter(transfer_number__contains=f'TO-{year}').order_by('id').last()
            new_no = (int(last_tr.transfer_number.split('-')[-1]) + 1) if last_tr else 1
            self.transfer_number = f"TO-{year}-{new_no:04d}"
        super().save(*args, **kwargs)

    def execute_transfer(self):
        """ تنفذ حركتي الصرف والاستلام تلقائياً """
        if self.status == 'RECEIVED':
            return
        
        for line in self.lines.all():
            StockMove.objects.create(
                opco=self.opco,
                material=line.material,
                source_bin=self.source_bin,
                dest_bin=self.dest_bin,
                quantity=line.quantity,
                move_type='OUT',
                reference=f"TRANSFER: {self.transfer_number}"
            )
            
        self.status = 'RECEIVED'
        self.save()

    def __str__(self):
        return f"{self.transfer_number}: {self.source_bin.code} -> {self.dest_bin.code}"


class WarehouseTransferLine(models.Model):
    transfer = models.ForeignKey(WarehouseTransfer, related_name='lines', on_delete=models.CASCADE)
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.material.name}"


class StockScrap(models.Model):
    """ إتلاف مخزني وتصفية أصناف تالفة/مفقودة (Scrap / Inventory Write-off) """
    REASON_CHOICES = [
        ('EXPIRED', 'منتهي الصلاحية'),
        ('DAMAGED', 'تالف / كسر'),
        ('LOST', 'عجز / مفقود'),
        ('SCRAP', 'هالك عام'),
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    scrap_number = models.CharField(max_length=50, unique=True, blank=True)
    storage_bin = models.ForeignKey(StorageBin, on_delete=models.CASCADE, related_name='scraps')
    material = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default='DAMAGED')
    notes = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.scrap_number:
            year = datetime.date.today().year
            last_sc = StockScrap.objects.filter(scrap_number__contains=f'SCRAP-{year}').order_by('id').last()
            new_no = (int(last_sc.scrap_number.split('-')[-1]) + 1) if last_sc else 1
            self.scrap_number = f"SCRAP-{year}-{new_no:04d}"
        
        self.total_cost = self.quantity * self.unit_cost
        super().save(*args, **kwargs)

        if is_new:
            StockMove.objects.create(
                opco=self.opco,
                material=self.material,
                source_bin=self.storage_bin,
                dest_bin=None,
                quantity=self.quantity,
                move_type='OUT',
                unit_cost=self.unit_cost,
                reference=f"SCRAP: {self.scrap_number} ({self.get_reason_display()})"
            )

    def __str__(self):
        return f"{self.scrap_number} - {self.material.name}"