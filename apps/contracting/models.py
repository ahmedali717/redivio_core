# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from decimal import Decimal

from apps.core.models import OpCo
from apps.sales.models import Customer
from apps.procurement.models import Vendor
from apps.item_master.models import Material


# ==============================================================================
# 1. المشـروع الإنشـائي (Construction / Contracting Project)
# ==============================================================================
class Project(models.Model):
    PROJECT_STATUS = [
        ('DRAFT', 'مسودة / قيد الدراسة (Draft)'),
        ('IN_PROGRESS', 'قيد التنفيذ (In Progress)'),
        ('SUSPENDED', 'متوقف مؤقتاً (Suspended)'),
        ('HANDOVER_INITIAL', 'تسليم ابتدائي (Initial Handover)'),
        ('HANDOVER_FINAL', 'تسليم نهائي وإقفال (Final Handover)'),
        ('CLOSED', 'مغلق (Closed)'),
    ]

    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='contracting_projects', verbose_name='الشركة المشغلة')
    code = models.CharField(max_length=50, unique=True, verbose_name='كود المشروع')
    name = models.CharField(max_length=255, verbose_name='اسم المشروع')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='contract_projects', verbose_name='المالك / العميل')
    
    consultant_name = models.CharField(max_length=200, blank=True, default='', verbose_name='الاستشاري المشرف')
    project_manager = models.CharField(max_length=200, blank=True, default='', verbose_name='مدير المشروع')
    site_engineer = models.CharField(max_length=200, blank=True, default='', verbose_name='مهندس الموقع')
    location_address = models.CharField(max_length=255, blank=True, default='', verbose_name='موقع المشروع / العنوان')
    
    start_date = models.DateField(default=timezone.now, verbose_name='تاريخ البدء المخطط')
    end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الانتهاء المخطط')
    actual_completion_date = models.DateField(null=True, blank=True, verbose_name='تاريخ الإنجاز الفعلي')
    
    contract_value = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='قيمة العقد الإجمالية')
    estimated_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='التكلفة التقديرية')
    actual_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='المنصرف الفعلي')
    
    progress_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='نسبة الإنجاز الفعلية %')
    status = models.CharField(max_length=20, choices=PROJECT_STATUS, default='IN_PROGRESS', verbose_name='حالة المشروع')
    
    cost_center = models.ForeignKey(
        'accounting.CostCenter', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='contract_projects', verbose_name='مركز التكلفة المحاسبي'
    )
    
    notes = models.TextField(blank=True, default='', verbose_name='ملاحظات عامة')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracting_projects'
        verbose_name = 'مشروع إنشائي'
        verbose_name_plural = 'المشاريع الإنشائية'
        ordering = ['-id']

    def __str__(self):
        return f"{self.code} - {self.name}"


