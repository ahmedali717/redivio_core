# -*- coding: utf-8 -*-
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from decimal import Decimal

from .models import (
    Project, JobContract, ContractExtension, JobCostSheet, JobCostLine,
    QuantitySurvey, ContractAbstract, CheckTransaction, SiteCustody,
    SiteCustodyExpense, PaymentRequest
)
from .serializers import (
    ProjectSerializer, JobContractSerializer, ContractExtensionSerializer,
    JobCostSheetSerializer, JobCostLineSerializer, QuantitySurveySerializer,
    ContractAbstractSerializer, CheckTransactionSerializer, SiteCustodySerializer,
    SiteCustodyExpenseSerializer, PaymentRequestSerializer
)


class BaseOpCoViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        opco_id = self.request.query_params.get('opco') or self.request.headers.get('X-Opco-Id')
        if opco_id and hasattr(self.model, 'opco'):
            return qs.filter(opco_id=opco_id)
        return qs


class ProjectViewSet(BaseOpCoViewSet):
    queryset = Project.objects.all().select_related('customer', 'opco')
    serializer_class = ProjectSerializer
    model = Project


class JobContractViewSet(BaseOpCoViewSet):
    queryset = JobContract.objects.all().select_related('project', 'customer', 'subcontractor', 'opco')
    serializer_class = JobContractSerializer
    model = JobContract

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        contract_type = self.request.query_params.get('type')
        if contract_type:
            qs = qs.filter(contract_type=contract_type)
        return qs


class ContractExtensionViewSet(viewsets.ModelViewSet):
    queryset = ContractExtension.objects.all().select_related('contract')
    serializer_class = ContractExtensionSerializer
    permission_classes = [permissions.IsAuthenticated]


class JobCostSheetViewSet(BaseOpCoViewSet):
    queryset = JobCostSheet.objects.all().select_related('project', 'contract', 'opco').prefetch_related('lines')
    serializer_class = JobCostSheetSerializer
    model = JobCostSheet

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class JobCostLineViewSet(viewsets.ModelViewSet):
    queryset = JobCostLine.objects.all().select_related('cost_sheet', 'material', 'subcontractor')
    serializer_class = JobCostLineSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        sheet_id = self.request.query_params.get('cost_sheet')
        if sheet_id:
            qs = qs.filter(cost_sheet_id=sheet_id)
        return qs


class QuantitySurveyViewSet(viewsets.ModelViewSet):
    queryset = QuantitySurvey.objects.all().select_related('project', 'cost_line')
    serializer_class = QuantitySurveySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        return qs


class ContractAbstractViewSet(BaseOpCoViewSet):
    queryset = ContractAbstract.objects.all().select_related('project', 'contract', 'opco')
    serializer_class = ContractAbstractSerializer
    model = ContractAbstract

    def get_queryset(self):
        qs = super().get_queryset()
        project_id = self.request.query_params.get('project')
        if project_id:
            qs = qs.filter(project_id=project_id)
        abstract_type = self.request.query_params.get('type')
        if abstract_type:
            qs = qs.filter(abstract_type=abstract_type)
        return qs


class CheckTransactionViewSet(BaseOpCoViewSet):
    queryset = CheckTransaction.objects.all().select_related('project', 'customer', 'vendor', 'opco')
    serializer_class = CheckTransactionSerializer
    model = CheckTransaction

    def get_queryset(self):
        qs = super().get_queryset()
        check_type = self.request.query_params.get('type')
        if check_type:
            qs = qs.filter(check_type=check_type)
        check_status = self.request.query_params.get('status')
        if check_status:
            qs = qs.filter(status=check_status)
        return qs

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        check = self.get_object()
        new_status = request.data.get('status')
        if new_status:
            check.status = new_status
            check.rejection_reason = request.data.get('reason', '')
            check.save()
            return Response({'status': 'success', 'check_status': check.status})
        return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)


class SiteCustodyViewSet(BaseOpCoViewSet):
    queryset = SiteCustody.objects.all().select_related('project', 'opco').prefetch_related('expenses')
    serializer_class = SiteCustodySerializer
    model = SiteCustody


class SiteCustodyExpenseViewSet(viewsets.ModelViewSet):
    queryset = SiteCustodyExpense.objects.all().select_related('custody')
    serializer_class = SiteCustodyExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]


class PaymentRequestViewSet(BaseOpCoViewSet):
    queryset = PaymentRequest.objects.all().select_related('project', 'vendor', 'opco')
    serializer_class = PaymentRequestSerializer
    model = PaymentRequest


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def contracting_dashboard_stats(request):
    opco_id = request.query_params.get('opco') or request.headers.get('X-Opco-Id')
    
    projects_qs = Project.objects.all()
    contracts_qs = JobContract.objects.all()
    abstracts_qs = ContractAbstract.objects.all()
    checks_qs = CheckTransaction.objects.all()
    custody_qs = SiteCustody.objects.all()

    if opco_id:
        projects_qs = projects_qs.filter(opco_id=opco_id)
        contracts_qs = contracts_qs.filter(opco_id=opco_id)
        abstracts_qs = abstracts_qs.filter(opco_id=opco_id)
        checks_qs = checks_qs.filter(opco_id=opco_id)
        custody_qs = custody_qs.filter(opco_id=opco_id)

    total_projects = projects_qs.count()
    active_projects = projects_qs.filter(status='IN_PROGRESS').count()
    
    total_contracts_value = sum(c.total_amount for c in contracts_qs)
    total_abstracts_billed = sum(a.net_payable_amount for a in abstracts_qs)
    total_retention_held = sum(a.retention_deduction for a in abstracts_qs)
    
    pending_checks_count = checks_qs.filter(status__in=['HELD', 'DEPOSITED']).count()
    pending_checks_amount = sum(c.amount for c in checks_qs.filter(status__in=['HELD', 'DEPOSITED']))
    
    active_custody_balance = sum(c.remaining_balance for c in custody_qs.filter(status='ACTIVE'))

    return Response({
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_contracts_value': float(total_contracts_value),
        'total_abstracts_billed': float(total_abstracts_billed),
        'total_retention_held': float(total_retention_held),
        'pending_checks_count': pending_checks_count,
        'pending_checks_amount': float(pending_checks_amount),
        'active_custody_balance': float(active_custody_balance),
    })
