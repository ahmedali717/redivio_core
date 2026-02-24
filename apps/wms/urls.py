from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 1. إعداد الـ Router وتسجيل الـ ViewSets
# ملاحظة: تم التأكد من أن جميع المسارات مسجلة بشكل صحيح لتتوافق مع طلبات Vue.js
router = DefaultRouter()
router.register(r'plants', views.PlantViewSet)
router.register(r'locations', views.StorageLocationViewSet)
router.register(r'bins', views.StorageBinViewSet)
router.register(r'inventory', views.StockQuantViewSet, basename='inventory')
router.register(r'moves', views.StockMoveViewSet)

urlpatterns = [
    # روابط الـ API: ستبدأ جميعها بـ /api/ مثل /api/moves/
    # الـ include(router.urls) يضيف تلقائياً السلاش النهائي (Trailing Slash)
    path('api/', include(router.urls)), 
    
    # روابط واجهة المستخدم (Template Views)
    path('dashboard/', views.WMSHomeView.as_view(), name='wms_home'),
    
    # رابط الإحصائيات المخصص
    path('stats/', views.wms_stats, name='wms_stats'), 
]