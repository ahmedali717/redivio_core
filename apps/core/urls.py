from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# إعداد الراوتر للـ ViewSets
# تأكد من أن الأسماء هنا تطابق تماماً ما نطلبه في fetch() داخل ملفات الـ JavaScript
router = DefaultRouter()
router.register(r'dashboard-data', views.DashboardDataViewSet, basename='dashboard-data')
router.register(r'opcos', views.OpCoViewSet, basename='opcos')
router.register(r'plants', views.PlantViewSet, basename='plants')
router.register(r'locations', views.LocationViewSet, basename='locations')
router.register(r'bins', views.StorageBinViewSet, basename='bins')

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
    
    # روابط الراوتر التلقائية (ViewSets)
    path('api/', include(router.urls)), 
    
    # روابط المصادقة والتحكم (Custom API Views)
    path('api/login/', views.LoginAPI.as_view(), name='api_login'),
    path('api/signup/', views.TenantSignupAPI.as_view(), name='api_signup'),
    path('api/send-otp/', views.send_otp, name='api_send_otp'),
    path('api/verify-otp/', views.verify_otp, name='api_verify_otp'),
    path('api/check-auth/', views.CheckAuthAPI.as_view(), name='api_check_auth'),
    path('api/check-email/', views.check_email_status, name='api_check_email'),
    path('api/switch-company/', views.switch_active_company, name='api_switch_company'),
    path('api/change-plan/', views.ChangePlanAPI.as_view(), name='api_change_plan'),
    path('api/debug-logs/', views.get_debug_logs, name='api_debug_logs'),
]