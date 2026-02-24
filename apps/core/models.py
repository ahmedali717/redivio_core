from django.db import models
from django.conf import settings

class OpCo(models.Model):
    """
    الشركة المشغلة (Tenant / Workspace)
    تم حذف الروابط الخاصة بـ django-tenants لأننا نستخدم PostgreSQL عادي.
    """
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # أفضل من get_user_model لتجنب مشاكل التحميل
        on_delete=models.CASCADE,
        related_name="owned_companies"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

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

    def __str__(self):
        return f"{self.name} ({self.code})"


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