# ==============================================================================
# 2. عقد المقاولة (Job Contract)
# ==============================================================================
class JobContract(models.Model):
    CONTRACT_TYPES = [
        ('MAIN', 'عقد رئيسي مع المالك (Main Contract)'),
        ('SUBCONTRACT', 'عقد مقاولة باطن (Subcontract)'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'مسودة (Draft)'),
        ('ACTIVE', 'ساري / معتمد (Active)'),
        ('COMPLETED', 'مكتمل (Completed)'),
        ('TERMINATED', 'مفسوخ (Terminated)'),
    ]

    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='job_contracts', verbose_name='الشركة المشغلة')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='contracts', verbose_name='المشروع المرتبط')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPES, default='MAIN', verbose_name='نوع العقد')
    
    contract_number = models.CharField(max_length=100, unique=True, verbose_name='رقم العقد')
    title = models.CharField(max_length=255, verbose_name='عنوان / موضوع العقد')
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='job_contracts', verbose_name='المالك / العميل')
    subcontractor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='subcontracts', verbose_name='مقاول الباطن')
    
    contract_date = models.DateField(default=timezone.now, verbose_name='تاريخ توقيع العقد')
    start_date = models.DateField(default=timezone.now, verbose_name='تاريخ سريان العقد')
    end_date = models.DateField(null=True, blank=True, verbose_name='تاريخ نهاية العقد')
    
    total_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='قيمة العقد التعاقدية')

    # الشروط التعاقدية والتأمينات والضمانات (Contract Terms & Guarantees)
    advance_payment_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='نسبة الدفعة المقدمة %')
    advance_payment_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='قيمة الدفعة المقدمة')
    advance_deduction_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'), verbose_name='نسبة استقطاع الدفعة المقدمة من المستخلصات %')
    
    retention_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'), verbose_name='نسبة استقطاع ضمان وحسن تنفيذ الأعمال (Retention) %')
    primary_insurance_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='التأمين الابتدائي (Bid Bond)')
    final_insurance_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='التأمين النهائي (Performance Bond)')
    
    penalty_per_day = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='غرامة التأخير اليومية')
    max_penalty_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('10.00'), verbose_name='الحد الأقصى لغرامات التأخير %')
    warranty_period_months = models.PositiveIntegerField(default=12, verbose_name='مدة الضمان والصيانة (شهور)')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE', verbose_name='حالة العقد')
    notes = models.TextField(blank=True, default='', verbose_name='الشروط الخاصة والملاحظات')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracting_job_contracts'
        verbose_name = 'عقد مقاولة'
        verbose_name_plural = 'عقود المقاولات'
        ordering = ['-id']

    def __str__(self):
        return f"{self.contract_number} - {self.title}"


# ==============================================================================
# 3. ملاحق العقود وأوامر التغيير (Contract Extension & Variation Orders)
# ==============================================================================
class ContractExtension(models.Model):
    EXTENSION_TYPES = [
        ('VARIATION_ORDER', 'أمر تغيير كميات / أسعار (Variation Order)'),
        ('TIME_EXTENSION', 'تمديد زمني فقط (Time Extension)'),
        ('BOTH', 'أمر تغيير مالي وتمديد زمني (Both)'),
    ]

    contract = models.ForeignKey(JobContract, on_delete=models.CASCADE, related_name='extensions', verbose_name='عقد المقاولة')
    extension_number = models.CharField(max_length=50, verbose_name='رقم الملحق / أمر التغيير')
    extension_type = models.CharField(max_length=30, choices=EXTENSION_TYPES, default='VARIATION_ORDER', verbose_name='نوع الملحق')
    
    additional_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='القيمة المالية الإضافية (+ أو -)')
    additional_days = models.IntegerField(default=0, verbose_name='الأيام المضافة للمدة')
    
    issue_date = models.DateField(default=timezone.now, verbose_name='تاريخ أمر التغيير')
    approved_by = models.CharField(max_length=150, blank=True, default='', verbose_name='الجهة أو الشخص المعتمد')
    reason = models.TextField(verbose_name='سبب التعديل / تفاصيل الأعمال الإضافية')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contracting_contract_extensions'
        verbose_name = 'ملحق عقد / أمر تغيير'
        verbose_name_plural = 'ملاحق العقود وأوامر التغيير'
        ordering = ['-id']

    def __str__(self):
        return f"{self.contract.contract_number} - {self.extension_number}"


