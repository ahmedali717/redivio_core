from rest_framework import serializers
from .models import Account, CostCenter, JournalEntry, JournalEntryLine, GLEntry, PurchaseInvoice, PaymentEntry


class AccountSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.account_name', read_only=True)
    children_count = serializers.IntegerField(source='children.count', read_only=True)

    class Meta:
        model = Account
        fields = [
            'id', 'opco', 'account_number', 'account_name', 'root_type', 'account_type',
            'parent', 'parent_name', 'is_group', 'currency', 'balance', 'is_active',
            'children_count', 'extra_data', 'created_at', 'updated_at'
        ]


class CostCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostCenter
        fields = '__all__'


class JournalEntryLineSerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_name = serializers.CharField(source='account.account_name', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.cost_center_name', read_only=True)

    class Meta:
        model = JournalEntryLine
        fields = [
            'id', 'journal_entry', 'account', 'account_number', 'account_name',
            'party_type', 'party_id', 'party_name', 'debit', 'credit',
            'cost_center', 'cost_center_name', 'remark', 'extra_data'
        ]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True, required=False)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            'id', 'opco', 'entry_number', 'posting_date', 'entry_type',
            'total_debit', 'total_credit', 'difference', 'status', 'docstatus',
            'reference_number', 'user_remark', 'created_by', 'created_by_username',
            'extra_data', 'created_at', 'updated_at', 'lines'
        ]
        read_only_fields = ['entry_number', 'total_debit', 'total_credit', 'difference', 'docstatus']

    def create(self, validated_data):
        lines_data = self.context.get('request').data.get('lines', []) if self.context.get('request') else []
        if 'lines' in validated_data:
            validated_data.pop('lines')

        journal_entry = JournalEntry.objects.create(**validated_data)
        for line in lines_data:
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account_id=line.get('account'),
                party_type=line.get('party_type', 'NONE'),
                party_id=line.get('party_id'),
                party_name=line.get('party_name', ''),
                debit=line.get('debit', 0),
                credit=line.get('credit', 0),
                cost_center_id=line.get('cost_center'),
                remark=line.get('remark', '')
            )
        journal_entry.validate_and_compute_totals()
        return journal_entry

    def update(self, instance, validated_data):
        lines_data = self.context.get('request').data.get('lines', None) if self.context.get('request') else None
        if 'lines' in validated_data:
            validated_data.pop('lines')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if lines_data is not None:
            instance.lines.all().delete()
            for line in lines_data:
                JournalEntryLine.objects.create(
                    journal_entry=instance,
                    account_id=line.get('account'),
                    party_type=line.get('party_type', 'NONE'),
                    party_id=line.get('party_id'),
                    party_name=line.get('party_name', ''),
                    debit=line.get('debit', 0),
                    credit=line.get('credit', 0),
                    cost_center_id=line.get('cost_center'),
                    remark=line.get('remark', '')
                )
        instance.validate_and_compute_totals()
        return instance


class GLEntrySerializer(serializers.ModelSerializer):
    account_number = serializers.CharField(source='account.account_number', read_only=True)
    account_name = serializers.CharField(source='account.account_name', read_only=True)

    class Meta:
        model = GLEntry
        fields = [
            'id', 'opco', 'posting_date', 'account', 'account_number', 'account_name',
            'party_type', 'party_id', 'party_name', 'debit', 'credit',
            'voucher_type', 'voucher_no', 'cost_center', 'remarks', 'is_cancelled', 'created_at'
        ]


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = [
            'id', 'opco', 'invoice_number', 'vendor', 'vendor_name',
            'purchase_order', 'po_number', 'receipt', 'posting_date', 'due_date',
            'currency', 'exchange_rate', 'subtotal', 'discount_amount', 'tax_amount',
            'grand_total', 'paid_amount', 'status', 'docstatus',
            'credit_to_account', 'expense_account', 'notes', 'extra_data', 'created_at'
        ]
        read_only_fields = ['invoice_number', 'paid_amount']


class PaymentEntrySerializer(serializers.ModelSerializer):
    paid_from_name = serializers.CharField(source='paid_from_account.account_name', read_only=True)
    paid_to_name = serializers.CharField(source='paid_to_account.account_name', read_only=True)

    class Meta:
        model = PaymentEntry
        fields = [
            'id', 'opco', 'entry_number', 'payment_type', 'party_type', 'party_id', 'party_name',
            'sales_invoice', 'purchase_invoice', 'paid_from_account', 'paid_from_name',
            'paid_to_account', 'paid_to_name', 'paid_amount', 'posting_date',
            'payment_method', 'reference_no', 'status', 'docstatus', 'notes',
            'extra_data', 'created_at'
        ]
        read_only_fields = ['entry_number', 'docstatus']
