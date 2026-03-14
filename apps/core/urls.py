from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# 1. إعداد الراوتر للـ ViewSets (العناوين التلقائية)
router = DefaultRouter()
router.register(r'dashboard-data', views.DashboardDataViewSet, basename='dashboard-data')
router.register(r'opcos', views.OpCoViewSet, basename='opcos')
router.register(r'plants', views.PlantViewSet, basename='plants')
router.register(r'locations', views.LocationViewSet, basename='locations')
router.register(r'bins', views.StorageBinViewSet, basename='bins')

# 🚀 تسجيل راوتر أوامر التوريد (المشتريات) - لخدمة /api/orders/
router.register(r'orders', views.PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'vendors', views.VendorViewSet, basename='vendors')

urlpatterns = [
    # ==========================================
    # 1. صفحات الـ HTML (Web Pages)
    # ==========================================
    path('', views.landing_view, name='landing_page'),
    path('login/', views.login_view, name='login_page'),
    path('signup/', views.signup_view, name='signup_page'),
    path('dashboard/', views.dashboard_view, name='dashboard_home'),
    path('logout/', views.logout_view, name='logout_action'),
    
    # صفحات الإعداد والـ Onboarding
    path('building-core/', views.modules_puzzle_view, name='modules_page'),
    path('verify-otp/', views.otp_view, name='otp_page'),
    path('setup-account/', views.setup_view, name='setup_page'),

    # ==========================================
    # 2. روابط الـ API والـ Router
    # ==========================================
    
    # روابط الراوتر التلقائية (ViewSets) تحت مسار /api/
    path('api/', include(router.urls)), 
    
    # 🚀 رابط استلام البضاعة (المخازن) - لخدمة /api/stock-receipts/
    # تأكد أن اسم الدالة في views.py هو receive_stock
    path('api/stock-receipts/', views.receive_stock, name='api_stock_receipts'),

    # روابط المصادقة والتحكم (Custom API Views)
    path('api/login/', views.LoginAPI.as_view(), name='api_login'),
    path('api/signup/', views.TenantSignupAPI.as_view(), name='api_signup'),
    path('api/check-auth/', views.CheckAuthAPI.as_view(), name='api_check_auth'),
    path('api/check-email/', views.check_email_status, name='api_check_email'),
    path('api/switch-company/', views.switch_active_company, name='api_switch_company'),
]