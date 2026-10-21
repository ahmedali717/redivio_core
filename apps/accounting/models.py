import datetime
import decimal
from django.db import models, transaction
from django.conf import settings
from django.utils import timezone


class Account(models.Model):
    """
    شجرة الحسابات (Chart of Accounts)
    بنية شجرية متعددة المستويات مستوحاة من ERPNext لدعم المعايير المحاسبية المزدوجة.
    """
    ROOT_TYPE_CHOICES = [
        ('ASSET', 'أصول (Asset)'),
        ('LIABILITY', 'التزامات (Liability)'),
        ('EQUITY', 'حقوق ملكية (Equity)'),
        ('INCOME', 'إيرادات (Income)'),
        ('EXPENSE', 'مصروفات (Expense)')
    ]

    ACCOUNT_TYPE_CHOICES = [
        ('ACCUMULATED_DEPRECIATION', 'مجمع إهلاك (Accumulated Depreciation)'),
        ('BANK', 'بنك (Bank)'),
        ('CASH', 'خزينة ونقدية (Cash)'),
        ('RECEIVABLE', 'عملاء ومدينون (Accounts Receivable)'),
        ('PAYABLE', 'موردون ودائنون (Accounts Payable)'),
        ('COST_OF_GOODS_SOLD', 'تكلفة بضاعة مباعة (COGS)'),
        ('EQUITY', 'رأس مال وحقوق ملكية (Equity)'),
        ('EXPENSE_ACCOUNT', 'حساب مصروفات (Expense)'),
        ('INCOME_ACCOUNT', 'حساب إيرادات (Income)'),
        ('FIXED_ASSET', 'أصول ثابتة (Fixed Asset)'),
        ('STOCK', 'مخزون بضاعة (Stock In Hand)'),
        ('TAX', 'ضرائب وقيمة مضافة (Tax / VAT)'),
        ('ROUND_OFF', 'فروق تقريب (Round Off)'),
        ('OTHER', 'أخرى (Other)')
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='accounts', verbose_name="الشركة التابعة")
    account_number = models.CharField(max_length=50, verbose_name="رقم الحساب / الكود")
    account_name = models.CharField(max_length=200, verbose_name="اسم الحساب")
    root_type = models.CharField(max_length=20, choices=ROOT_TYPE_CHOICES, verbose_name="النوع الرئيسي")
    account_type = models.CharField(max_length=30, choices=ACCOUNT_TYPE_CHOICES, default='OTHER', verbose_name="نوع الحساب التفصيلي")
    
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name="الحساب الأب")
    is_group = models.BooleanField(default=False, verbose_name="مجلد رئيسي (حساب تجميعي لا يقبل قيود مباشرة)")
    currency = models.CharField(max_length=10, default='SAR', verbose_name="العملة")
    
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="الرصيد الدفتري الحالي")
    is_active = models.BooleanField(default=True, verbose_name="نشط")
    
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="حقول مخصصة (Custom Fields)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['account_number']
        unique_together = ('opco', 'account_number')
        verbose_name = "حساب مالي"
        verbose_name_plural = "دليل الحسابات (Chart of Accounts)"

    def __str__(self):
        return f"{self.account_number} - {self.account_name}"

    def recalculate_balance(self):
        """إعادة حساب الرصيد بدقة من دفتر الأستاذ العام GL Entries"""
        if self.is_group:
            total = sum(child.recalculate_balance() for child in self.children.all())
            self.balance = total
            self.save(update_fields=['balance'])
            return total

        gl_sums = self.gl_entries.filter(is_cancelled=False).aggregate(
            total_debit=models.Sum('debit'),
            total_credit=models.Sum('credit')
        )
        debit = gl_sums['total_debit'] or decimal.Decimal('0.00')
        credit = gl_sums['total_credit'] or decimal.Decimal('0.00')

        # طبيعة الحساب: الأصول والمصروفات طبيعتها مدينة، الباقي دائن
        if self.root_type in ['ASSET', 'EXPENSE']:
            self.balance = debit - credit
        else:
            self.balance = credit - debit

        self.save(update_fields=['balance'])
        return self.balance


