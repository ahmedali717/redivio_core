from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class OpCo(models.Model):
    """
    الشركة المشغلة (Tenant / Workspace)
    تم التحديث لدعم نظام الشركات القابضة (Holding) والشركات التابعة (Subsidiaries)
    مع إضافة حماية أمان للشركة الأساسية.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_companies"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    # --- إضافات الهيكل الهرمي (Holding & Subsidiaries) ---
    parent = models.ForeignKey(
        'self', 
        on_delete=models.PROTECT,  # يمنع حذف الشركة الأم إذا كان لها شركات تابعة
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
        editable=False,  # لا تظهر في النماذج العادية لحمايتها
        verbose_name="شركة أساسية للنظام"
    )
    # --------------------------------------------------

    plan = models.CharField(
        max_length=20,
        choices=[
            ("free", "Free"),
            ("pro", "Pro"),
            ("enterprise", "Enterprise"),
        ],
        default="free"
    )

    region = models.CharField(max_length=50, default="global")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    currency = models.CharField(max_length=3, default="USD")
    tax_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="الرقم الضريبي")
    cr_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="السجل التجاري")
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True, verbose_name="شعار الشركة")

    class Meta:
        verbose_name = "شركة مشغلة"
        verbose_name_plural = "الشركات المشغلة"

    def clean(self):
        # التحقق من أن الشركة لا تتبع نفسها لتجنب الحلقات اللانهائية
        if self.parent and self.pk == self.parent.pk:
            raise ValidationError("لا يمكن للشركة أن تكون تابعة لنفسها.")

    def delete(self, *args, **kwargs):
        # منع حذف الشركة الأساسية برمجياً
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





class TenantBaseModel(models.Model):
    """
    موديل تجريدي ترث منه كافة الجداول التي تحتاج للعزل حسب الشركة.
    """
    opco = models.ForeignKey(
        OpCo, 
        on_delete=models.CASCADE,
        related_name="%(class)s_records"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True