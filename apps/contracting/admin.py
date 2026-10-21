# -*- coding: utf-8 -*-
from django.contrib import admin
from .models import (
    Project, JobContract, ContractExtension, JobCostSheet, JobCostLine,
    QuantitySurvey, ContractAbstract, CheckTransaction, SiteCustody,
    SiteCustodyExpense, PaymentRequest, FabricationOrder, FabricationOrderLine,
    ManufacturingOrder, LoadingNote, LoadingNoteLine
)


class JobCostLineInline(admin.TabularInline):
    model = JobCostLine
    extra = 1


class ContractExtensionInline(admin.TabularInline):
    model = ContractExtension
    extra = 0


class SiteCustodyExpenseInline(admin.TabularInline):
    model = SiteCustodyExpense
    extra = 1


class FabricationOrderLineInline(admin.TabularInline):
    model = FabricationOrderLine
    extra = 1


class LoadingNoteLineInline(admin.TabularInline):
    model = LoadingNoteLine
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'customer', 'status', 'contract_value', 'actual_cost', 'progress_percent', 'opco')
    list_filter = ('status', 'opco')
    search_fields = ('code', 'name', 'customer__name', 'consultant_name')


@admin.register(JobContract)
class JobContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'title', 'project', 'contract_type', 'total_amount', 'status', 'contract_date')
    list_filter = ('contract_type', 'status', 'opco')
    search_fields = ('contract_number', 'title', 'project__name')
    inlines = [ContractExtensionInline]


@admin.register(JobCostSheet)
class JobCostSheetAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'project', 'estimated_total_cost', 'actual_total_cost', 'status')
    list_filter = ('status', 'opco')
    search_fields = ('code', 'title', 'project__name')
    inlines = [JobCostLineInline]


@admin.register(ContractAbstract)
class ContractAbstractAdmin(admin.ModelAdmin):
    list_display = ('abstract_number', 'project', 'abstract_type', 'current_work_amount', 'net_payable_amount', 'status', 'date')
    list_filter = ('abstract_type', 'status', 'opco')
    search_fields = ('abstract_number', 'project__name')


@admin.register(CheckTransaction)
class CheckTransactionAdmin(admin.ModelAdmin):
    list_display = ('check_number', 'check_type', 'bank_name', 'amount', 'currency', 'due_date', 'status', 'party_name')
    list_filter = ('check_type', 'status', 'opco')
    search_fields = ('check_number', 'party_name', 'bank_name')


@admin.register(SiteCustody)
class SiteCustodyAdmin(admin.ModelAdmin):
    list_display = ('custody_code', 'custodian_name', 'project', 'assigned_amount', 'spent_amount', 'remaining_balance', 'status')
    list_filter = ('status', 'opco')
    search_fields = ('custody_code', 'custodian_name', 'project__name')
    inlines = [SiteCustodyExpenseInline]


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'project', 'beneficiary_type', 'beneficiary_name', 'amount', 'status', 'date')
    list_filter = ('beneficiary_type', 'status', 'opco')
    search_fields = ('request_number', 'beneficiary_name', 'project__name')


@admin.register(FabricationOrder)
class FabricationOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'title', 'project', 'status', 'order_date', 'target_date', 'responsible_engineer')
    list_filter = ('status', 'opco')
    search_fields = ('order_number', 'title', 'project__name', 'responsible_engineer')
    inlines = [FabricationOrderLineInline]


@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(admin.ModelAdmin):
    list_display = ('mo_number', 'product_name', 'project', 'fabrication_order', 'planned_qty', 'produced_qty', 'status')
    list_filter = ('status', 'opco')
    search_fields = ('mo_number', 'product_name', 'project__name')


@admin.register(LoadingNote)
class LoadingNoteAdmin(admin.ModelAdmin):
    list_display = ('note_number', 'project', 'vehicle_plate', 'driver_name', 'driver_phone', 'status', 'dispatch_date')
    list_filter = ('status', 'opco')
    search_fields = ('note_number', 'vehicle_plate', 'driver_name', 'project__name')
    inlines = [LoadingNoteLineInline]

