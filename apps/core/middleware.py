from django.db import models
from .models import OpCo 
from .context import set_current_tenant_id, clear_current_tenant_id

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. التحقق من تسجيل الدخول
        if not request.user.is_authenticated:
            return self.get_response(request)

        # 2. الحصول على معرف الشركة من الجلسة
        tenant_id = request.session.get("active_opco_id")
        tenant = None

        # 3. محاولة جلب الشركة المختارة
        # نستخدم objects العادية لضمان أن الميدل وير يرى الشركة ليتمكن من اختيارها
        if tenant_id:
            tenant = OpCo.objects.filter(
                id=tenant_id,
                is_active=True
            ).filter(
                models.Q(owner=request.user) | models.Q(companyuser__user=request.user)
            ).distinct().first()

        # 4. إذا لم يسبق الاختيار، نجلب أول شركة متاحة (القابضة غالباً)
        if not tenant:
            tenant = OpCo.objects.filter(is_active=True).filter(
                models.Q(owner=request.user) | models.Q(companyuser__user=request.user)
            ).distinct().first()

            if tenant:
                request.session["active_opco_id"] = tenant.id

        # --- 💡 استثناء روابط الإدارة لضمان عدم اختفاء الشركات من الهيدر ---
        # إذا كان الطلب يخص قائمة الشركات أو فحص الهوية، نوقف الفلترة التلقائية مؤقتاً
        is_api_opcos = request.path.startswith('/api/opcos/')
        is_check_auth = request.path.startswith('/api/check-auth/')

        if tenant:
            # نربط المعرف بالسياق فقط للعمليات التشغيلية (مخزون، أصناف، إلخ)
            if not (is_api_opcos or is_check_auth):
                set_current_tenant_id(tenant.id)
            
            # إتاحة الكائن في الـ request لاستخدامه في الـ HTML Templates
            request.tenant = tenant
        
        response = self.get_response(request)

        # تنظيف البيانات بعد انتهاء الطلب لضمان أمان البيانات للطلب القادم
        clear_current_tenant_id()

        return response