class CostCenter(models.Model):
    """مراكز التكلفة (Cost Centers) لتوزيع الأعباء المالية والمشاريع"""
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='cost_centers')
    cost_center_name = models.CharField(max_length=150, verbose_name="اسم مركز التكلفة")
    code = models.CharField(max_length=50, blank=True, verbose_name="كود مركز التكلفة")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_group = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    extra_data = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "مركز تكلفة"
        verbose_name_plural = "مراكز التكلفة (Cost Centers)"

    def __str__(self):
        return f"{self.code or ''} {self.cost_center_name}".strip()


class JournalEntry(models.Model):
    """
    سند القيد اليومي (Journal Entry)
    قيد محاسبي مزدوج يدعم التدقيق والتوجيه على مستوى الأستاذ العام.
    """
    ENTRY_TYPE_CHOICES = [
        ('JOURNAL_ENTRY', 'قيد يومية عام (Journal Entry)'),
        ('BANK_ENTRY', 'قيد بنكي (Bank Entry)'),
        ('CASH_ENTRY', 'قيد نقدي (Cash Entry)'),
        ('OPENING_ENTRY', 'قيد افتتاحي (Opening Entry)'),
        ('CREDIT_NOTE', 'إشعار دائن (Credit Note)'),
        ('DEBIT_NOTE', 'إشعار مدين (Debit Note)')
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'مسودة (Draft)'),
        ('SUBMITTED', 'معتمد ومرحل (Submitted)'),
        ('CANCELLED', 'ملغى (Cancelled)')
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='journal_entries')
    entry_number = models.CharField(max_length=50, unique=True, verbose_name="رقم سند القيد")
    posting_date = models.DateField(default=datetime.date.today, verbose_name="تاريخ القيد / الترحيل")
    entry_type = models.CharField(max_length=30, choices=ENTRY_TYPE_CHOICES, default='JOURNAL_ENTRY', verbose_name="نوع القيد")
    
    total_debit = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="إجمالي المدين")
    total_credit = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="إجمالي الدائن")
    difference = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="الفرق (يجب أن يكون 0 للترحيل)")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="الحالة")
    docstatus = models.IntegerField(default=0, verbose_name="حالة الوثيقة ERPNext (0:مسودة، 1:معتمد، 2:ملغى)")
    
    reference_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم المرجع الخارجي / الشيك")
    user_remark = models.TextField(blank=True, null=True, verbose_name="البيان / شرح القيد")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="المستخدم المنشئ")
    
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="حقول مخصصة (Custom Fields)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-posting_date', '-id']
        verbose_name = "سند قيد يومي"
        verbose_name_plural = "سندات القيود اليومية (Journal Entries)"

    def __str__(self):
        return f"{self.entry_number} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            year = datetime.date.today().year
            last_entry = JournalEntry.objects.filter(entry_number__startswith=f"JV-{year}").order_by('id').last()
            if last_entry:
                try:
                    num = int(last_entry.entry_number.split('-')[-1]) + 1
                except (IndexError, ValueError):
                    num = 1
            else:
                num = 1
            self.entry_number = f"JV-{year}-{num:05d}"
        super().save(*args, **kwargs)

    def validate_and_compute_totals(self):
        lines = self.lines.all()
        total_d = sum(line.debit for line in lines)
        total_c = sum(line.credit for line in lines)
        self.total_debit = total_d
        self.total_credit = total_c
        self.difference = total_d - total_c
        self.save(update_fields=['total_debit', 'total_credit', 'difference'])
        return self.difference == 0

    def submit_and_post(self):
        """اعتماد وترحيل سند القيد إلى دفتر الأستاذ العام GL Entry"""
        if self.status == 'SUBMITTED':
            return
        
        self.validate_and_compute_totals()
        if abs(self.difference) > decimal.Decimal('0.01'):
            raise ValueError(f"لا يمكن ترحيل القيد! القيد غير متوازن: المدين ({self.total_debit}) لا يساوي الدائن ({self.total_credit}).")

        if self.lines.count() < 2:
            raise ValueError("القيد المحاسبي يجب أن يحتوي على سطرين على الأقل.")

        with transaction.atomic():
            for line in self.lines.all():
                GLEntry.objects.create(
                    opco=self.opco,
                    posting_date=self.posting_date,
                    account=line.account,
                    party_type=line.party_type,
                    party_id=line.party_id,
                    party_name=line.party_name,
                    debit=line.debit,
                    credit=line.credit,
                    voucher_type='Journal Entry',
                    voucher_no=self.entry_number,
                    cost_center=line.cost_center,
                    remarks=line.remark or self.user_remark or f"Journal Entry {self.entry_number}"
                )
                line.account.recalculate_balance()

            self.status = 'SUBMITTED'
            self.docstatus = 1
            self.save(update_fields=['status', 'docstatus'])

    def cancel(self):
        """إلغاء القيد وعكس أثره المالي في الأستاذ العام"""
        if self.status != 'SUBMITTED':
            self.status = 'CANCELLED'
            self.docstatus = 2
            self.save(update_fields=['status', 'docstatus'])
            return

        with transaction.atomic():
            # وسم حركات الأستاذ العام بالإلغاء
            gl_entries = GLEntry.objects.filter(voucher_type='Journal Entry', voucher_no=self.entry_number)
            for gl in gl_entries:
                gl.is_cancelled = True
                gl.save(update_fields=['is_cancelled'])
                gl.account.recalculate_balance()

            self.status = 'CANCELLED'
            self.docstatus = 2
            self.save(update_fields=['status', 'docstatus'])


