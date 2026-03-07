import threading

# كائن لتخزين البيانات الخاصة بكل Thread بشكل مستقل
_thread_locals = threading.local()

def set_current_tenant_id(tenant_id):
    """حفظ معرف الشركة للطلب الحالي"""
    setattr(_thread_locals, "tenant_id", tenant_id)

def get_current_tenant_id():
    """الحصول على معرف الشركة للطلب الحالي"""
    return getattr(_thread_locals, "tenant_id", None)

def clear_current_tenant_id():
    """مسح البيانات بعد انتهاء الطلب لضمان النظافة"""
    if hasattr(_thread_locals, "tenant_id"):
        delattr(_thread_locals, "tenant_id")