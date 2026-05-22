from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from .context import get_current_tenant_id  # تأكد من إنشاء ملف context.py في نفس المجلد

# --- 1. الـ Manager المسؤول عن الفلترة التلقائية (Odoo Style) ---
class TenantManager(models.Manager):
    """
    Manager مخصص يضيف فلترة تلقائية بناءً على الشركة النشطة في السياق الحالي.
    """
    def get_queryset(self):
        tenant_id = get_current_tenant_id()
        queryset = super().get_queryset()
        
        # إذا كان هناك شركة نشطة، يتم الفلترة بناءً عليها تلقائياً
        # ملاحظة: يتم تطبيق هذا على الموديلات التي ترث من TenantBaseModel فقط
        if tenant_id:
            return queryset.filter(opco_id=tenant_id)
        return queryset

# --- 2. كود OpCo (يجب أن يكون أول كلاس موديل لكي تراه بقية الجداول) ---
class OpCo(models.Model):
    """
    الشركة المشغلة (Tenant / Workspace)
    تدعم نظام الشركات القابضة (Holding) والشركات التابعة (Subsidiaries)
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_companies"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    # الهيكل الهرمي
    parent = models.ForeignKey(
        'self', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True, 
        related_name="subsidiaries",
        verbose_name="الشركة الأم"
    )
    
    is_holding = models.BooleanField(
        default=False, 
        verbose_name="شركة قابضة؟",
        help_text="حدد هذا الخيار إذا كانت هذه الشركة تمتلك شركات أخرى تحتها"
    )

    is_system_root = models.BooleanField(
        default=False, 
        verbose_name="شركة أساسية للنظام"
    )

    plan = models.CharField(
        max_length=20,
        choices=[
            ("starter", "Starter"),
            ("business", "Business"),
            ("professional", "Professional"),
            ("enterprise", "Enterprise"),
            ("free", "Free"),
            ("pro", "Pro"),
        ],
        default="starter"
    )

    region = models.CharField(max_length=50, default="global")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    currency = models.CharField(max_length=3, default="USD")
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="الرقم الضريبي")
    cr_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="السجل التجاري")
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, verbose_name="شعار الشركة")
    brand_color = models.CharField(max_length=20, default="#6366f1", verbose_name="لون العلامة التجارية")

    # ✅ بيانات المشترك الأساسية (SaaS Data)
    contact_name = models.CharField(max_length=150, blank=True, null=True, verbose_name="اسم المشترك")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الهاتف")
    industry = models.CharField(max_length=100, blank=True, null=True, verbose_name="النشاط")
    database_name = models.CharField(max_length=50, blank=True, null=True, verbose_name="اسم قاعدة البيانات", unique=True)
    
    # ✅ إعدادات الرخصة ونوع النظام (License & Architecture)
    system_mode = models.CharField(
        max_length=20,
        choices=[("standalone", "Stand Alone"), ("modular", "Full Package")],
        default="modular",
        verbose_name="نوع النظام"
    )
    purchased_modules = models.JSONField(default=list, blank=True, verbose_name="الموديولات المشتراة")

    # ✅ المانيجرز:objects العادي لا يفلتر لكي يرى السيرفر كل الشركات في الهيدر
    objects = models.Manager() 
    all_objects = models.Manager() 

    class Meta:
        verbose_name = "شركة مشغلة"
        verbose_name_plural = "الشركات المشغلة"

    def clean(self):
        if self.parent and self.pk == self.parent.pk:
            raise ValidationError("لا يمكن للشركة أن تكون تابعة لنفسها.")

    def delete(self, *args, **kwargs):
        if self.is_system_root:
            raise ValidationError("أمان: لا يمكن حذف الشركة الأساسية المسجلة للنظام.")
        super().delete(*args, **kwargs)

    def __str__(self):
        label = f"{self.name} ({self.code})"
        if self.is_holding:
            label = f"🏢 {label}"
        elif self.parent:
            label = f"↳ {label}"
        return label

# --- 3. تحديث TenantBaseModel (يعتمد على OpCo المعرف أعلاه) ---
class TenantBaseModel(models.Model):
    """
    موديل تجريدي ترث منه الجداول التي تحتاج للعزل (مثل Plants, Materials, Bins)
    """
    opco = models.ForeignKey(
        OpCo, 
        on_delete=models.CASCADE,
        related_name="%(class)s_records"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ استخدام TenantManager لضمان الفلترة التلقائية في الجداول التشغيلية
    objects = TenantManager() 
    all_objects = models.Manager() 

    class Meta:
        abstract = True

# --- 4. كود CompanyUser ---
class CompanyUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="company_assignments")
    company = models.ForeignKey(OpCo, on_delete=models.CASCADE)
    ROLE_CHOICES = [
        ('admin', 'Admin (كل الصلاحيات)'),
        ('cashier', 'Cashier (الكاشير)'),
        ('kitchen', 'Kitchen (المطبخ)'),
        ('warehouse', 'Warehouse (المخازن والتكاليف)'),
        ('manager', 'Manager (الإدارة والتقارير)'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    is_active_session = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'company')
        verbose_name = "موظف في شركة"

class PutawayRule(models.Model):
    # نربط بـ item_master.Material بدلاً من Item
    item = models.ForeignKey('item_master.Material', on_delete=models.CASCADE)
    
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    
    # نربط بـ wms.StorageBin بدلاً من WarehouseBin
    default_bin = models.ForeignKey('wms.StorageBin', on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ('item', 'opco')

    def __str__(self):
        return f"{self.item.name} -> {self.default_bin.code}"