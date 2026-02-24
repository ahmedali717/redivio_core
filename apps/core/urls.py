from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# إعداد الراوتر للـ ViewSets (تأكد من مطابقة الأسماء للكلاسات في views.py)
router = DefaultRouter()
router.register(r'dashboard-stats', views.DashboardDataViewSet, basename='dashboard-stats')
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
    
    # صفحات الإعداد
    path('building-core/', views.modules_puzzle_view, name='modules_page'),
    path('verify-otp/', views.otp_view, name='otp_page'),
    path('setup-account/', views.setup_view, name='setup_page'),

    # ==========================================
    # 2. روابط الـ API والـ Router
    # ==========================================
    # روابط الراوتر (ViewSets) ستكون تحت مسار فارغ أو يمكن تخصيصها
    path('api/', include(router.urls)), 
    
    # روابط المصادقة (Auth API)
    path('api/login/', views.LoginAPI.as_view(), name='api_login'),
    path('api/signup/', views.TenantSignupAPI.as_view(), name='api_signup'),
    path('api/check-auth/', views.CheckAuthAPI.as_view(), name='api_check_auth'),
    path('api/check-email/', views.check_email_status, name='api_check_email'),
]