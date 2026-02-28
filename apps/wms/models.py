from django.db import models

# ❌ لا تضع أي import هنا من apps.core أو apps.item_master
# سنعتمد على الإشارة النصية (String References) لمنع الأخطاء

class Plant(models.Model):
    # ربطنا هنا بـ 'core.OpCo' نصياً
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='plants')
    code = models.CharField(max_length=5) 
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=3, default='WH')
    
    def __str__(self): return self.name

class StorageLocation(models.Model):
    plant = models.ForeignKey(Plant, on_delete=models.CASCADE, related_name='locations') 
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    extra_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self): return f"{self.plant.code} - {self.code}"

class StorageBin(models.Model):
    # ✅ تعديل 1: تغيير الاسم إلى storage_location ليتطابق مع الـ Serializer والـ Frontend
    storage_location = models.ForeignKey(StorageLocation, on_delete=models.CASCADE, related_name='bins')
    
    # ✅ تعديل 2: استخدام code بسيط بدلاً من rack/shelf/cell (لأن المودال الحالي يرسل code فقط)
    code = models.CharField(max_length=20)
    
    # يمكنك إعادة rack/shelf لاحقاً إذا طورت الواجهة الأمامية لتدعمها
    is_active = models.BooleanField(default=True)
    
    def __str__(self): return self.code

    class Meta:
        # هذا السطر يضمن عدم تكرار الكود على مستوى قاعدة البيانات
        # إذا كنت تريد التميز على مستوى الشركة، يفضل دمج كود الشركة مع كود الرف
        unique_together = ('code', 'storage_location')

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
    date = models.DateTimeField(auto_now_add=True)
    move_type = models.CharField(max_length=10, choices=[('IN', 'In'), ('OUT', 'Out')])
    
    # أضف الحقول دي عشان السيريالايزر يشتغل صح
    vendor_name = models.CharField(max_length=200, null=True, blank=True)
    payment_term = models.CharField(max_length=50, default="CASH")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    receipt_type = models.CharField(max_length=50, null=True, blank=True) # اللي كان عامل المشكلة

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # تحديث الأرصدة عند الحركات الجديدة
            if self.dest_bin: # removed extra checks for simplicity, assuming integrity
                # ملاحظة: يجب التأكد أن dest_bin مرتبط بـ location و plant
                # لكن للكود الحالي، سنبسطه:
                 plant_obj = self.dest_bin.storage_location.plant
                 q, _ = StockQuant.objects.get_or_create(
                    opco=self.opco, plant=plant_obj, 
                    storage_bin=self.dest_bin, material=self.material
                )
                 q.quantity += self.quantity
                 q.save()
            
            if self.source_bin:
                plant_obj = self.source_bin.storage_location.plant
                q, _ = StockQuant.objects.get_or_create(
                    opco=self.opco, plant=plant_obj, 
                    storage_bin=self.source_bin, material=self.material
                )
                q.quantity -= self.quantity
                q.save()