# ==============================================================================
# 4. مقايسة المشروع وبطاقة تكلفة العملية (Job Cost Sheet / BOQ Master)
# ==============================================================================
class JobCostSheet(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة (Draft)'),
        ('SUBMITTED', 'مقدمة للمراجعة (Submitted)'),
        ('APPROVED', 'معتمدة للتشغيل (Approved)'),
        ('REVISED', 'معدلة (Revised)'),
    ]

    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='job_cost_sheets', verbose_name='الشركة المشغلة')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='cost_sheets', verbose_name='المشروع')
    contract = models.ForeignKey(JobContract, on_delete=models.SET_NULL, null=True, blank=True, related_name='cost_sheets', verbose_name='العقد المرتبط')
    
    code = models.CharField(max_length=50, unique=True, verbose_name='كود المقايسة')
    title = models.CharField(max_length=255, verbose_name='عنوان المقايسة / بطاقة التكلفة')
    
    # التكاليف التقديرية الإجمالية
    estimated_material_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='تكلفة المواد التقديرية')
    estimated_labor_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='تكلفة العمالة التقديرية')
    estimated_subcontract_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='تكلفة مقاولي الباطن التقديرية')
    estimated_overhead_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='المصاريف الإدارية والمعدات التقديرية')
    estimated_total_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي التكلفة المقدرة')
    
    contract_selling_price = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='سعر البيع التعاقدي الإجمالي')
    expected_profit_margin = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='هامش الربح المتوقع %')

    # التكاليف الفعلية المتراكمة (Actuals)
    actual_material_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='المنصرف الفعلي مواد')
    actual_labor_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='المنصرف الفعلي عمالة')
    actual_subcontract_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='المنصرف الفعلي مقاولو باطن')
    actual_overhead_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='المنصرف الفعلي مصاريف ومعدات')
    actual_total_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي المنصرف الفعلي')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name='حالة المقايسة')
    notes = models.TextField(blank=True, default='', verbose_name='ملاحظات')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracting_job_cost_sheets'
        verbose_name = 'بطاقة تكلفة عملية / مقايسة'
        verbose_name_plural = 'بطاقات التكلفة والمقايسات (BOQ)'
        ordering = ['-id']

    def __str__(self):
        return f"{self.code} - {self.title}"


# ==============================================================================
# 5. بنود المقايسة والتكلفة (Job Cost Line / BOQ Line Item)
# ==============================================================================
class JobCostLine(models.Model):
    ITEM_TYPES = [
        ('MATERIAL', 'خامات ومواد (Material)'),
        ('LABOR', 'عمالة وتشغيل (Labour)'),
        ('SUBCONTRACT', 'مقاولة باطن (Subcontractor)'),
        ('OVERHEAD', 'مصاريف ومعدات (Overhead & Equipment)'),
    ]

    cost_sheet = models.ForeignKey(JobCostSheet, on_delete=models.CASCADE, related_name='lines', verbose_name='المقايسة')
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES, default='MATERIAL', verbose_name='نوع البند')
    item_code = models.CharField(max_length=50, verbose_name='كود / رقم البند بالمقايسة')
    description = models.CharField(max_length=500, verbose_name='وصف البند والمواصفات')
    
    material = models.ForeignKey(Material, on_delete=models.SET_NULL, null=True, blank=True, related_name='boq_lines', verbose_name='الخامة المخزنية المرتبطة')
    subcontractor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='subcontract_boq_lines', verbose_name='مقاول الباطن المسند إليه')
    
    uom = models.CharField(max_length=20, default='M2', verbose_name='وحدة القياس')
    estimated_qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('1.000'), verbose_name='الكمية المقدرة')
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), verbose_name='تكلفة الوحدة المقدرة')
    total_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي التكلفة المقدرة')
    
    unit_selling_price = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), verbose_name='سعر البيع التعاقدي للوحدة')
    total_selling_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي قيمة البند التعاقدية')

    # المنفذ الفعلي
    actual_qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('0.000'), verbose_name='الكمية المنفذة فعلياً')
    actual_cost = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='المنصرف الفعلي')

    class Meta:
        db_table = 'contracting_job_cost_lines'
        verbose_name = 'بند مقايسة وتكلفة'
        verbose_name_plural = 'بنود المقايسة والتكلفة'
        ordering = ['id']

    def __str__(self):
        return f"{self.item_code}: {self.description[:40]}"


