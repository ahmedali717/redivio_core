from django.contrib import admin
from .models import Account, CostCenter, JournalEntry, JournalEntryLine, GLEntry, PurchaseInvoice, PaymentEntry


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'account_name', 'root_type', 'account_type', 'parent', 'is_group', 'balance', 'currency')
    list_filter = ('root_type', 'account_type', 'is_group', 'opco')
    search_fields = ('account_number', 'account_name')


@admin.register(CostCenter)
class CostCenterAdmin(admin.ModelAdmin):
    list_display = ('code', 'cost_center_name', 'parent', 'is_group')
    search_fields = ('code', 'cost_center_name')


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 2


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'posting_date', 'entry_type', 'total_debit', 'total_credit', 'difference', 'status')
    list_filter = ('status', 'entry_type', 'posting_date', 'opco')
    search_fields = ('entry_number', 'reference_number', 'user_remark')
    inlines = [JournalEntryLineInline]


@admin.register(GLEntry)
class GLEntryAdmin(admin.ModelAdmin):
    list_display = ('posting_date', 'account', 'voucher_type', 'voucher_no', 'debit', 'credit', 'party_type', 'party_name', 'is_cancelled')
    list_filter = ('voucher_type', 'is_cancelled', 'posting_date', 'opco')
    search_fields = ('voucher_no', 'account__account_name', 'account__account_number', 'party_name')


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'vendor', 'posting_date', 'due_date', 'grand_total', 'paid_amount', 'status')
    list_filter = ('status', 'posting_date', 'opco')
    search_fields = ('invoice_number', 'vendor__name')


@admin.register(PaymentEntry)
class PaymentEntryAdmin(admin.ModelAdmin):
    list_display = ('entry_number', 'payment_type', 'party_type', 'party_name', 'paid_amount', 'paid_from_account', 'paid_to_account', 'posting_date', 'status')
    list_filter = ('payment_type', 'payment_method', 'status', 'posting_date', 'opco')
    search_fields = ('entry_number', 'party_name', 'reference_no')
