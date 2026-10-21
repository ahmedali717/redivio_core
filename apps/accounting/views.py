import datetime
import decimal
from django.db.models import Sum, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Account, CostCenter, JournalEntry, JournalEntryLine, GLEntry, PurchaseInvoice, PaymentEntry
from .serializers import (
    AccountSerializer, CostCenterSerializer, JournalEntrySerializer,
    GLEntrySerializer, PurchaseInvoiceSerializer, PaymentEntrySerializer
)
from .services import seed_default_chart_of_accounts


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Account.objects.all().select_related('parent')
        opco_id = self.request.query_params.get('opco')
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        root_type = self.request.query_params.get('root_type')
        if root_type:
            qs = qs.filter(root_type=root_type)
        is_group = self.request.query_params.get('is_group')
        if is_group is not None:
            qs = qs.filter(is_group=(is_group.lower() == 'true'))
        return qs

    @action(detail=False, methods=['post'], url_path='seed-coa')
    def seed_coa(self, request):
        """توليد شجرة الحسابات القياسية للشركة التابعة بضغطة زر"""
        opco_id = request.data.get('opco_id')
        if not opco_id:
            from apps.core.models import OpCo
            opco = OpCo.objects.first()
        else:
            from apps.core.models import OpCo
            opco = OpCo.objects.filter(id=opco_id).first()

        if not opco:
            return Response({"error": "الشركة التابعة (OpCo) غير محددة أو غير موجودة."}, status=status.HTTP_400_BAD_REQUEST)

        created = seed_default_chart_of_accounts(opco)
        if created:
            return Response({"message": f"تم إنشاء شجرة الحسابات القياسية بنجاح للشركة: {opco.name}"})
        else:
            return Response({"message": "شجرة الحسابات موجودة بالفعل لهذه الشركة."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """إرجاع شجرة الحسابات بتسلسل هرمي للعرض المرئي"""
        opco_id = request.query_params.get('opco')
        qs = self.get_queryset()
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        
        accounts = list(qs.order_by('account_number'))
        account_dict = {a.id: {
            'id': a.id,
            'account_number': a.account_number,
            'account_name': a.account_name,
            'root_type': a.root_type,
            'account_type': a.account_type,
            'is_group': a.is_group,
            'currency': a.currency,
            'balance': float(a.balance),
            'parent': a.parent_id,
            'children': []
        } for a in accounts}

        tree = []
        for a in accounts:
            node = account_dict[a.id]
            if a.parent_id and a.parent_id in account_dict:
                account_dict[a.parent_id]['children'].append(node)
            else:
                tree.append(node)

        return Response(tree)


class CostCenterViewSet(viewsets.ModelViewSet):
    serializer_class = CostCenterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = CostCenter.objects.all()
        opco_id = self.request.query_params.get('opco')
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        return qs


class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = JournalEntry.objects.all().prefetch_related('lines__account')
        opco_id = self.request.query_params.get('opco')
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        entry_status = self.request.query_params.get('status')
        if entry_status:
            qs = qs.filter(status=entry_status)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_entry(self, request, pk=None):
        """اعتماد وترحيل سند القيد"""
        entry = self.get_object()
        try:
            entry.submit_and_post()
            return Response({"message": f"تم اعتماد وترحيل سند القيد {entry.entry_number} بنجاح.", "status": entry.status})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_entry(self, request, pk=None):
        """إلغاء سند القيد وعكس قيود الأستاذ العام"""
        entry = self.get_object()
        try:
            entry.cancel()
            return Response({"message": f"تم إلغاء سند القيد {entry.entry_number}.", "status": entry.status})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class GLEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GLEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = GLEntry.objects.filter(is_cancelled=False).select_related('account')
        opco_id = self.request.query_params.get('opco')
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        account_id = self.request.query_params.get('account')
        if account_id:
            qs = qs.filter(account_id=account_id)
        from_date = self.request.query_params.get('from_date')
        if from_date:
            qs = qs.filter(posting_date__gte=from_date)
        to_date = self.request.query_params.get('to_date')
        if to_date:
            qs = qs.filter(posting_date__lte=to_date)
        voucher_no = self.request.query_params.get('voucher_no')
        if voucher_no:
            qs = qs.filter(voucher_no__icontains=voucher_no)
        party_type = self.request.query_params.get('party_type')
        if party_type:
            qs = qs.filter(party_type=party_type)
        party_id = self.request.query_params.get('party_id')
        if party_id:
            qs = qs.filter(party_id=party_id)
        return qs.order_by('-posting_date', '-id')


class PurchaseInvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseInvoiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PurchaseInvoice.objects.all().select_related('vendor', 'purchase_order')
        opco_id = self.request.query_params.get('opco')
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        inv_status = self.request.query_params.get('status')
        if inv_status:
            qs = qs.filter(status=inv_status)
        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        return qs


class PaymentEntryViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PaymentEntry.objects.all().select_related('paid_from_account', 'paid_to_account', 'sales_invoice', 'purchase_invoice')
        opco_id = self.request.query_params.get('opco')
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        payment_type = self.request.query_params.get('payment_type')
        if payment_type:
            qs = qs.filter(payment_type=payment_type)
        entry_status = self.request.query_params.get('status')
        if entry_status:
            qs = qs.filter(status=entry_status)
        return qs

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_payment(self, request, pk=None):
        entry = self.get_object()
        try:
            entry.submit_and_post()
            return Response({"message": f"تم اعتماد وترحيل سند الدفع {entry.entry_number} بنجاح.", "status": entry.status})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_payment(self, request, pk=None):
        entry = self.get_object()
        try:
            entry.cancel()
            return Response({"message": f"تم إلغاء سند الدفع {entry.entry_number}.", "status": entry.status})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FinancialReportsViewSet(viewsets.ViewSet):
    """
    محرك التقارير المالية المتطورة المستوحى من ERPNext:
    - ميزان المراجعة (Trial Balance)
    - قائمة الدخل / الأرباح والخسائر (Profit and Loss)
    - الميزانية العمومية (Balance Sheet)
    - كشف حساب الأستاذ العام (General Ledger Statement)
    """
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='trial-balance')
    def trial_balance(self, request):
        opco_id = request.query_params.get('opco')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date', datetime.date.today().isoformat())

        accounts = Account.objects.filter(is_group=False)
        if opco_id:
            accounts = accounts.filter(opco_id=opco_id)

        rows = []
        total_debit = decimal.Decimal('0.00')
        total_credit = decimal.Decimal('0.00')

        for acc in accounts:
            gl_qs = GLEntry.objects.filter(account=acc, is_cancelled=False)
            if opco_id:
                gl_qs = gl_qs.filter(opco_id=opco_id)
            if from_date:
                gl_qs = gl_qs.filter(posting_date__gte=from_date)
            if to_date:
                gl_qs = gl_qs.filter(posting_date__lte=to_date)

            totals = gl_qs.aggregate(d=Sum('debit'), c=Sum('credit'))
            debit = totals['d'] or decimal.Decimal('0.00')
            credit = totals['c'] or decimal.Decimal('0.00')

            if debit > 0 or credit > 0:
                net = debit - credit
                total_debit += debit
                total_credit += credit
                rows.append({
                    'account_id': acc.id,
                    'account_number': acc.account_number,
                    'account_name': acc.account_name,
                    'root_type': acc.root_type,
                    'debit': float(debit),
                    'credit': float(credit),
                    'net': float(net)
                })

        return Response({
            'from_date': from_date,
            'to_date': to_date,
            'total_debit': float(total_debit),
            'total_credit': float(total_credit),
            'is_balanced': abs(total_debit - total_credit) < decimal.Decimal('0.01'),
            'rows': rows
        })

    @action(detail=False, methods=['get'], url_path='profit-and-loss')
    def profit_and_loss(self, request):
        opco_id = request.query_params.get('opco')
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date', datetime.date.today().isoformat())

        # حساب الإيرادات (Income)
        income_accs = Account.objects.filter(root_type='INCOME', is_group=False)
        if opco_id: income_accs = income_accs.filter(opco_id=opco_id)
        
        income_rows = []
        total_income = decimal.Decimal('0.00')
        for acc in income_accs:
            gl = GLEntry.objects.filter(account=acc, is_cancelled=False)
            if from_date: gl = gl.filter(posting_date__gte=from_date)
            if to_date: gl = gl.filter(posting_date__lte=to_date)
            t = gl.aggregate(d=Sum('debit'), c=Sum('credit'))
            amt = (t['c'] or 0) - (t['d'] or 0)
            if amt != 0:
                total_income += amt
                income_rows.append({'account_name': acc.account_name, 'amount': float(amt)})

        # حساب المصروفات (Expenses)
        expense_accs = Account.objects.filter(root_type='EXPENSE', is_group=False)
        if opco_id: expense_accs = expense_accs.filter(opco_id=opco_id)
        
        expense_rows = []
        total_expenses = decimal.Decimal('0.00')
        for acc in expense_accs:
            gl = GLEntry.objects.filter(account=acc, is_cancelled=False)
            if from_date: gl = gl.filter(posting_date__gte=from_date)
            if to_date: gl = gl.filter(posting_date__lte=to_date)
            t = gl.aggregate(d=Sum('debit'), c=Sum('credit'))
            amt = (t['d'] or 0) - (t['c'] or 0)
            if amt != 0:
                total_expenses += amt
                expense_rows.append({'account_name': acc.account_name, 'amount': float(amt)})

        net_profit = total_income - total_expenses

        return Response({
            'from_date': from_date,
            'to_date': to_date,
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'net_profit': float(net_profit),
            'income_rows': income_rows,
            'expense_rows': expense_rows
        })

    @action(detail=False, methods=['get'], url_path='balance-sheet')
    def balance_sheet(self, request):
        opco_id = request.query_params.get('opco')
        as_of_date = request.query_params.get('as_of_date', datetime.date.today().isoformat())

        def get_root_total(root_type):
            accs = Account.objects.filter(root_type=root_type, is_group=False)
            if opco_id: accs = accs.filter(opco_id=opco_id)
            total = decimal.Decimal('0.00')
            items = []
            for acc in accs:
                gl = GLEntry.objects.filter(account=acc, is_cancelled=False, posting_date__lte=as_of_date)
                t = gl.aggregate(d=Sum('debit'), c=Sum('credit'))
                d = t['d'] or decimal.Decimal('0.00')
                c = t['c'] or decimal.Decimal('0.00')
                val = (d - c) if root_type in ['ASSET', 'EXPENSE'] else (c - d)
                if val != 0:
                    total += val
                    items.append({'account_name': acc.account_name, 'amount': float(val)})
            return total, items

        total_assets, asset_items = get_root_total('ASSET')
        total_liabilities, liability_items = get_root_total('LIABILITY')
        total_equity, equity_items = get_root_total('EQUITY')

        # أرباح الفترة تضاف إلى حقوق الملكية
        inc, _ = get_root_total('INCOME')
        exp, _ = get_root_total('EXPENSE')
        period_profit = inc - exp
        total_equity_and_reserves = total_equity + period_profit

        return Response({
            'as_of_date': as_of_date,
            'total_assets': float(total_assets),
            'total_liabilities': float(total_liabilities),
            'total_equity': float(total_equity_and_reserves),
            'period_profit': float(period_profit),
            'is_balanced': abs(total_assets - (total_liabilities + total_equity_and_reserves)) < decimal.Decimal('0.01'),
            'asset_items': asset_items,
            'liability_items': liability_items,
            'equity_items': equity_items
        })