# ==============================================================================
# 6. حصر الكميات الموقعية الفعلي (Quantity Survey / QS)
# ==============================================================================
class QuantitySurvey(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'مسودة حصر (Draft)'),
        ('SUBMITTED', 'مقدم للاستشاري (Submitted)'),
        ('APPROVED', 'معتمد موقعياً (Approved)'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='quantity_surveys', verbose_name='المشروع')
    cost_line = models.ForeignKey(JobCostLine, on_delete=models.CASCADE, related_name='quantity_surveys', verbose_name='بند المقايسة')
    survey_date = models.DateField(default=timezone.now, verbose_name='تاريخ الحصر')
    surveyor_name = models.CharField(max_length=150, verbose_name='مهندس الحصر')
    
    previous_qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('0.000'), verbose_name='الكمية السابقة المنفذة')
    current_qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('0.000'), verbose_name='الكمية المنفذة في هذه الفترة')
    cumulative_qty = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal('0.000'), verbose_name='إجمالي الكمية التراكمية')
    
    completion_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), verbose_name='نسبة الإنجاز للبند %')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='APPROVED', verbose_name='حالة الحصر')
    remarks = models.TextField(blank=True, default='', verbose_name='ملاحظات وموقع الأعمال المنفذة')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'contracting_quantity_surveys'
        verbose_name = 'حصر كميات موقعي'
        verbose_name_plural = 'سجلات حصر الكميات (QS)'
        ordering = ['-id']

    def __str__(self):
        return f"{self.project.code} - {self.cost_line.item_code} ({self.survey_date})"


# ==============================================================================
# 7. المستخلصـات الجـارية والختـامية (Contract Abstracts / Progress Billings)
# ==============================================================================
class ContractAbstract(models.Model):
    ABSTRACT_TYPES = [
        ('CLIENT', 'مستخلص عميل / مالك (Client Valuation)'),
        ('SUBCONTRACTOR', 'مستخلص مقاول باطن (Subcontractor Progress)'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'مسودة مستخلص (Draft)'),
        ('SUBMITTED', 'مقدم للاستشاري (Submitted)'),
        ('APPROVED', 'معتمد من الاستشاري (Approved)'),
        ('INVOICED', 'مرحل للمحاسبة (Invoiced)'),
        ('PAID', 'مصروف / مدفوع (Paid)'),
    ]

    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='contract_abstracts', verbose_name='الشركة المشغلة')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='abstracts', verbose_name='المشروع')
    contract = models.ForeignKey(JobContract, on_delete=models.CASCADE, related_name='abstracts', verbose_name='العقد المرتبط')
    abstract_type = models.CharField(max_length=20, choices=ABSTRACT_TYPES, default='CLIENT', verbose_name='نوع المستخلص')
    
    abstract_number = models.CharField(max_length=50, verbose_name='رقم المستخلص (مثال: جاري 01)')
    is_final = models.BooleanField(default=False, verbose_name='مستخلص ختامي نهائي')
    
    date = models.DateField(default=timezone.now, verbose_name='تاريخ تحرير المستخلص')
    period_from = models.DateField(null=True, blank=True, verbose_name='عن الفترة من')
    period_to = models.DateField(null=True, blank=True, verbose_name='إلى تاريخ')

    # المبالغ والحسابات
    current_work_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='قيمة الأعمال المنفذة في هذه الفترة')
    cumulative_work_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي الأعمال المنفذة تراكمياً')
    previous_work_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='ما تم صرفه في المستخلصات السابقة')
    
    advance_deduction = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='استقطاع استهلاك الدفعة المقدمة')
    retention_deduction = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='استقطاع ضمان الأعمال (Retention)')
    other_deductions = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='استقطاعات وجزاءات أخرى')
    
    vat_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='ضريبة القيمة المضافة (VAT)')
    net_payable_amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='صافي المستحق للصرف')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', verbose_name='حالة المستخلص')
    notes = models.TextField(blank=True, default='', verbose_name='ملاحظات وتفاصيل الاستقطاعات')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracting_abstracts'
        verbose_name = 'مستخلص مقاولات'
        verbose_name_plural = 'المستخلصات الجارية والختامية'
        ordering = ['-id']

    def __str__(self):
        return f"{self.project.code} - {self.abstract_number}"


