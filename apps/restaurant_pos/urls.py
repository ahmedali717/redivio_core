from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import POSOrderViewSet, RestaurantFloorViewSet, RestaurantTableViewSet

router = DefaultRouter()
router.register(r'orders', POSOrderViewSet)
router.register(r'floors', RestaurantFloorViewSet, basename='floors')
router.register(r'tables', RestaurantTableViewSet, basename='tables')

urlpatterns = [
    path('', include(router.urls)),
]
