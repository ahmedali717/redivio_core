# -*- coding: utf-8 -*-
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProjectViewSet, JobContractViewSet, ContractExtensionViewSet,
    JobCostSheetViewSet, JobCostLineViewSet, QuantitySurveyViewSet,
    ContractAbstractViewSet, CheckTransactionViewSet, SiteCustodyViewSet,
    SiteCustodyExpenseViewSet, PaymentRequestViewSet, contracting_dashboard_stats,
    FabricationOrderViewSet, FabricationOrderLineViewSet,
    ManufacturingOrderViewSet, LoadingNoteViewSet, LoadingNoteLineViewSet
)

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='contracting-project')
router.register(r'contracts', JobContractViewSet, basename='contracting-contract')
router.register(r'extensions', ContractExtensionViewSet, basename='contracting-extension')
router.register(r'cost-sheets', JobCostSheetViewSet, basename='contracting-cost-sheet')
router.register(r'cost-lines', JobCostLineViewSet, basename='contracting-cost-line')
router.register(r'quantity-surveys', QuantitySurveyViewSet, basename='contracting-qs')
router.register(r'abstracts', ContractAbstractViewSet, basename='contracting-abstract')
router.register(r'checks', CheckTransactionViewSet, basename='contracting-check')
router.register(r'custodies', SiteCustodyViewSet, basename='contracting-custody')
router.register(r'custody-expenses', SiteCustodyExpenseViewSet, basename='contracting-custody-expense')
router.register(r'payment-requests', PaymentRequestViewSet, basename='contracting-payment-request')
router.register(r'fabrication-orders', FabricationOrderViewSet, basename='contracting-fabrication-order')
router.register(r'fabrication-lines', FabricationOrderLineViewSet, basename='contracting-fabrication-line')
router.register(r'manufacturing-orders', ManufacturingOrderViewSet, basename='contracting-mo')
router.register(r'loading-notes', LoadingNoteViewSet, basename='contracting-loading-note')
router.register(r'loading-lines', LoadingNoteLineViewSet, basename='contracting-loading-line')

urlpatterns = [
    path('dashboard-stats/', contracting_dashboard_stats, name='contracting-dashboard-stats'),
    path('', include(router.urls)),
]