# ==============================================================================
# 8. إدارة الشيكات وأوراق القبض والدفع (Check / Commercial Paper Management)
# ==============================================================================
class CheckTransaction(models.Model):
    CHECK_TYPES = [
        ('RECEIVABLE', 'شيك قبض وارد (Receivable Check)'),
        ('PAYABLE', 'شيك دفع صادر (Payable Check)'),
    ]

    CHECK_STATUS = [
        ('HELD', 'في الخزينة / تحت اليد (In Treasury)'),
        ('DEPOSITED', 'مُودع بالبنك برسم التحصيل (Under Collection)'),
        ('COLLECTED', 'تم التحصيل والصرف (Collected)'),
        ('BOUNCED', 'مرتد / مرفوض من البنك (Bounced)'),
        ('ENDORSED', 'مُظَهّر لطرف ثالث (Endorsed)'),
        ('CANCELLED', 'ملغي (Cancelled)'),
    ]

    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='check_transactions', verbose_name='الشركة المشغلة')
    check_type = models.CharField(max_length=20, choices=CHECK_TYPES, default='RECEIVABLE', verbose_name='نوع الشيك')
    
    check_number = models.CharField(max_length=100, verbose_name='رقم الشيك')
    bank_name = models.CharField(max_length=150, verbose_name='اسم البنك المسحوب عليه')
    branch = models.CharField(max_length=100, blank=True, default='', verbose_name='الفرع')
    
    amount = models.DecimalField(max_digits=16, decimal_places=2, default=Decimal('0.00'), verbose_name='مبلغ الشيك')
    currency = models.CharField(max_length=10, default='SAR', verbose_name='العملة')
    
    issue_date = models.DateField(default=timezone.now, verbose_name='تاريخ تحرير الشيك')
    due_date = models.DateField(verbose_name='تاريخ استحقاق الشيك')
    
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='checks', verbose_name='المشروع المرتبط')
    party_name = models.CharField(max_length=200, verbose_name='الساحب / المستفيد')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='checks', verbose_name='العميل (إن وجد)')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='checks', verbose_name='المورد / مقاول الباطن')
    
    status = models.CharField(max_length=20, choices=CHECK_STATUS, default='HELD', verbose_name='حالة الشيك')
    action_date = models.DateField(null=True, blank=True, verbose_name='تاريخ آخر إجراء (تحصيل / ارتداد)')
    rejection_reason = models.CharField(max_length=255, blank=True, default='', verbose_name='سبب الارتداد / الرفض')
    notes = models.TextField(blank=True, default='', verbose_name='ملاحظات الشيك')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracting_check_transactions'
        verbose_name = 'شيك / ورقة تجارية'
        verbose_name_plural = 'إدارة الشيكات وأوراق الدفع والقبض'
        ordering = ['due_date', '-id']

    def __str__(self):
        return f"{self.get_check_type_display()} - #{self.check_number} ({self.amount} {self.currency})"


# ==============================================================================
# 9. عهد المواقع والمصروفات النثرية (Site Cash Custody)
# ==============================================================================
class SiteCustody(models.Model):
    CUSTODY_STATUS = [
        ('ACTIVE', 'عهدة نشطة ومفتوحة (Active)'),
        ('SETTLED', 'تمت التسوية والإقفال (Settled)'),
        ('REPLENISHED', 'تمت الاستعاضة (Replenished)'),
    ]

    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='site_custodies', verbose_name='الشركة المشغلة')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='custodies', verbose_name='المشروع')
    
    custody_code = models.CharField(max_length=50, unique=True, verbose_name='كود العهدة')
    custodian_name = models.CharField(max_length=150, verbose_name='المسؤول عن العهدة / مهندس الموقع')
    
    assigned_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), verbose_name='مبلغ العهدة المستلم')
    spent_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), verbose_name='إجمالي المنصرف')
    remaining_balance = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), verbose_name='الرصيد المتبقي بالعهدة')
    
    open_date = models.DateField(default=timezone.now, verbose_name='تاريخ فتح العهدة')
    settled_date = models.DateField(null=True, blank=True, verbose_name='تاريخ التسوية')
    
    status = models.CharField(max_length=20, choices=CUSTODY_STATUS, default='ACTIVE', verbose_name='حالة العهدة')
    notes = models.TextField(blank=True, default='', verbose_name='ملاحظات')

    class Meta:
        db_table = 'contracting_site_custodies'
        verbose_name = 'عهدة موقع'
        verbose_name_plural = 'عهد المواقع النثرية'
        ordering = ['-id']

    def __str__(self):
        return f"{self.custody_code} - {self.custodian_name} ({self.project.code})"