class JournalEntryLine(models.Model):
    """سطر سند القيد اليومي"""
    PARTY_TYPES = [
        ('CUSTOMER', 'عميل (Customer)'),
        ('VENDOR', 'مورد (Vendor)'),
        ('EMPLOYEE', 'موظف (Employee)'),
        ('NONE', 'لا يوجد (None)')
    ]

    journal_entry = models.ForeignKey(JournalEntry, related_name='lines', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, verbose_name="الحساب")
    
    party_type = models.CharField(max_length=20, choices=PARTY_TYPES, default='NONE', verbose_name="نوع الطرف")
    party_id = models.IntegerField(null=True, blank=True, verbose_name="معرف الطرف")
    party_name = models.CharField(max_length=200, blank=True, verbose_name="اسم الطرف")
    
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="مدين (Debit)")
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="دائن (Credit)")
    
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مركز التكلفة")
    remark = models.CharField(max_length=255, blank=True, verbose_name="شرح السطر")
    extra_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.account.account_name} | D:{self.debit} C:{self.credit}"


class GLEntry(models.Model):
    """
    دفتر الأستاذ العام (General Ledger Entry)
    المرجع والمصدر الأحادي الموحد لكافة العمليات المالية واستخراج ميزان المراجعة والقوائم المالية.
    """
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='gl_entries')
    posting_date = models.DateField(verbose_name="تاريخ القيد")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='gl_entries', verbose_name="الحساب")
    
    party_type = models.CharField(max_length=50, blank=True, verbose_name="نوع الطرف")
    party_id = models.IntegerField(null=True, blank=True, verbose_name="معرف الطرف")
    party_name = models.CharField(max_length=200, blank=True, verbose_name="اسم الطرف")
    
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="مدين")
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0, verbose_name="دائن")
    
    voucher_type = models.CharField(max_length=100, verbose_name="نوع المستند / القسيمة")
    voucher_no = models.CharField(max_length=100, verbose_name="رقم المستند")
    
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="مركز التكلفة")
    remarks = models.TextField(blank=True, verbose_name="البيان")
    
    is_cancelled = models.BooleanField(default=False, verbose_name="ملغى / معكوس")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['posting_date', 'id']
        verbose_name = "حركة أستاذ عام"
        verbose_name_plural = "دفتر الأستاذ العام (General Ledger)"

    def __str__(self):
        return f"{self.posting_date} | {self.account.account_number} | D:{self.debit} C:{self.credit}"


