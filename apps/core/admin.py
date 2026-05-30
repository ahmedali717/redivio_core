from django.contrib import admin
from django.utils import timezone
from .models import OpCo, SubscriptionRequest

@admin.register(OpCo)
class OpCoAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'currency', 'plan', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('currency', 'plan')

@admin.register(SubscriptionRequest)
class SubscriptionRequestAdmin(admin.ModelAdmin):
    list_display = ('opco', 'plan', 'payment_method', 'payment_status', 'status', 'amount', 'transaction_id', 'created_at')
    list_filter = ('status', 'payment_status', 'plan', 'payment_method')
    search_fields = ('opco__name', 'transaction_id')
    actions = ['approve_requests', 'reject_requests']

    @admin.action(description="تأكيد وتفعيل طلب الاشتراك / Approve & Activate Request")
    def approve_requests(self, request, queryset):
        count = 0
        for req in queryset.filter(status='pending'):
            req.status = 'approved'
            req.payment_status = 'paid'
            req.save()
            
            # تحديث خطة الشركة المستهدفة
            opco = req.opco
            opco.plan = req.plan
            opco.created_at = timezone.now()
            opco.save()
            count += 1
            
        self.message_user(
            request,
            f"تمت الموافقة وتفعيل {count} طلب اشتراك بنجاح." if count > 0 
            else "لا توجد طلبات معلقة للموافقة عليها."
        )

    @admin.action(description="رفض طلب الاشتراك / Reject Request")
    def reject_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(
            request,
            f"تم رفض {updated} طلب اشتراك." if updated > 0
            else "لا توجد طلبات معلقة لرفضها."
        )