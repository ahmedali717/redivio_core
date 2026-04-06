from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# 1. استيراد الـ ViewSets
from apps.core.views import (
    OpCoViewSet,
    PlantViewSet,
    LocationViewSet,
    StorageBinViewSet,
    DashboardDataViewSet,
    logout_view
)
# 👈 مسحنا FieldDefinitionViewSet من السطر ده
from apps.item_master.views import MaterialViewSet, CategoryViewSet
from apps.wms.views import StockQuantViewSet, StockMoveViewSet
# عدل السطر ده ليتضمن الدالة الجديدة
from apps.procurement.views import VendorViewSet, PurchaseOrderViewSet, PurchaseOrderLineViewSet, print_po_pdf, print_grn_pdf, StockReceiptViewSet
from apps.sales.views import CustomerViewSet, SalesOrderViewSet, SalesOrderLineViewSet, SalesInvoiceViewSet, CustomerPaymentViewSet

# 2. إعداد الراوتر
router = DefaultRouter()

# ✅✅✅ الإصلاح الأساسي: إضافة basename="..." لكل سطر هنا
router.register(r'dashboard-data', DashboardDataViewSet, basename='dashboard-data')
router.register(r'opcos', OpCoViewSet, basename='opco')
router.register(r'plants', PlantViewSet, basename='plant')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'bins', StorageBinViewSet, basename='bin')

router.register(r'materials', MaterialViewSet, basename='material')
router.register(r'categories', CategoryViewSet, basename='category')
# 👈 مسحنا سطر تسجيل الـ fields من هنا

router.register(r'inventory', StockQuantViewSet, basename='stockquant')
router.register(r'moves', StockMoveViewSet, basename='stockmove')

router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'stock-receipts', StockReceiptViewSet, basename='stockreceipt')
router.register(r'orders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'order-lines', PurchaseOrderLineViewSet, basename='purchaseorderline')

router.register(r'customers', CustomerViewSet, basename='customer')
router.register(r'sales-orders', SalesOrderViewSet, basename='salesorder')
router.register(r'sales-lines', SalesOrderLineViewSet, basename='salesorderline')
router.register(r'sales-invoices', SalesInvoiceViewSet, basename='salesinvoice')
router.register(r'customer-payments', CustomerPaymentViewSet, basename='customerpayment')

# 3. الروابط
urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), # ✅ رابط تغيير اللغة
    path('api/', include(router.urls)),
    path('api/wms/', include('apps.wms.urls')),
    path('print/po/<int:pk>/', print_po_pdf, name='print_po_pdf'),
    path('print/grn/<int:pk>/', print_grn_pdf, name='print_grn'),
    path('logout/', logout_view, name='logout'), # ✅ رابط الخروج
    path('', include('apps.core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)