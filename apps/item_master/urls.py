from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MaterialViewSet, import_materials, SaleGroupViewSet # 👈 استيراد دالة الاستيراد

# إنشاء الراوتر وتسجيل الـ ViewSets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'sale-groups', SaleGroupViewSet)
router.register(r'materials', MaterialViewSet, basename='material')

urlpatterns = [
    # 🚀 مهم جداً: مسار الـ import لازم يكون "فوق" الراوتر عشان جينغو يلقطه الأول
    path('api/materials/import/', import_materials, name='import_materials'),

    # ربط مسارات الـ API تلقائياً
    path('api/', include(router.urls)),
]