class PurchaseInvoice(models.Model):
    """
    فاتورة شراء ومطالبة مورد (Purchase Invoice / Bill)
    مستوحاة من ERPNext لتوثيق الاستحقاقات الضريبية والتجارية للموردين.
    """
    STATUS_CHOICES = [
        ('UNPAID', 'Unpaid / غير مدفوعة'),
        ('PARTIAL', 'Partial / سداد جزئي'),
        ('PAID', 'Paid / مدفوعة بالكامل'),
        ('CANCELLED', 'Cancelled / ملغاة')
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='purchase_invoices')
    invoice_number = models.CharField(max_length=50, unique=True, verbose_name="رقم فاتورة الشراء")
    vendor = models.ForeignKey('procurement.Vendor', on_delete=models.CASCADE, related_name='purchase_invoices', verbose_name="المورد")
    purchase_order = models.ForeignKey('procurement.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices', verbose_name="أمر الشراء المرتبط")
    receipt = models.ForeignKey('procurement.StockReceipt', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="إذن الاستلام المخزني")
    
    posting_date = models.DateField(default=datetime.date.today, verbose_name="تاريخ الفاتورة")
    due_date = models.DateField(verbose_name="تاريخ الاستحقاق")
    
    currency = models.CharField(max_length=10, default='SAR', verbose_name="العملة")
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=1.0)
    
    subtotal = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="المجموع قبل الضريبة")
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="مبلغ الخصم")
    tax_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="ضريبة القيمة المضافة")
    grand_total = models.DecimalField(max_digits=15, decimal_places=2, verbose_name="الإجمالي الصافي")
    paid_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name="المدفوع")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='UNPAID')
    docstatus = models.IntegerField(default=1, verbose_name="حالة الوثيقة")
    
    credit_to_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='pi_creditors', verbose_name="حساب الموردين (الدائنون)")
    expense_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='pi_expenses', verbose_name="حساب المشتريات / المخزون (المدين)")
    
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="حقول مخصصة (Custom Fields)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posting_date', '-id']
        verbose_name = "فاتورة مشتريات"
        verbose_name_plural = "فواتير المشتريات (Purchase Invoices)"

    def __str__(self):
        return f"{self.invoice_number} - {self.vendor.name}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.invoice_number:
            year = datetime.date.today().year
            last_pi = PurchaseInvoice.objects.filter(invoice_number__startswith=f"PINV-{year}").order_by('id').last()
            num = (int(last_pi.invoice_number.split('-')[-1]) + 1) if last_pi else 1
            self.invoice_number = f"PINV-{year}-{num:05d}"

        super().save(*args, **kwargs)

        if is_new and self.status != 'CANCELLED':
            # ترحيل الأثر المالي آلياً لدفتر الأستاذ العام وزيادة رصيد مديونية المورد
            self.post_gl_entries()

    def post_gl_entries(self):
        """توليد قيود الأستاذ العام وتحديث رصيد المورد"""
        with transaction.atomic():
            # البحث عن حساب الموردين والضريبة والمشتريات التلقائية إذا لم تحدد
            creditor_acc = self.credit_to_account or Account.objects.filter(opco=self.opco, account_type='PAYABLE').first()
            expense_acc = self.expense_account or Account.objects.filter(opco=self.opco, account_type__in=['STOCK', 'EXPENSE_ACCOUNT', 'COST_OF_GOODS_SOLD']).first()
            tax_acc = Account.objects.filter(opco=self.opco, account_type='TAX').first()

            if creditor_acc and expense_acc:
                # 1. مدين: حساب المشتريات / المخزون
                GLEntry.objects.create(
                    opco=self.opco,
                    posting_date=self.posting_date,
                    account=expense_acc,
                    party_type='VENDOR',
                    party_id=self.vendor.id,
                    party_name=self.vendor.name,
                    debit=self.subtotal,
                    credit=0,
                    voucher_type='Purchase Invoice',
                    voucher_no=self.invoice_number,
                    remarks=f"Purchase from {self.vendor.name} - Inv {self.invoice_number}"
                )
                expense_acc.recalculate_balance()

                # 2. مدين: ضريبة القيمة المضافة (إن وجدت)
                if self.tax_amount > 0 and tax_acc:
                    GLEntry.objects.create(
                        opco=self.opco,
                        posting_date=self.posting_date,
                        account=tax_acc,
                        party_type='VENDOR',
                        party_id=self.vendor.id,
                        party_name=self.vendor.name,
                        debit=self.tax_amount,
                        credit=0,
                        voucher_type='Purchase Invoice',
                        voucher_no=self.invoice_number,
                        remarks=f"VAT on Purchase Inv {self.invoice_number}"
                    )
                    tax_acc.recalculate_balance()

                # 3. دائن: حساب الموردين بإجمالي الفاتورة
                GLEntry.objects.create(
                    opco=self.opco,
                    posting_date=self.posting_date,
                    account=creditor_acc,
                    party_type='VENDOR',
                    party_id=self.vendor.id,
                    party_name=self.vendor.name,
                    debit=0,
                    credit=self.grand_total,
                    voucher_type='Purchase Invoice',
                    voucher_no=self.invoice_number,
                    remarks=f"Payable to {self.vendor.name} for {self.invoice_number}"
                )
                creditor_acc.recalculate_balance()

            # تحديث رصيد المورد
            if hasattr(self.vendor, 'balance'):
                self.vendor.balance = (self.vendor.balance or 0) + self.grand_total
                self.vendor.save(update_fields=['balance'])


