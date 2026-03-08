from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, MaterialViewSet

# إنشاء الراوتر وتسجيل الـ ViewSets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'materials', MaterialViewSet, basename='material')

urlpatterns = [
    # ربط مسارات الـ API تلقائياً
    path('api/', include(router.urls)),
]