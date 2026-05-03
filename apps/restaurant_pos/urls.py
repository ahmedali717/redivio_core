from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import POSOrderViewSet

router = DefaultRouter()
router.register(r'orders', POSOrderViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
