from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AccountViewSet, CostCenterViewSet, JournalEntryViewSet,
    GLEntryViewSet, PurchaseInvoiceViewSet, PaymentEntryViewSet,
    FinancialReportsViewSet
)

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'cost-centers', CostCenterViewSet, basename='cost-center')
router.register(r'journal-entries', JournalEntryViewSet, basename='journal-entry')
router.register(r'gl-entries', GLEntryViewSet, basename='gl-entry')
router.register(r'purchase-invoices', PurchaseInvoiceViewSet, basename='purchase-invoice')
router.register(r'payment-entries', PaymentEntryViewSet, basename='payment-entry')
router.register(r'reports', FinancialReportsViewSet, basename='financial-reports')

urlpatterns = [
    path('', include(router.urls)),
]
