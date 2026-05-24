from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import POSOrderViewSet, RestaurantFloorViewSet, RestaurantTableViewSet, POSTerminalViewSet

router = DefaultRouter()
router.register(r'orders', POSOrderViewSet)
router.register(r'floors', RestaurantFloorViewSet, basename='floors')
router.register(r'tables', RestaurantTableViewSet, basename='tables')
router.register(r'terminals', POSTerminalViewSet, basename='terminals')

urlpatterns = [
    path('', include(router.urls)),
]
