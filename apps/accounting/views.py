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


def get_request_opco_id(request):
    """
    استخراج معرف الشركة التابعة (OpCo ID) من الطلب بعدة طرق موثوقة:
    1. Query param 'opco' أو 'opco_id'
    2. Body param 'opco' أو 'opco_id'
    3. request.tenant (من TenantMiddleware)
    4. request.session['active_opco_id']
    5. Fallback إلى أول شركة موجودة في النظام
    """
    opco_id = None
    if hasattr(request, 'query_params'):
        opco_id = request.query_params.get('opco') or request.query_params.get('opco_id')
    if not opco_id and hasattr(request, 'data') and isinstance(request.data, dict):
        opco_id = request.data.get('opco_id') or request.data.get('opco')

    if opco_id and str(opco_id).lower() not in ['null', 'undefined', '', 'none', 'all']:
        try:
            return int(opco_id)
        except (ValueError, TypeError):
            return opco_id

    if opco_id and str(opco_id).lower() == 'all':
        return None

    if hasattr(request, 'tenant') and request.tenant:
        return request.tenant.id

    if hasattr(request, 'session'):
        session_opco = request.session.get('active_opco_id')
        if session_opco:
            return session_opco

    from apps.core.models import OpCo
    first_opco = OpCo.objects.first()
    return first_opco.id if first_opco else None


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Account.objects.all().select_related('parent')
        opco_id = get_request_opco_id(self.request)
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        root_type = self.request.query_params.get('root_type')
        if root_type:
            qs = qs.filter(root_type=root_type)
        is_group = self.request.query_params.get('is_group')
        if is_group is not None:
            qs = qs.filter(is_group=(is_group.lower() == 'true'))
        return qs

    def perform_create(self, serializer):
        opco_id = get_request_opco_id(self.request)
        if 'opco' not in serializer.validated_data and opco_id:
            from apps.core.models import OpCo
            serializer.save(opco=OpCo.objects.filter(id=opco_id).first())
        else:
            serializer.save()

    @action(detail=False, methods=['post'], url_path='seed-coa')
    def seed_coa(self, request):
        """توليد شجرة الحسابات القياسية للشركة التابعة بضغطة زر"""
        from apps.core.models import OpCo
        opco_id = get_request_opco_id(request)
        opco = None
        if opco_id:
            opco = OpCo.objects.filter(id=opco_id).first()
        if not opco and hasattr(request, 'tenant') and request.tenant:
            opco = request.tenant
        if not opco:
            opco = OpCo.objects.first()

        if not opco:
            return Response({"error": "الشركة التابعة (OpCo) غير محددة أو غير موجودة."}, status=status.HTTP_400_BAD_REQUEST)

        created_count, total_count = seed_default_chart_of_accounts(opco)
        if created_count > 0:
            return Response({
                "message": f"تم توليد وتحديث شجرة حسابات ERPNext بنجاح للشركة: {opco.name} (تمت إضافة {created_count} حساباً جديداً، الإجمالي: {total_count})",
                "opco_id": opco.id,
                "opco_name": opco.name,
                "created_count": created_count,
                "total_count": total_count
            })
        else:
            return Response({
                "message": f"شجرة حسابات ERPNext مكتملة ومحدثة بالكامل للشركة: {opco.name} (إجمالي {total_count} حساباً)",
                "opco_id": opco.id,
                "opco_name": opco.name,
                "created_count": created_count,
                "total_count": total_count
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """إرجاع شجرة الحسابات بتسلسل هرمي للعرض المرئي"""
        qs = self.get_queryset()
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
        opco_id = get_request_opco_id(self.request)
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        return qs

    def perform_create(self, serializer):
        opco_id = get_request_opco_id(self.request)
        if 'opco' not in serializer.validated_data and opco_id:
            from apps.core.models import OpCo
            serializer.save(opco=OpCo.objects.filter(id=opco_id).first())
        else:
            serializer.save()


class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = JournalEntry.objects.all().prefetch_related('lines__account')
        opco_id = get_request_opco_id(self.request)
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        entry_status = self.request.query_params.get('status')
        if entry_status:
            qs = qs.filter(status=entry_status)
        return qs

    def perform_create(self, serializer):
        opco_id = get_request_opco_id(self.request)
        kwargs = {'created_by': self.request.user}
        if 'opco' not in serializer.validated_data and opco_id:
            from apps.core.models import OpCo
            kwargs['opco'] = OpCo.objects.filter(id=opco_id).first()
        serializer.save(**kwargs)

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
        opco_id = get_request_opco_id(self.request)
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
        opco_id = get_request_opco_id(self.request)
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        inv_status = self.request.query_params.get('status')
        if inv_status:
            qs = qs.filter(status=inv_status)
        vendor_id = self.request.query_params.get('vendor')
        if vendor_id:
            qs = qs.filter(vendor_id=vendor_id)
        return qs

    def perform_create(self, serializer):
        opco_id = get_request_opco_id(self.request)
        if 'opco' not in serializer.validated_data and opco_id:
            from apps.core.models import OpCo
            serializer.save(opco=OpCo.objects.filter(id=opco_id).first())
        else:
            serializer.save()

    @action(detail=True, methods=['post'], url_path='post-gl')
    def post_invoice(self, request, pk=None):
        """اعتماد وترحيل فاتورة المشتريات إلى دفتر الأستاذ العام"""
        pi = self.get_object()
        try:
            pi.post_gl_entries()
            pi.docstatus = 1
            if not pi.extra_data:
                pi.extra_data = {}
            pi.extra_data['is_posted'] = True
            pi.save(update_fields=['docstatus', 'extra_data'])
            return Response({"message": f"تم ترحيل فاتورة المشتريات {pi.invoice_number} بنجاح إلى دفتر الأستاذ العام."})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class PaymentEntryViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = PaymentEntry.objects.all().select_related('paid_from_account', 'paid_to_account', 'sales_invoice', 'purchase_invoice')
        opco_id = get_request_opco_id(self.request)
        if opco_id:
            qs = qs.filter(opco_id=opco_id)
        payment_type = self.request.query_params.get('payment_type')
        if payment_type:
            qs = qs.filter(payment_type=payment_type)
        entry_status = self.request.query_params.get('status')
        if entry_status:
            qs = qs.filter(status=entry_status)
        return qs

    def perform_create(self, serializer):
        opco_id = get_request_opco_id(self.request)
        if 'opco' not in serializer.validated_data and opco_id:
            from apps.core.models import OpCo
            serializer.save(opco=OpCo.objects.filter(id=opco_id).first())
        else:
            serializer.save()

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
    محرك التقارير المالية المتطورة المستوحى من ERPNext و Odoo:
    - ميزان المراجعة الشجري الهرمي (Hierarchical Trial Balance)
    - قائمة الدخل / الأرباح والخسائر الشجرية (Profit and Loss Statement)
    - الميزانية العمومية وقائمة المركز المالي الشجرية (Balance Sheet)
    - دعم التوسيع والضم التلقائي واليدوي لجميع مستويات الحسابات
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _build_account_tree(accounts_qs, gl_qs):
        import collections
        accounts = list(accounts_qs.order_by('account_number'))
        account_map = {acc.id: acc for acc in accounts}
        children_map = collections.defaultdict(list)
        for acc in accounts:
            if acc.parent_id and acc.parent_id in account_map:
                children_map[acc.parent_id].append(acc.id)

        agg = gl_qs.values('account_id').annotate(d=Sum('debit'), c=Sum('credit'))
        leaf_debits = {row['account_id']: (row['d'] or decimal.Decimal('0.00')) for row in agg}
        leaf_credits = {row['account_id']: (row['c'] or decimal.Decimal('0.00')) for row in agg}

        # حساب المجاميع التراكمية للمجموعات والأصول والفروع (Rollup)
        memo = {}
        def get_rollup(acc_id):
            if acc_id in memo:
                return memo[acc_id]
            d = leaf_debits.get(acc_id, decimal.Decimal('0.00'))
            c = leaf_credits.get(acc_id, decimal.Decimal('0.00'))
            for child_id in children_map.get(acc_id, []):
                cd, cc = get_rollup(child_id)
                d += cd
                c += cc
            memo[acc_id] = (d, c)
            return d, c

        rows = []
        for acc in accounts:
            d, c = get_rollup(acc.id)
            rows.append({
                'account_id': acc.id,
                'parent_id': acc.parent_id,
                'is_group': acc.is_group,
                'account_number': acc.account_number,
                'account_name': acc.account_name,
                'root_type': acc.root_type,
                'account_type': acc.account_type,
                'currency': acc.currency or 'SAR',
                'has_children': len(children_map.get(acc.id, [])) > 0,
                'children_count': len(children_map.get(acc.id, [])),
                'debit': float(d),
                'credit': float(c),
                'net': float(d - c)
            })

        total_debit = sum(leaf_debits.values(), decimal.Decimal('0.00'))
        total_credit = sum(leaf_credits.values(), decimal.Decimal('0.00'))

        return rows, total_debit, total_credit

    @action(detail=False, methods=['get'], url_path='trial-balance')
    def trial_balance(self, request):
        opco_id = get_request_opco_id(request)
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date', datetime.date.today().isoformat())

        accounts_qs = Account.objects.all()
        if opco_id:
            accounts_qs = accounts_qs.filter(opco_id=opco_id)

        gl_qs = GLEntry.objects.filter(is_cancelled=False)
        if opco_id:
            gl_qs = gl_qs.filter(opco_id=opco_id)
        if from_date:
            gl_qs = gl_qs.filter(posting_date__gte=from_date)
        if to_date:
            gl_qs = gl_qs.filter(posting_date__lte=to_date)

        rows, total_debit, total_credit = self._build_account_tree(accounts_qs, gl_qs)

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
        opco_id = get_request_opco_id(request)
        from_date = request.query_params.get('from_date')
        to_date = request.query_params.get('to_date', datetime.date.today().isoformat())

        accounts_qs = Account.objects.filter(root_type__in=['INCOME', 'EXPENSE'])
        if opco_id:
            accounts_qs = accounts_qs.filter(opco_id=opco_id)

        gl_qs = GLEntry.objects.filter(is_cancelled=False)
        if opco_id:
            gl_qs = gl_qs.filter(opco_id=opco_id)
        if from_date:
            gl_qs = gl_qs.filter(posting_date__gte=from_date)
        if to_date:
            gl_qs = gl_qs.filter(posting_date__lte=to_date)

        rows, _, _ = self._build_account_tree(accounts_qs, gl_qs)

        # حساب الإيرادات والمصروفات وصافي الربح
        total_income = sum(r['credit'] - r['debit'] for r in rows if r['root_type'] == 'INCOME' and not r['has_children'])
        total_expenses = sum(r['debit'] - r['credit'] for r in rows if r['root_type'] == 'EXPENSE' and not r['has_children'])
        net_profit = total_income - total_expenses

        return Response({
            'from_date': from_date,
            'to_date': to_date,
            'total_income': float(total_income),
            'total_expenses': float(total_expenses),
            'net_profit': float(net_profit),
            'rows': rows
        })

    @action(detail=False, methods=['get'], url_path='balance-sheet')
    def balance_sheet(self, request):
        opco_id = get_request_opco_id(request)
        as_of_date = request.query_params.get('as_of_date', datetime.date.today().isoformat())

        accounts_qs = Account.objects.filter(root_type__in=['ASSET', 'LIABILITY', 'EQUITY'])
        if opco_id:
            accounts_qs = accounts_qs.filter(opco_id=opco_id)

        gl_qs = GLEntry.objects.filter(is_cancelled=False, posting_date__lte=as_of_date)
        if opco_id:
            gl_qs = gl_qs.filter(opco_id=opco_id)

        rows, _, _ = self._build_account_tree(accounts_qs, gl_qs)

        total_assets = sum(r['debit'] - r['credit'] for r in rows if r['root_type'] == 'ASSET' and not r['has_children'])
        total_liabilities = sum(r['credit'] - r['debit'] for r in rows if r['root_type'] == 'LIABILITY' and not r['has_children'])
        total_equity = sum(r['credit'] - r['debit'] for r in rows if r['root_type'] == 'EQUITY' and not r['has_children'])

        # أرباح الفترة
        pnl_accs = Account.objects.filter(root_type__in=['INCOME', 'EXPENSE'])
        if opco_id:
            pnl_accs = pnl_accs.filter(opco_id=opco_id)
        pnl_rows, _, _ = self._build_account_tree(pnl_accs, gl_qs)
        inc = sum(r['credit'] - r['debit'] for r in pnl_rows if r['root_type'] == 'INCOME' and not r['has_children'])
        exp = sum(r['debit'] - r['credit'] for r in pnl_rows if r['root_type'] == 'EXPENSE' and not r['has_children'])
        period_profit = inc - exp

        total_equity_with_profit = total_equity + period_profit
        is_balanced = abs(total_assets - (total_liabilities + total_equity_with_profit)) < 0.01

        return Response({
            'as_of_date': as_of_date,
            'total_assets': float(total_assets),
            'total_liabilities': float(total_liabilities),
            'total_equity': float(total_equity_with_profit),
            'period_profit': float(period_profit),
            'is_balanced': is_balanced,
            'rows': rows
        })

