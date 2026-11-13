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
        read_only_fields = ['id', 'journal_entry']
        extra_kwargs = {
            'party_type': {'required': False, 'allow_blank': True},
            'party_id': {'required': False, 'allow_null': True},
            'party_name': {'required': False, 'allow_blank': True},
            'cost_center': {'required': False, 'allow_null': True},
            'remark': {'required': False, 'allow_blank': True},
            'extra_data': {'required': False}
        }


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalEntryLineSerializer(many=True, required=False, allow_null=True)
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

    def to_internal_value(self, data):
        # تنظيف أسطر القيد لضمان عدم حدوث أخطاء تحويل أو قيم نصية فارغة
        if 'lines' in data and isinstance(data['lines'], list):
            cleaned_lines = []
            for line in data['lines']:
                if not isinstance(line, dict):
                    continue
                c_line = dict(line)
                if not c_line.get('party_type'):
                    c_line['party_type'] = 'NONE'
                if c_line.get('party_id') in ['', 'null', None, 0]:
                    c_line['party_id'] = None
                if c_line.get('cost_center') in ['', 'null', None, 0]:
                    c_line['cost_center'] = None
                if c_line.get('debit') in ['', None]:
                    c_line['debit'] = 0
                if c_line.get('credit') in ['', None]:
                    c_line['credit'] = 0
                cleaned_lines.append(c_line)
            data = dict(data)
            data['lines'] = cleaned_lines
        return super().to_internal_value(data)

    def create(self, validated_data):
        lines_data = self.context.get('request').data.get('lines', []) if self.context.get('request') else []
        if 'lines' in validated_data:
            validated_data.pop('lines')

        journal_entry = JournalEntry.objects.create(**validated_data)
        for line in lines_data:
            party_id = line.get('party_id')
            if party_id == '' or party_id == 'null' or party_id is None:
                party_id = None
            else:
                try:
                    party_id = int(party_id)
                except (ValueError, TypeError):
                    party_id = None

            cost_center_id = line.get('cost_center')
            if cost_center_id == '' or cost_center_id == 'null' or cost_center_id is None:
                cost_center_id = None
            else:
                try:
                    cost_center_id = int(cost_center_id)
                except (ValueError, TypeError):
                    cost_center_id = None

            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account_id=line.get('account'),
                party_type=line.get('party_type') or 'NONE',
                party_id=party_id,
                party_name=line.get('party_name') or '',
                debit=line.get('debit') or 0,
                credit=line.get('credit') or 0,
                cost_center_id=cost_center_id,
                remark=line.get('remark') or ''
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
                party_id = line.get('party_id')
                if party_id == '' or party_id == 'null' or party_id is None:
                    party_id = None
                else:
                    try:
                        party_id = int(party_id)
                    except (ValueError, TypeError):
                        party_id = None

                cost_center_id = line.get('cost_center')
                if cost_center_id == '' or cost_center_id == 'null' or cost_center_id is None:
                    cost_center_id = None
                else:
                    try:
                        cost_center_id = int(cost_center_id)
                    except (ValueError, TypeError):
                        cost_center_id = None

                JournalEntryLine.objects.create(
                    journal_entry=instance,
                    account_id=line.get('account'),
                    party_type=line.get('party_type') or 'NONE',
                    party_id=party_id,
                    party_name=line.get('party_name') or '',
                    debit=line.get('debit') or 0,
                    credit=line.get('credit') or 0,
                    cost_center_id=cost_center_id,
                    remark=line.get('remark') or ''
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
