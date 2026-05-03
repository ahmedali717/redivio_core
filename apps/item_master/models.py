from django.db import models
from django.core.exceptions import ValidationError

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

# 2. الموديل الأساسي للصنف (Material / Product)
class Material(models.Model):
    # ✅ تفضل core.OpCo لأن تطبيق core هو اللي فيه الشركة
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='materials')
    
    # البيانات الأساسية
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    base_uom = models.CharField(max_length=50, default='PCS')
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
    
    # القياسات والأوزان (للحسابات المتقدمة في الشحن والتخزين)
    weight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    volume = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # حدود المخزون الذكية
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # --- 🍽️ Restaurant POS Extensions ---
    is_pos_item = models.BooleanField(default=False, help_text="هل هذا الصنف متاح في قائمة البيع للمطعم؟")
    expiry_date = models.DateField(null=True, blank=True, help_text="تاريخ انتهاء الصلاحية لهذا الصنف (اختياري)")
    
    # التزامن مع القابضة
    is_template = models.BooleanField(default=False) # هل هذا صنف مرجعي للقابضة؟
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    
    class Meta:
        unique_together = ('opco', 'sku') # SKU فريد لكل شركة

    def __str__(self):
        return f"[{self.sku}] {self.name}"

    @property
    def total_on_hand(self):
        """حساب إجمالي الأرصدة في كل الرفوف الخاصة بهذا الصنف في هذه الشركة"""
        from django.db.models import Sum
        from apps.wms.models import StockQuant
        total = StockQuant.objects.filter(material=self, opco=self.opco).aggregate(Sum('quantity'))['quantity__sum']
        return total or 0

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
        """ منع ربط صنف برف يتبع شركة أخرى """
        bin_opco = self.storage_bin.storage_location.plant.opco
        if self.material.opco != bin_opco:
            raise ValidationError(f"خطأ: الرف {self.storage_bin.code} يتبع شركة {bin_opco.name} وليس شركة الصنف!")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)