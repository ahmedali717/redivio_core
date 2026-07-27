from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import TenantBaseModel

# 1. فئات الأصناف (Category)
class Category(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # استراتيجية الـ Putaway الافتراضية للفئة (مثل أودو)
    PUTAWAY_STRATEGIES = [
        ('fixed', 'Fixed Bin (الرف الثابت)'),
        ('closest', 'Closest Location (الأقرب)'),
        ('fifo', 'FIFO (الأقدم أولاً)'),
    ]
    default_putaway_strategy = models.CharField(max_length=20, choices=PUTAWAY_STRATEGIES, default='fixed')

    def __str__(self):
        return self.name

# 1.5. المجموعات البيعية (Sale Groups - POS Categories)
class SaleGroup(TenantBaseModel):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='sale_groups/', null=True, blank=True)
    color = models.CharField(max_length=20, default='#6366f1') # Default indigo

    def __str__(self):
        return self.name

# 2. الموديل الأساسي للصنف (Material / Product)
class Material(TenantBaseModel):
    # البيانات الأساسية
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    # 🚀 Item 11: إضافة حقل الوصف
    description = models.TextField(blank=True, null=True, verbose_name="وصف الصنف")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    sale_group = models.ForeignKey(SaleGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    base_uom = models.CharField(max_length=50, default='PCS')
    # 🚀 Item 09: إضافة وحدة القياس البديلة ونسبة التحويل (AUOM & Transformation Ratio)
    alternate_uom = models.CharField(max_length=50, blank=True, null=True, verbose_name="وحدة القياس البديلة")
    uom_conversion_factor = models.DecimalField(max_digits=12, decimal_places=4, default=1.0, verbose_name="نسبة التحويل (معكوس أو معامل الضرب)")
    
    # 🚀 Item 10: حقل التفعيل والتعطيل للصنف
    is_active = models.BooleanField(default=True, verbose_name="نشط؟", help_text="تعطيل الصنف يمنع أي معاملات مخزنية أو بيعية عليه")
    
    barcode = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to='materials/', null=True, blank=True)
    
    # --- 🚀 حقول الـ Advanced Mode (Odoo 19 Style) ---
    TRACKING_CHOICES = [
        ('none', 'No Tracking (بدون تتبع)'),
        ('serial', 'By Unique Serial (سيريال رقمي)'),
        ('lot', 'By Lots/Batch (رقم التشغيلة)'),
    ]
    tracking = models.CharField(max_length=10, choices=TRACKING_CHOICES, default='none')

    standard_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="سعر البيع للجمهور")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=15.00, help_text="نسبة ضريبة القيمة المضافة")
    
    # القياسات والأوزان (للحسابات المتقدمة في الشحن والتخزين)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    volume = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # حدود المخزون الذكية
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # --- 🍽️ Restaurant POS Extensions ---
    is_pos_item = models.BooleanField(default=False, help_text="هل هذا الصنف متاح في قائمة البيع للمطعم؟")
    is_combo = models.BooleanField(default=False, help_text="هل هذا الصنف عبارة عن عرض (Combo)؟")
    expiry_date = models.DateField(null=True, blank=True, help_text="تاريخ انتهاء الصلاحية لهذا الصنف (اختياري)")
    allowed_terminals = models.ManyToManyField(
        'restaurant_pos.POSTerminal',
        blank=True,
        related_name='materials',
        help_text='نقاط البيع المسموح بظهور هذا الصنف فيها'
    )
    
    # التزامن مع القابضة
    is_template = models.BooleanField(default=False) # هل هذا صنف مرجعي للقابضة؟
    
    # --- 👕 Product Variants ---
    has_variants = models.BooleanField(default=False, help_text="هل هذا الصنف له متغيرات (مثل الألوان أو المقاسات)؟")
    parent_template = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='variants', help_text="إذا كان هذا متغيراً، فمن هو الصنف الأب؟")
    variant_name = models.CharField(max_length=100, null=True, blank=True, help_text="اسم المتغير مثل (أحمر - كبير)")
    
    class Meta:
        unique_together = ('opco', 'sku') # SKU فريد لكل شركة

    def __str__(self):
        if self.parent_template and self.variant_name:
            return f"[{self.sku}] {self.name} - {self.variant_name}"
        return f"[{self.sku}] {self.name}"

    @property
    def total_on_hand(self):
        """حساب إجمالي الأرصدة في كل الرفوف الخاصة بهذا الصنف في هذه الشركة"""
        from django.db.models import Sum
        from apps.wms.models import StockQuant
        total = StockQuant.objects.filter(material=self, opco=self.opco).aggregate(Sum('quantity'))['quantity__sum']
        return total or 0

# 🚀 Item 17: أسعار الصنف المحددة لكل مصنع على حدة (Plant-level Pricing)
class MaterialPlantPrice(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='plant_prices')
    plant = models.ForeignKey('wms.Plant', on_delete=models.CASCADE, related_name='material_prices')
    standard_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="تلفة المصنع")
    sales_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="سعر بيع المصنع")

    class Meta:
        unique_together = ('material', 'plant')

    def __str__(self):
        return f"{self.material.name} @ {self.plant.name}: {self.sales_price}"

# 2.5. مكونات الـ Combo (Combo Items)
class ComboItem(models.Model):
    parent_material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='combo_items')
    item = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='included_in_combos')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="سعر إضافي عند اختيار هذا الصنف في العرض")

    def __str__(self):
        return f"{self.quantity} x {self.item.name} in {self.parent_material.name}"

# 3. 🛡️ محرك قواعد التوجيه (Putaway Rules / MaterialLocation)
class MaterialLocation(models.Model):
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='material_bins')
    # 🚀 التعديل الأخير: دي رجعت wms.StorageBin لأن الرفوف موجودة في تطبيق المخازن
    storage_bin = models.ForeignKey('wms.StorageBin', on_delete=models.CASCADE)
    
    # منطق الأولوية (Sequence)
    sequence = models.PositiveIntegerField(default=10)
    
    # هل هذا هو الرف الرئيسي (النجمة)؟
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ['sequence'] # الترتيب التلقائي حسب الأولوية
        unique_together = ('material', 'storage_bin')

    def clean(self):
        """ منع ربط صنف برف يتبع شركة أخرى أو أكثر من رف لنفس المصنع """
        bin_opco = self.storage_bin.plant.opco
        if self.material.opco != bin_opco:
            raise ValidationError(f"خطأ: الرف {self.storage_bin.code} يتبع شركة {bin_opco.name} وليس شركة الصنف!")
        
        # 🚀 Item 13: حظر ربط الصنف بأكثر من رف في نفس المصنع
        existing_in_plant = MaterialLocation.objects.filter(
            material=self.material, 
            storage_bin__plant=self.storage_bin.plant
        )
        if self.pk:
            existing_in_plant = existing_in_plant.exclude(pk=self.pk)
        if existing_in_plant.exists():
            raise ValidationError(f"خطأ: الصنف مرتبط بالفعل براد/رف آخر في المصنع ({self.storage_bin.plant.name}). لا يمكن تعيين أكثر من رف لنفس الصنف داخل نفس المصنع.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)