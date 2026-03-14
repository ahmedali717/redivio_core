from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'plants', views.PlantViewSet)
router.register(r'locations', views.StorageLocationViewSet)
router.register(r'bins', views.StorageBinViewSet)
router.register(r'inventory', views.StockQuantViewSet, basename='inventory')
router.register(r'moves', views.StockMoveViewSet)

urlpatterns = [
    # 1. روابط الـ Router (تنتهي بـ /)
    path('api/', include(router.urls)), 
    
    # 2. رابط تنفيذ الاستلام (POST) - ده اللي كان ناقص ومسبب 404
    path('api/stock-receipts/', views.StockReceiptAPI.as_view(), name='api_stock_receipts'),
    
    # 3. رابط تفاصيل أمر التوريد (GET) - ده اللي كان ناقص
    path('api/purchase-orders/<int:po_id>/', views.get_purchase_order_details, name='api_po_details'),
    
    # 4. روابط الواجهة والإحصائيات
    path('dashboard/', views.WMSHomeView.as_view(), name='wms_home'),
    path('stats/', views.wms_stats, name='wms_stats'), 
]