# ==============================================================================
# 10. بنود ومصروفات العهدة (Site Custody Expense Lines)
# ==============================================================================
class SiteCustodyExpense(models.Model):
    custody = models.ForeignKey(SiteCustody, on_delete=models.CASCADE, related_name='expenses', verbose_name='العهدة')
    expense_date = models.DateField(default=timezone.now, verbose_name='تاريخ الصرف')
    expense_category = models.CharField(max_length=100, verbose_name='بند الصرف (نثريات، وقود، إكراميات، بوفيه...)')
    receipt_number = models.CharField(max_length=100, blank=True, default='', verbose_name='رقم الفاتورة / الإيصال')
    description = models.CharField(max_length=255, verbose_name='بيان وتفاصيل المصروف')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), verbose_name='المبلغ المنصرف')

    class Meta:
        db_table = 'contracting_custody_expenses'
        verbose_name = 'مصروف عهدة موقع'
        verbose_name_plural = 'مصروفات العهد النثرية'
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.description} ({self.amount})"


# ==============================================================================
# 11. طلبات الصرف الموقعية (Site Payment Requests)
# ==============================================================================
class PaymentRequest(models.Model):
    BENEFICIARY_TYPES = [
        ('SUBCONTRACTOR', 'مقاول باطن (Subcontractor)'),
        ('VENDOR', 'مورد خامات (Vendor)'),
        ('LABOUR_WAGES', 'يوميات عمالة (Labor Wages)'),
        ('STAFF', 'موظف / مهندس (Staff)'),
        ('OTHER', 'جهة أخرى (Other)'),
    ]

    STATUS_CHOICES = [
        ('PENDING_ENGINEER', 'بانتظار اعتماد مهندس الموقع (Pending Engineer)'),
        ('PENDING_PM', 'بانتظار اعتماد مدير المشروع (Pending PM)'),
        ('APPROVED', 'معتمد للصرف (Approved)'),
        ('DISBURSED', 'تم الصرف (Disbursed)'),
        ('REJECTED', 'مرفوض (Rejected)'),
    ]

    opco = models.ForeignKey(OpCo, on_delete=models.CASCADE, related_name='payment_requests', verbose_name='الشركة المشغلة')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='payment_requests', verbose_name='المشروع')
    
    request_number = models.CharField(max_length=50, unique=True, verbose_name='رقم طلب الصرف')
    date = models.DateField(default=timezone.now, verbose_name='تاريخ الطلب')
    
    beneficiary_type = models.CharField(max_length=20, choices=BENEFICIARY_TYPES, default='SUBCONTRACTOR', verbose_name='نوع المستفيد')
    beneficiary_name = models.CharField(max_length=200, verbose_name='اسم المستفيد')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='site_payment_requests', verbose_name='المورد / مقاول الباطن')
    
    amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'), verbose_name='المبلغ المطلوب')
    reason = models.TextField(verbose_name='سبب ومبررات الصرف')
    payment_method = models.CharField(max_length=50, default='BANK_TRANSFER', verbose_name='طريقة الصرف المقترحة (تحويل، شيك، نقداً)')
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='PENDING_PM', verbose_name='حالة الطلب')
    approved_by = models.CharField(max_length=150, blank=True, default='', verbose_name='المعتمد')
    disbursement_reference = models.CharField(max_length=100, blank=True, default='', verbose_name='رقم الحوالة / الشيك المنصرف')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contracting_payment_requests'
        verbose_name = 'طلب صرف موقع'
        verbose_name_plural = 'طلبات الصرف الموقعية'
        ordering = ['-id']

    def __str__(self):
        return f"{self.request_number} - {self.beneficiary_name} ({self.amount})"
