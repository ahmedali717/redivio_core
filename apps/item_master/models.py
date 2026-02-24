from django.db import models

# 1. الحقول المخصصة (يجب أن يكون في البداية)
class FieldDefinition(models.Model):
    TARGET_MODELS = [
        ('material', 'Material'), 
        ('vendor', 'Vendor'), 
        ('po', 'PO'), 
        ('location', 'Location')
    ]
    FIELD_TYPES = [
        ('text', 'Text'), 
        ('number', 'Number'), 
        ('date', 'Date'), 
        ('bool', 'Checkbox'), 
        ('select', 'Select')
    ]
    
    target_model = models.CharField(max_length=20, choices=TARGET_MODELS)
    name = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='text')
    is_active = models.BooleanField(default=False)
    options = models.JSONField(default=list, blank=True)
    
    class Meta: 
        unique_together = ('target_model', 'name')
    
    def __str__(self): 
        return f"{self.target_model} -> {self.label}"

# 2. فئات الأصناف
class Category(models.Model):
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self): 
        return self.name

# 3. الأصناف الرئيسية
class Material(models.Model):
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='materials')
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    base_uom = models.CharField(max_length=10, default='PCS')
    barcode = models.CharField(max_length=100, unique=True, null=True, blank=True)
    image = models.ImageField(upload_to='materials/', null=True, blank=True) # أضف هذا السطر
    # ربط المواقع المتعددة
    storage_locations = models.ManyToManyField(
        'wms.StorageBin', 
        through='MaterialLocation', 
        related_name='materials'
    )
    
    extra_data = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('opco', 'sku')

    def __str__(self): 
        return f"[{self.sku}] {self.name}"

# 4. الجدول الوسيط لمواقع التخزين
class MaterialLocation(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='material_bins')
    storage_bin = models.ForeignKey('wms.StorageBin', on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        unique_together = ('material', 'storage_bin')