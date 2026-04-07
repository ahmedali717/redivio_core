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
    # الروابط هتكون مباشرة: /api/wms/plants/
    path('', include(router.urls)), 
    
    # رابط الاستلام: /api/wms/stock-receipts/
    path('stock-receipts/', views.StockReceiptAPI.as_view(), name='api_stock_receipts'),
    
    # رابط الصرف (Delivery): /api/wms/stock-deliveries/
    path('stock-deliveries/', views.StockDeliveryAPI.as_view(), name='api_stock_deliveries'),
    
    # رابط التفاصيل للمشتريات والمبيعات
    path('purchase-orders/<int:po_id>/', views.get_purchase_order_details, name='api_po_details'),
    path('sales-orders/<int:so_id>/', views.get_sales_order_details, name='api_so_details'),
    
    path('dashboard/', views.WMSHomeView.as_view(), name='wms_home'),
    path('stats/', views.wms_stats, name='wms_stats'), 
]