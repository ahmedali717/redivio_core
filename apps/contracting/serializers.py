# -*- coding: utf-8 -*-
from rest_framework import serializers
from .models import (
    Project, JobContract, ContractExtension, JobCostSheet, JobCostLine,
    QuantitySurvey, ContractAbstract, CheckTransaction, SiteCustody,
    SiteCustodyExpense, PaymentRequest, FabricationOrder, FabricationOrderLine,
    ManufacturingOrder, LoadingNote, LoadingNoteLine
)


class ProjectSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    contracts_count = serializers.SerializerMethodField()
    cost_sheets_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = '__all__'

    def get_contracts_count(self, obj):
        return obj.contracts.count()

    def get_cost_sheets_count(self, obj):
        return obj.cost_sheets.count()


class ContractExtensionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractExtension
        fields = '__all__'


class JobContractSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    customer_name = serializers.ReadOnlyField(source='customer.name')
    subcontractor_name = serializers.ReadOnlyField(source='subcontractor.name')
    extensions = ContractExtensionSerializer(many=True, read_only=True)

    class Meta:
        model = JobContract
        fields = '__all__'


class JobCostLineSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.name')
    subcontractor_name = serializers.ReadOnlyField(source='subcontractor.name')

    class Meta:
        model = JobCostLine
        fields = '__all__'


class JobCostSheetSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    contract_title = serializers.ReadOnlyField(source='contract.title')
    lines = JobCostLineSerializer(many=True, read_only=True)

    class Meta:
        model = JobCostSheet
        fields = '__all__'


class QuantitySurveySerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    item_code = serializers.ReadOnlyField(source='cost_line.item_code')
    item_description = serializers.ReadOnlyField(source='cost_line.description')

    class Meta:
        model = QuantitySurvey
        fields = '__all__'


class ContractAbstractSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    contract_title = serializers.ReadOnlyField(source='contract.title')
    contract_number = serializers.ReadOnlyField(source='contract.contract_number')

    class Meta:
        model = ContractAbstract
        fields = '__all__'


class CheckTransactionSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    customer_name = serializers.ReadOnlyField(source='customer.name')
    vendor_name = serializers.ReadOnlyField(source='vendor.name')

    class Meta:
        model = CheckTransaction
        fields = '__all__'


class SiteCustodyExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteCustodyExpense
        fields = '__all__'


class SiteCustodySerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    expenses = SiteCustodyExpenseSerializer(many=True, read_only=True)

    class Meta:
        model = SiteCustody
        fields = '__all__'


class PaymentRequestSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    vendor_name = serializers.ReadOnlyField(source='vendor.name')

    class Meta:
        model = PaymentRequest
        fields = '__all__'


class FabricationOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.name')
    boq_item_code = serializers.ReadOnlyField(source='boq_line.item_code')

    class Meta:
        model = FabricationOrderLine
        fields = '__all__'


class ManufacturingOrderSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    fabrication_order_number = serializers.ReadOnlyField(source='fabrication_order.order_number')

    class Meta:
        model = ManufacturingOrder
        fields = '__all__'


class FabricationOrderSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    contract_title = serializers.ReadOnlyField(source='contract.title')
    lines = FabricationOrderLineSerializer(many=True, read_only=True)
    mo_count = serializers.SerializerMethodField()
    loading_notes_count = serializers.SerializerMethodField()

    class Meta:
        model = FabricationOrder
        fields = '__all__'

    def get_mo_count(self, obj):
        return obj.manufacturing_orders.count()

    def get_loading_notes_count(self, obj):
        return obj.loading_notes.count()


class LoadingNoteLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadingNoteLine
        fields = '__all__'


class LoadingNoteSerializer(serializers.ModelSerializer):
    project_name = serializers.ReadOnlyField(source='project.name')
    project_code = serializers.ReadOnlyField(source='project.code')
    fabrication_order_number = serializers.ReadOnlyField(source='fabrication_order.order_number')
    lines = LoadingNoteLineSerializer(many=True, read_only=True)

    class Meta:
        model = LoadingNote
        fields = '__all__'