class PaymentEntry(models.Model):
    """
    سندات القبض والصرف الموحدة (Payment Entry)
    إدارة المقبوضات من العملاء، المدفوعات للموردين، والتحويلات الداخلية بين الصناديق والبنوك.
    """
    PAYMENT_TYPE_CHOICES = [
        ('RECEIVE', 'سند قبض من عميل (Receive)'),
        ('PAY', 'سند صرف لمورد (Pay)'),
        ('INTERNAL_TRANSFER', 'تحويل نقدية بين الحسابات (Internal Transfer)')
    ]

    PARTY_TYPE_CHOICES = [
        ('CUSTOMER', 'عميل (Customer)'),
        ('VENDOR', 'مورد (Vendor)'),
        ('NONE', 'لا يوجد (None)')
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'نقدي (Cash)'),
        ('BANK', 'تحويل بنكي (Bank Transfer)'),
        ('CHEQUE', 'شيك بنكي (Cheque)'),
        ('CARD', 'بطاقة مصرفية / مدى (Card / POS)')
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'مسودة (Draft)'),
        ('SUBMITTED', 'معتمد ومرحل (Submitted)'),
        ('CANCELLED', 'ملغى (Cancelled)')
    ]

    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE, related_name='payment_entries')
    entry_number = models.CharField(max_length=50, unique=True, verbose_name="رقم السند")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='RECEIVE', verbose_name="نوع السند")
    
    party_type = models.CharField(max_length=20, choices=PARTY_TYPE_CHOICES, default='NONE', verbose_name="نوع الطرف")
    party_id = models.IntegerField(null=True, blank=True, verbose_name="معرف الطرف")
    party_name = models.CharField(max_length=200, blank=True, verbose_name="اسم الطرف")
    
    sales_invoice = models.ForeignKey('sales.SalesInvoice', on_delete=models.SET_NULL, null=True, blank=True, related_name='accounting_payments', verbose_name="فاتورة المبيعات")
    purchase_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounting_payments', verbose_name="فاتورة المشتريات")
    
    paid_from_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='payments_from', verbose_name="الحساب المدفوع منه (الدائن)")
    paid_to_account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='payments_to', verbose_name="الحساب المستلم (المدين)")
    
    paid_amount = models.DecimalField(max_digits=18, decimal_places=2, verbose_name="المبلغ المدفوع / المحصل")
    posting_date = models.DateField(default=datetime.date.today, verbose_name="تاريخ السند")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='CASH', verbose_name="طريقة الدفع")
    reference_no = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم الحوالة / الإيصال / الشيك")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name="الحالة")
    docstatus = models.IntegerField(default=0, verbose_name="حالة الوثيقة")
    
    notes = models.TextField(blank=True, null=True, verbose_name="البيان / ملاحظات")
    extra_data = models.JSONField(default=dict, blank=True, verbose_name="حقول مخصصة (Custom Fields)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posting_date', '-id']
        verbose_name = "سند قبض / صرف"
        verbose_name_plural = "سندات القبض والصرف (Payment Entries)"

    def __str__(self):
        return f"{self.entry_number} [{self.get_payment_type_display()}] - {self.paid_amount}"

    def save(self, *args, **kwargs):
        if not self.entry_number:
            year = datetime.date.today().year
            prefix = "REC" if self.payment_type == 'RECEIVE' else ("PAY" if self.payment_type == 'PAY' else "TRF")
            last_pe = PaymentEntry.objects.filter(entry_number__startswith=f"{prefix}-{year}").order_by('id').last()
            num = (int(last_pe.entry_number.split('-')[-1]) + 1) if last_pe else 1
            self.entry_number = f"{prefix}-{year}-{num:05d}"
        super().save(*args, **kwargs)

    def submit_and_post(self):
        """اعتماد السند وترحيل الأثر المالي وتحديث الفواتير وأرصدة الأطراف"""
        if self.status == 'SUBMITTED':
            return

        with transaction.atomic():
            # 1. ترحيل الطرف المدين (الحساب المستلم: صندوق أو بنك في حالة القبض، أو مورد في حالة الصرف)
            GLEntry.objects.create(
                opco=self.opco,
                posting_date=self.posting_date,
                account=self.paid_to_account,
                party_type=self.party_type,
                party_id=self.party_id,
                party_name=self.party_name,
                debit=self.paid_amount,
                credit=0,
                voucher_type='Payment Entry',
                voucher_no=self.entry_number,
                remarks=self.notes or f"Payment {self.entry_number} ({self.get_payment_type_display()})"
            )
            self.paid_to_account.recalculate_balance()

            # 2. ترحيل الطرف الدائن (الحساب المدفوع منه: عميل في حالة القبض، أو صندوق/بنك في حالة الصرف)
            GLEntry.objects.create(
                opco=self.opco,
                posting_date=self.posting_date,
                account=self.paid_from_account,
                party_type=self.party_type,
                party_id=self.party_id,
                party_name=self.party_name,
                debit=0,
                credit=self.paid_amount,
                voucher_type='Payment Entry',
                voucher_no=self.entry_number,
                remarks=self.notes or f"Payment {self.entry_number} ({self.get_payment_type_display()})"
            )
            self.paid_from_account.recalculate_balance()

            # 3. تحديث الفواتير المرتبطة
            if self.sales_invoice:
                self.sales_invoice.paid_amount += self.paid_amount
                if self.sales_invoice.paid_amount >= self.sales_invoice.total_amount:
                    self.sales_invoice.status = 'PAID'
                elif self.sales_invoice.paid_amount > 0:
                    self.sales_invoice.status = 'PARTIAL'
                self.sales_invoice.save()

            if self.purchase_invoice:
                self.purchase_invoice.paid_amount += self.paid_amount
                if self.purchase_invoice.paid_amount >= self.purchase_invoice.grand_total:
                    self.purchase_invoice.status = 'PAID'
                elif self.purchase_invoice.paid_amount > 0:
                    self.purchase_invoice.status = 'PARTIAL'
                self.purchase_invoice.save()

            # 4. تحديث رصيد الطرف (عميل أو مورد)
            if self.payment_type == 'RECEIVE' and self.party_type == 'CUSTOMER' and self.party_id:
                from apps.sales.models import Customer
                cust = Customer.objects.filter(id=self.party_id).first()
                if cust:
                    cust.balance = (cust.balance or 0) - self.paid_amount
                    cust.save(update_fields=['balance'])

            elif self.payment_type == 'PAY' and self.party_type == 'VENDOR' and self.party_id:
                from apps.procurement.models import Vendor
                vend = Vendor.objects.filter(id=self.party_id).first()
                if vend and hasattr(vend, 'balance'):
                    vend.balance = (vend.balance or 0) - self.paid_amount
                    vend.save(update_fields=['balance'])

            self.status = 'SUBMITTED'
            self.docstatus = 1
            self.save(update_fields=['status', 'docstatus'])

    def cancel(self):
        """إلغاء السند وعكس الأثر المالي"""
        if self.status != 'SUBMITTED':
            self.status = 'CANCELLED'
            self.docstatus = 2
            self.save(update_fields=['status', 'docstatus'])
            return

        with transaction.atomic():
            gl_entries = GLEntry.objects.filter(voucher_type='Payment Entry', voucher_no=self.entry_number)
            for gl in gl_entries:
                gl.is_cancelled = True
                gl.save(update_fields=['is_cancelled'])
                gl.account.recalculate_balance()

            # عكس أثر الفواتير إن وجدت
            if self.sales_invoice:
                self.sales_invoice.paid_amount = max(0, self.sales_invoice.paid_amount - self.paid_amount)
                if self.sales_invoice.paid_amount == 0:
                    self.sales_invoice.status = 'UNPAID'
                else:
                    self.sales_invoice.status = 'PARTIAL'
                self.sales_invoice.save()

            if self.purchase_invoice:
                self.purchase_invoice.paid_amount = max(0, self.purchase_invoice.paid_amount - self.paid_amount)
                if self.purchase_invoice.paid_amount == 0:
                    self.purchase_invoice.status = 'UNPAID'
                else:
                    self.purchase_invoice.status = 'PARTIAL'
                self.purchase_invoice.save()

            self.status = 'CANCELLED'
            self.docstatus = 2
            self.save(update_fields=['status', 'docstatus'])
