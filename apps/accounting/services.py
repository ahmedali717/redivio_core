from django.db import transaction
from .models import Account, CostCenter


def seed_default_chart_of_accounts(opco, force=False):
    """
    إنشاء وتوسيع شجرة الحسابات القياسية الكاملة (Comprehensive ERPNext Standard Chart of Accounts)
    للشركة المحددة، متوافقة 100% مع معايير المحاسبة الدولية (IFRS) والأنظمة الضريبية ومعيار ERPNext.
    تحتوي على أكثر من 70 حساباً قياسياً شاملاً كافة التفرعات والمستويات.
    تستخدم get_or_create لضمان عدم تكرار الحسابات وإضافة أي حسابات ناقصة في حالة الترقية.
    """
    created_count = 0

    def add_acc(num, name, root, acc_type='OTHER', parent=None, is_group=False, currency='SAR'):
        nonlocal created_count
        acc, created = Account.objects.get_or_create(
            opco=opco,
            account_number=str(num),
            defaults={
                'account_name': name,
                'root_type': root,
                'account_type': acc_type,
                'parent': parent,
                'is_group': is_group,
                'currency': currency,
            }
        )
        if created:
            created_count += 1
        elif parent and acc.parent_id != parent.id:
            acc.parent = parent
            acc.save(update_fields=['parent'])
        return acc

    with transaction.atomic():
        # =====================================================================
        # 1. الأصول (ASSETS) - 1000
        # =====================================================================
        assets = add_acc('1000', 'الأصول (Application of Funds / Assets)', 'ASSET', 'OTHER', is_group=True)

        # 1.1 الأصول المتداولة (Current Assets) - 1100
        curr_assets = add_acc('1100', 'الأصول المتداولة (Current Assets)', 'ASSET', 'OTHER', parent=assets, is_group=True)

        # 1.1.1 النقد وما يعادله
        cash_group = add_acc('1110', 'النقد وما في حكمه (Cash & Bank Equivalents)', 'ASSET', 'OTHER', parent=curr_assets, is_group=True)
        add_acc('1111', 'الخزينة الرئيسية (Main Cashbox)', 'ASSET', 'CASH', parent=cash_group, is_group=False)
        add_acc('1112', 'عهد الخزائن الفرعية والمصروفات النثرية (Petty Cash)', 'ASSET', 'CASH', parent=cash_group, is_group=False)
        add_acc('1113', 'نقدية صناديق ونقاط البيع (POS Till Cash)', 'ASSET', 'CASH', parent=cash_group, is_group=False)
        add_acc('1121', 'حساب البنك الجاري الرئيسي (Main Bank Current Account)', 'ASSET', 'BANK', parent=cash_group, is_group=False)
        add_acc('1122', 'حساب بنكي ثانوي / ادخار (Secondary Bank Account)', 'ASSET', 'BANK', parent=cash_group, is_group=False)
        add_acc('1125', 'شيكات برسم التحصيل (Cheques in Hand / Collection)', 'ASSET', 'BANK', parent=cash_group, is_group=False)

        # 1.1.2 المدينون والعملاء
        ar_group = add_acc('1130', 'العملاء والمدينون (Accounts Receivable - Debtors)', 'ASSET', 'OTHER', parent=curr_assets, is_group=True)
        add_acc('1131', 'مديونيات العملاء التجاريين (Trade Debtors / Receivables)', 'ASSET', 'RECEIVABLE', parent=ar_group, is_group=False)
        add_acc('1132', 'شيكات مرتدة برسم التحصيل (Bounced Cheques Receivable)', 'ASSET', 'RECEIVABLE', parent=ar_group, is_group=False)

        # 1.1.3 سلف وعهد ومصروفات مقدمة
        adv_group = add_acc('1140', 'سلف وعهد وأرصدة مدينة أخرى (Loans, Advances & Prepayments)', 'ASSET', 'OTHER', parent=curr_assets, is_group=True)
        add_acc('1141', 'عهد وسلف الموظفين النقدية (Employee Advances & Loans)', 'ASSET', 'OTHER', parent=adv_group, is_group=False)
        add_acc('1142', 'دفعات وعرابين مقدمة للموردين (Advances Paid to Vendors)', 'ASSET', 'OTHER', parent=adv_group, is_group=False)
        add_acc('1143', 'تأمينات مستردة لدى الغير (Security Deposits Given)', 'ASSET', 'OTHER', parent=adv_group, is_group=False)
        add_acc('1144', 'مصروفات مدفوعة مقدماً (Prepaid Expenses)', 'ASSET', 'OTHER', parent=adv_group, is_group=False)
        add_acc('1145', 'إيرادات مستحقة غير مقبوضة (Accrued Income)', 'ASSET', 'OTHER', parent=adv_group, is_group=False)

        # 1.1.4 المخزون والبضاعة
        stock_group = add_acc('1150', 'أصول المخزون والبضاعة (Stock & Inventory Assets)', 'ASSET', 'OTHER', parent=curr_assets, is_group=True)
        add_acc('1151', 'مخزون البضاعة التامة بالمستودعات (Stock in Hand)', 'ASSET', 'STOCK', parent=stock_group, is_group=False)
        add_acc('1152', 'بضاعة بالطريق واعتمادات مستندية (Stock in Transit / LC)', 'ASSET', 'STOCK', parent=stock_group, is_group=False)
        add_acc('1153', 'مخزون مواد أولية وخام (Raw Materials & Packaging)', 'ASSET', 'STOCK', parent=stock_group, is_group=False)
        add_acc('1154', 'إنتاج تحت التشغيل (Work in Progress)', 'ASSET', 'STOCK', parent=stock_group, is_group=False)

        # 1.1.5 الأصول الضريبية
        tax_asset_group = add_acc('1160', 'الأصول والمدفوعات الضريبية (Tax Assets)', 'ASSET', 'OTHER', parent=curr_assets, is_group=True)
        add_acc('1161', 'ضريبة القيمة المضافة للمدخلات / المشتريات (VAT Input Tax)', 'ASSET', 'TAX', parent=tax_asset_group, is_group=False)

        # 1.2 الأصول غير المتداولة والثابتة (Fixed & Non-Current Assets) - 1200
        fixed_assets = add_acc('1200', 'الأصول الثابتة وغير المتداولة (Fixed & Non-Current Assets)', 'ASSET', 'FIXED_ASSET', parent=assets, is_group=True)

        # 1.2.1 الممتلكات والإنشاءات
        prop_group = add_acc('1210', 'الممتلكات والمباني والإنشاءات (Land & Buildings)', 'ASSET', 'FIXED_ASSET', parent=fixed_assets, is_group=True)
        add_acc('1211', 'أراضي ومواقع تجارية (Freehold Land)', 'ASSET', 'FIXED_ASSET', parent=prop_group, is_group=False)
        add_acc('1212', 'مباني وعقارات إدارية وتشغيلية (Buildings)', 'ASSET', 'FIXED_ASSET', parent=prop_group, is_group=False)
        add_acc('1213', 'مشروعات وأعمال رأسمالية تحت التنفيذ (Capital Work in Progress)', 'ASSET', 'FIXED_ASSET', parent=prop_group, is_group=False)

        # 1.2.2 الآلات والمعدات والتجهيزات
        equip_group = add_acc('1220', 'الآلات والمعدات والتجهيزات (Plant, Machinery & Equipment)', 'ASSET', 'FIXED_ASSET', parent=fixed_assets, is_group=True)
        add_acc('1221', 'آلات وماكينات تشغيل ومعدات صناعية (Plant & Machinery)', 'ASSET', 'FIXED_ASSET', parent=equip_group, is_group=False)
        add_acc('1222', 'أجهزة حاسوب وأنظمة إلكترونية (IT Equipment & Computers)', 'ASSET', 'FIXED_ASSET', parent=equip_group, is_group=False)
        add_acc('1223', 'أثاث ومفروشات وتجهيزات مكتبية (Office Furniture & Fixtures)', 'ASSET', 'FIXED_ASSET', parent=equip_group, is_group=False)

        # 1.2.3 أسطول النقل والسيارات
        veh_group = add_acc('1230', 'أسطول وسائط النقل والسيارات (Vehicles & Fleet)', 'ASSET', 'FIXED_ASSET', parent=fixed_assets, is_group=True)
        add_acc('1231', 'سيارات وشاحنات نقل البضائع والخدمة (Commercial Vehicles)', 'ASSET', 'FIXED_ASSET', parent=veh_group, is_group=False)

        # 1.2.4 مجمع الإهلاك (Contra-Asset)
        dep_group = add_acc('1290', 'مجمع إهلاك الأصول الثابتة (Accumulated Depreciation)', 'ASSET', 'ACCUMULATED_DEPRECIATION', parent=fixed_assets, is_group=True)
        add_acc('1291', 'مجمع إهلاك المباني (Acc. Dep. - Buildings)', 'ASSET', 'ACCUMULATED_DEPRECIATION', parent=dep_group, is_group=False)
        add_acc('1292', 'مجمع إهلاك الآلات والمعدات (Acc. Dep. - Machinery)', 'ASSET', 'ACCUMULATED_DEPRECIATION', parent=dep_group, is_group=False)
        add_acc('1293', 'مجمع إهلاك أجهزة الحاسوب (Acc. Dep. - IT Equipment)', 'ASSET', 'ACCUMULATED_DEPRECIATION', parent=dep_group, is_group=False)
        add_acc('1294', 'مجمع إهلاك وسائط النقل (Acc. Dep. - Vehicles)', 'ASSET', 'ACCUMULATED_DEPRECIATION', parent=dep_group, is_group=False)
        add_acc('1295', 'مجمع إهلاك الأثاث والتجهيزات (Acc. Dep. - Furniture)', 'ASSET', 'ACCUMULATED_DEPRECIATION', parent=dep_group, is_group=False)

        # =====================================================================
        # 2. الالتزامات (LIABILITIES) - 2000
        # =====================================================================
        liabilities = add_acc('2000', 'الالتزامات (Source of Funds / Liabilities)', 'LIABILITY', 'OTHER', is_group=True)

        # 2.1 الالتزامات المتداولة (Current Liabilities) - 2100
        curr_liabilities = add_acc('2100', 'الالتزامات المتداولة (Current Liabilities)', 'LIABILITY', 'OTHER', parent=liabilities, is_group=True)

        # 2.1.1 الموردون والدائنون
        ap_group = add_acc('2110', 'الموردون والدائنون التجاريون (Accounts Payable - Creditors)', 'LIABILITY', 'OTHER', parent=curr_liabilities, is_group=True)
        add_acc('2111', 'الموردون التجاريون (Trade Creditors / Payables)', 'LIABILITY', 'PAYABLE', parent=ap_group, is_group=False)
        add_acc('2112', 'دائنو أوراق الدفع والشيكات الآجلة (Notes Payable)', 'LIABILITY', 'PAYABLE', parent=ap_group, is_group=False)

        # 2.1.2 الالتزامات الضريبية والحكومية
        duties_group = add_acc('2120', 'الالتزامات الضريبية والرسوم الحكومية (Duties and Taxes)', 'LIABILITY', 'OTHER', parent=curr_liabilities, is_group=True)
        add_acc('2121', 'أمانات ضريبة القيمة المضافة للمبيعات (VAT Output Tax)', 'LIABILITY', 'TAX', parent=duties_group, is_group=False)
        add_acc('2122', 'ضريبة الاستقطاع والدخل (Withholding & Income Tax)', 'LIABILITY', 'TAX', parent=duties_group, is_group=False)
        add_acc('2123', 'مستحقات التأمينات الاجتماعية (GOSI / Social Insurance Payable)', 'LIABILITY', 'PAYABLE', parent=duties_group, is_group=False)

        # 2.1.3 التزامات المخزون والبضاعة المستلمة
        stock_liab_group = add_acc('2130', 'التزامات المخزون والتوريد (Stock Liabilities)', 'LIABILITY', 'OTHER', parent=curr_liabilities, is_group=True)
        add_acc('2131', 'بضاعة مستلمة لم تفوتر بعد (Stock Received But Not Billed)', 'LIABILITY', 'PAYABLE', parent=stock_liab_group, is_group=False)

        # 2.1.4 الدفعات المقدمة من العملاء
        cust_adv_group = add_acc('2140', 'الدفعات المقدمة ومستحقات العملاء (Customer Advances)', 'LIABILITY', 'OTHER', parent=curr_liabilities, is_group=True)
        add_acc('2141', 'دفعات مقدمة وعرابين من العملاء (Customer Advances)', 'LIABILITY', 'PAYABLE', parent=cust_adv_group, is_group=False)

        # 2.1.5 المصروفات المستحقة ومستحقات العاملين
        accrued_group = add_acc('2150', 'المصروفات المستحقة ومستحقات الموظفين (Accrued Liabilities & Payroll)', 'LIABILITY', 'OTHER', parent=curr_liabilities, is_group=True)
        add_acc('2151', 'رواتب وأجور ومستحقات الموظفين (Accrued Payroll / Salaries Payable)', 'LIABILITY', 'PAYABLE', parent=accrued_group, is_group=False)
        add_acc('2152', 'مصاريف تشغيلية مستحقة غير مدفوعة (Accrued Operating Expenses)', 'LIABILITY', 'PAYABLE', parent=accrued_group, is_group=False)
        add_acc('2153', 'مخصص مكافأة نهاية الخدمة - متداول (End of Service Benefits - Current)', 'LIABILITY', 'PAYABLE', parent=accrued_group, is_group=False)

        # 2.2 الالتزامات غير المتداولة (Non-Current Liabilities) - 2200
        non_curr_liab = add_acc('2200', 'الالتزامات غير المتداولة (Non-Current Liabilities)', 'LIABILITY', 'OTHER', parent=liabilities, is_group=True)
        loan_group = add_acc('2210', 'القروض والتسهيلات البنكية طويلة الأجل (Long-Term Loans & Financing)', 'LIABILITY', 'OTHER', parent=non_curr_liab, is_group=True)
        add_acc('2211', 'قروض وتمويلات بنكية تجارية (Bank Term Loans)', 'LIABILITY', 'OTHER', parent=loan_group, is_group=False)
        add_acc('2212', 'تسهيلات سحب بنكي على المكشوف (Bank Overdraft Facilities)', 'LIABILITY', 'OTHER', parent=loan_group, is_group=False)
        prov_group = add_acc('2220', 'مخصصات والتزامات غير متداولة (Long-Term Provisions)', 'LIABILITY', 'OTHER', parent=non_curr_liab, is_group=True)
        add_acc('2221', 'مخصص منافع الموظفين ونهاية الخدمة طويل الأجل (Non-Current EOSB)', 'LIABILITY', 'OTHER', parent=prov_group, is_group=False)

        # =====================================================================
        # 3. حقوق الملكية (EQUITY) - 3000
        # =====================================================================
        equity = add_acc('3000', 'حقوق الملكية (Equity & Capital)', 'EQUITY', 'EQUITY', is_group=True)

        # 3.1 رأس المال والاحتياطيات
        cap_group = add_acc('3100', 'رأس المال والاحتياطيات (Share Capital & Reserves)', 'EQUITY', 'EQUITY', parent=equity, is_group=True)
        add_acc('3110', 'رأس المال المدفوع (Share Capital)', 'EQUITY', 'EQUITY', parent=cap_group, is_group=False)
        add_acc('3120', 'الاحتياطي النظامي والقانوني (Statutory & Legal Reserve)', 'EQUITY', 'EQUITY', parent=cap_group, is_group=False)

        # 3.2 الأرباح المبقاة والمحتجزة
        ret_group = add_acc('3200', 'الأرباح المبقاة والمحتجزة (Retained Earnings)', 'EQUITY', 'EQUITY', parent=equity, is_group=True)
        add_acc('3210', 'أرباح وخسائر مرحلة / مبقاة (Retained Earnings / Accumulated Profit)', 'EQUITY', 'EQUITY', parent=ret_group, is_group=False)
        add_acc('3220', 'أرباح وخسائر العام الجاري (Current Year Profit/Loss)', 'EQUITY', 'EQUITY', parent=ret_group, is_group=False)

        # 3.3 حسابات الشركاء والتسويات
        owner_group = add_acc('3300', 'حسابات الشركاء والتسويات الافتتاحية (Owners & Opening Balance)', 'EQUITY', 'EQUITY', parent=equity, is_group=True)
        add_acc('3310', 'جاري الشركاء / الملاك (Owners / Partners Current Account)', 'EQUITY', 'EQUITY', parent=owner_group, is_group=False)
        add_acc('3320', 'مسحوبات الشركاء (Partners Drawings)', 'EQUITY', 'EQUITY', parent=owner_group, is_group=False)
        add_acc('3330', 'رصيد افتتاحي مؤقت للتسوية (Temporary Opening Balance Equity)', 'EQUITY', 'EQUITY', parent=owner_group, is_group=False)

        # =====================================================================
        # 4. الإيرادات (INCOME) - 4000
        # =====================================================================
        income = add_acc('4000', 'الإيرادات (Income & Revenues)', 'INCOME', 'INCOME_ACCOUNT', is_group=True)

        # 4.1 إيرادات النشاط الرئيسي والمبيعات
        sales_group = add_acc('4100', 'إيرادات النشاط الرئيسي والمبيعات (Direct Income / Sales Revenue)', 'INCOME', 'INCOME_ACCOUNT', parent=income, is_group=True)
        add_acc('4110', 'مبيعات البضائع والمنتجات (Product Sales)', 'INCOME', 'INCOME_ACCOUNT', parent=sales_group, is_group=False)
        add_acc('4120', 'إيرادات الخدمات والاستشارات (Service Revenue)', 'INCOME', 'INCOME_ACCOUNT', parent=sales_group, is_group=False)
        add_acc('4130', 'مبيعات نقاط البيع والمطعم (POS Sales)', 'INCOME', 'INCOME_ACCOUNT', parent=sales_group, is_group=False)

        # 4.1.1 مردودات ومسموحات المبيعات (Contra-Income)
        sales_red_group = add_acc('4190', 'تسويات ومردودات المبيعات (Sales Reductions - Contra Income)', 'INCOME', 'INCOME_ACCOUNT', parent=sales_group, is_group=True)
        add_acc('4191', 'مردودات ومسموحات المبيعات (Sales Returns and Allowances)', 'INCOME', 'INCOME_ACCOUNT', parent=sales_red_group, is_group=False)
        add_acc('4192', 'خصم مسموح به وتخفيضات تجارية (Discount Allowed)', 'INCOME', 'INCOME_ACCOUNT', parent=sales_red_group, is_group=False)

        # 4.2 إيرادات غير تشغيلية وأخرى
        other_inc_group = add_acc('4200', 'إيرادات أخرى غير تشغيلية (Indirect & Other Income)', 'INCOME', 'INCOME_ACCOUNT', parent=income, is_group=True)
        add_acc('4210', 'أرباح وفروق العملات الأجنبية (Foreign Exchange Gain)', 'INCOME', 'INCOME_ACCOUNT', parent=other_inc_group, is_group=False)
        add_acc('4220', 'إيرادات تمويلية وعوائد استثمارات (Finance & Investment Income)', 'INCOME', 'INCOME_ACCOUNT', parent=other_inc_group, is_group=False)
        add_acc('4230', 'إيرادات رأسمالية وأرباح بيع أصول (Gain on Sale of Fixed Assets)', 'INCOME', 'INCOME_ACCOUNT', parent=other_inc_group, is_group=False)
        add_acc('4240', 'إيرادات متنوعة وأخرى (Miscellaneous Income)', 'INCOME', 'INCOME_ACCOUNT', parent=other_inc_group, is_group=False)

        # =====================================================================
        # 5. المصروفات (EXPENSES) - 5000
        # =====================================================================
        expenses = add_acc('5000', 'المصروفات (Expenses)', 'EXPENSE', 'EXPENSE_ACCOUNT', is_group=True)

        # 5.1 التكاليف والمصروفات المباشرة
        cogs_group = add_acc('5100', 'التكاليف والمصروفات المباشرة (Cost of Goods Sold - COGS)', 'EXPENSE', 'COST_OF_GOODS_SOLD', parent=expenses, is_group=True)
        add_acc('5110', 'تكلفة البضاعة المباعة (Cost of Goods Sold - COGS)', 'EXPENSE', 'COST_OF_GOODS_SOLD', parent=cogs_group, is_group=False)
        add_acc('5120', 'تكاليف شحن ونقل المشتريات والجمارك (Freight & Customs Inward)', 'EXPENSE', 'COST_OF_GOODS_SOLD', parent=cogs_group, is_group=False)
        add_acc('5130', 'تكاليف هالك وتوالف المخزون (Inventory Scrap & Losses)', 'EXPENSE', 'COST_OF_GOODS_SOLD', parent=cogs_group, is_group=False)

        # 5.2 المصروفات التشغيلية والعمومية والإدارية
        admin_group = add_acc('5200', 'المصروفات التشغيلية والعمومية والإدارية (Operating & Admin Expenses)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=expenses, is_group=True)

        # 5.2.1 تكاليف الكادر البشري والرواتب
        staff_group = add_acc('5210', 'تكاليف ورواتب الكادر البشري (Personnel & Staff Costs)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=admin_group, is_group=True)
        add_acc('5211', 'الرواتب الأساسية والبدلات (Salaries & Basic Allowances)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=staff_group, is_group=False)
        add_acc('5212', 'حصة الشركة في التأمينات الاجتماعية (GOSI Employer Contribution)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=staff_group, is_group=False)
        add_acc('5213', 'مصروف مكافأة نهاية الخدمة (End of Service Expense)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=staff_group, is_group=False)
        add_acc('5214', 'عمولات ومكافآت العاملين (Incentives & Bonuses)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=staff_group, is_group=False)
        add_acc('5215', 'تدريب وتطوير الموظفين (Training & Development)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=staff_group, is_group=False)

        # 5.2.2 مصاريف الإيجار والمرافق والصيانة
        facility_group = add_acc('5220', 'مصاريف الإيجار والمرافق والصيانة (Rent, Utilities & Maintenance)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=admin_group, is_group=True)
        add_acc('5221', 'إيجار المقرات والفروع (Rent Expense)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=facility_group, is_group=False)
        add_acc('5222', 'كهرباء، مياه، وغاز (Electricity, Water & Utilities)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=facility_group, is_group=False)
        add_acc('5223', 'اتصالات وإنترنت واشتراكات سحابية (Internet, Telecom & Software)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=facility_group, is_group=False)
        add_acc('5224', 'صيانة ونظافة وتشغيل مرافق (Facility Repairs & Cleaning)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=facility_group, is_group=False)

        # 5.2.3 مصاريف إدارية وقانونية متنوعة
        gen_group = add_acc('5230', 'مصاريف إدارية وقانونية متنوعة (General & Professional Expenses)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=admin_group, is_group=True)
        add_acc('5231', 'أتعاب محاسبية وقانونية واستشارية (Legal & Professional Fees)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=gen_group, is_group=False)
        add_acc('5232', 'مطبوعات وأدوات مكتبية وقرطاسية (Office Supplies & Printing)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=gen_group, is_group=False)
        add_acc('5233', 'رسوم وتراخيص وسجلات حكومية (Government Fees & Licenses)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=gen_group, is_group=False)
        add_acc('5234', 'تأمين الممتلكات والمسؤوليات (Commercial & Property Insurance)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=gen_group, is_group=False)

        # 5.3 المصروفات البيعية والتسويقية
        mkt_group = add_acc('5300', 'المصروفات البيعية والتسويقية (Sales & Marketing Expenses)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=expenses, is_group=True)
        add_acc('5310', 'إعلانات وحملات ترويجية ورقمية (Advertising & Digital Marketing)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=mkt_group, is_group=False)
        add_acc('5320', 'معارض وفعاليات ومؤتمرات (Exhibitions & Events)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=mkt_group, is_group=False)
        add_acc('5330', 'مصاريف ضيافة وعلاقات عامة (Hospitality & PR)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=mkt_group, is_group=False)
        add_acc('5340', 'تكاليف نقل وتوصيل البضائع للعملاء (Outward Freight & Shipping)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=mkt_group, is_group=False)

        # 5.4 مصاريف الإهلاك والاستهلاك
        dep_exp_group = add_acc('5400', 'مصاريف الإهلاك والاستهلاك (Depreciation & Amortization)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=expenses, is_group=True)
        add_acc('5410', 'إهلاك المباني والمنشآت (Depreciation - Buildings)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=dep_exp_group, is_group=False)
        add_acc('5420', 'إهلاك الآلات والمعدات (Depreciation - Machinery)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=dep_exp_group, is_group=False)
        add_acc('5430', 'إهلاك الحواسيب والأجهزة (Depreciation - IT Equipment)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=dep_exp_group, is_group=False)
        add_acc('5440', 'إهلاك أسطول وسائط النقل (Depreciation - Vehicles)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=dep_exp_group, is_group=False)
        add_acc('5450', 'إهلاك الأثاث والديكور (Depreciation - Furniture)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=dep_exp_group, is_group=False)

        # 5.5 المصروفات البنكية والتمويلية
        fin_group = add_acc('5500', 'المصروفات البنكية والتمويلية (Finance Costs & Other Expenses)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=expenses, is_group=True)
        add_acc('5510', 'عمولات ومصروفات بنكية ونقاط بيع (Bank Charges & POS Fees)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=fin_group, is_group=False)
        add_acc('5520', 'فوائد وأعباء تمويلية (Interest & Financing Expense)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=fin_group, is_group=False)
        add_acc('5530', 'خسائر فروق العملات الأجنبية (Foreign Exchange Loss)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=fin_group, is_group=False)
        add_acc('5540', 'مصاريف استثنائية وأخرى (Other Miscellaneous Expenses)', 'EXPENSE', 'EXPENSE_ACCOUNT', parent=fin_group, is_group=False)

        # مراكز التكلفة الافتراضية
        default_cost_centers = [
            ('CC-MAIN', 'المركز الرئيسي (Main Center)'),
            ('CC-ADMIN', 'الإدارة العامة (General Administration)'),
            ('CC-SALES', 'المبيعات والتسويق (Sales & Marketing)'),
            ('CC-OPS', 'العمليات والتشغيل (Operations)')
        ]
        for code, name in default_cost_centers:
            CostCenter.objects.get_or_create(
                opco=opco,
                code=code,
                defaults={
                    'cost_center_name': name,
                    'is_group': False
                }
            )

    total_count = Account.objects.filter(opco=opco).count()
    return created_count, total_count
