from django.db import transaction
from .models import Account, CostCenter

def seed_default_chart_of_accounts(opco):
    """
    إنشاء شجرة الحسابات القياسية (Standard Chart of Accounts) للشركة
    إذا لم تكن موجودة بالفعل، بناءً على النموذج القياسي المعتمد في ERPNext.
    """
    if Account.objects.filter(opco=opco).exists():
        return False  # موجودة مسبقاً

    with transaction.atomic():
        # 1. الأصول (Assets)
        assets = Account.objects.create(
            opco=opco, account_number='1000', account_name='الأصول (Application of Funds / Assets)',
            root_type='ASSET', account_type='OTHER', is_group=True
        )
        curr_assets = Account.objects.create(
            opco=opco, account_number='1100', account_name='الأصول المتداولة (Current Assets)',
            root_type='ASSET', account_type='OTHER', parent=assets, is_group=True
        )
        cash_group = Account.objects.create(
            opco=opco, account_number='1110', account_name='النقد وما يعادله (Cash & Bank Equivalents)',
            root_type='ASSET', account_type='OTHER', parent=curr_assets, is_group=True
        )
        Account.objects.create(
            opco=opco, account_number='1111', account_name='الخزينة الرئيسية (Main Cashbox)',
            root_type='ASSET', account_type='CASH', parent=cash_group, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='1112', account_name='حساب البنك الرئيسي (Main Bank Account)',
            root_type='ASSET', account_type='BANK', parent=cash_group, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='1120', account_name='العملاء والمدينون (Accounts Receivable - Debtors)',
            root_type='ASSET', account_type='RECEIVABLE', parent=curr_assets, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='1130', account_name='مخزون البضاعة (Stock in Hand)',
            root_type='ASSET', account_type='STOCK', parent=curr_assets, is_group=False
        )
        fixed_assets = Account.objects.create(
            opco=opco, account_number='1200', account_name='الأصول الثابتة (Fixed Assets)',
            root_type='ASSET', account_type='FIXED_ASSET', parent=assets, is_group=True
        )
        Account.objects.create(
            opco=opco, account_number='1210', account_name='أثاث ومعدات وتجهيزات (Equipment & Fixtures)',
            root_type='ASSET', account_type='FIXED_ASSET', parent=fixed_assets, is_group=False
        )

        # 2. الالتزامات (Liabilities)
        liabilities = Account.objects.create(
            opco=opco, account_number='2000', account_name='الالتزامات (Source of Funds / Liabilities)',
            root_type='LIABILITY', account_type='OTHER', is_group=True
        )
        curr_liabilities = Account.objects.create(
            opco=opco, account_number='2100', account_name='الالتزامات المتداولة (Current Liabilities)',
            root_type='LIABILITY', account_type='OTHER', parent=liabilities, is_group=True
        )
        Account.objects.create(
            opco=opco, account_number='2110', account_name='الموردون والدائنون (Accounts Payable - Creditors)',
            root_type='LIABILITY', account_type='PAYABLE', parent=curr_liabilities, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='2120', account_name='أمانات ضريبة القيمة المضافة (VAT Output Tax)',
            root_type='LIABILITY', account_type='TAX', parent=curr_liabilities, is_group=False
        )

        # 3. حقوق الملكية (Equity)
        equity = Account.objects.create(
            opco=opco, account_number='3000', account_name='حقوق الملكية (Equity & Capital)',
            root_type='EQUITY', account_type='EQUITY', is_group=True
        )
        Account.objects.create(
            opco=opco, account_number='3100', account_name='رأس المال المدفوع (Share Capital)',
            root_type='EQUITY', account_type='EQUITY', parent=equity, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='3200', account_name='الأرباح المبقاة / المحتجزة (Retained Earnings)',
            root_type='EQUITY', account_type='EQUITY', parent=equity, is_group=False
        )

        # 4. الإيرادات (Income)
        income = Account.objects.create(
            opco=opco, account_number='4000', account_name='الإيرادات (Income & Revenues)',
            root_type='INCOME', account_type='INCOME_ACCOUNT', is_group=True
        )
        Account.objects.create(
            opco=opco, account_number='4100', account_name='إيرادات المبيعات (Sales Revenue)',
            root_type='INCOME', account_type='INCOME_ACCOUNT', parent=income, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='4200', account_name='إيرادات خدمات وأخرى (Service & Other Income)',
            root_type='INCOME', account_type='INCOME_ACCOUNT', parent=income, is_group=False
        )

        # 5. المصروفات (Expenses)
        expenses = Account.objects.create(
            opco=opco, account_number='5000', account_name='المصروفات (Expenses)',
            root_type='EXPENSE', account_type='EXPENSE_ACCOUNT', is_group=True
        )
        Account.objects.create(
            opco=opco, account_number='5100', account_name='تكلفة البضاعة المباعة (Cost of Goods Sold - COGS)',
            root_type='EXPENSE', account_type='COST_OF_GOODS_SOLD', parent=expenses, is_group=False
        )
        operating_exp = Account.objects.create(
            opco=opco, account_number='5200', account_name='المصروفات التشغيلية والإدارية (Operating Expenses)',
            root_type='EXPENSE', account_type='EXPENSE_ACCOUNT', parent=expenses, is_group=True
        )
        Account.objects.create(
            opco=opco, account_number='5210', account_name='الرواتب والأجور ومستحقات الموظفين (Salaries & Wages)',
            root_type='EXPENSE', account_type='EXPENSE_ACCOUNT', parent=operating_exp, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='5220', account_name='الإيجارات والمرافق (Rent & Utilities)',
            root_type='EXPENSE', account_type='EXPENSE_ACCOUNT', parent=operating_exp, is_group=False
        )
        Account.objects.create(
            opco=opco, account_number='5230', account_name='مصروفات نقل وشحن ولوجستيات (Freight & Logistics)',
            root_type='EXPENSE', account_type='EXPENSE_ACCOUNT', parent=operating_exp, is_group=False
        )

        # إنشاء مركز تكلفة رئيسي افتراضي
        CostCenter.objects.get_or_create(
            opco=opco,
            code='CC-MAIN',
            defaults={
                'cost_center_name': 'المركز الرئيسي (Main Center)',
                'is_group': False
            }
        )

    return True
