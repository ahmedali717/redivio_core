# 📘 دليل المطورين والمعمارية البرمجية الشامل لنظام Redivio ERP
## Comprehensive Developer Onboarding & Architecture Manual

> **الإصدار:** 2.0.0 Enterprise Ready  
> **تاريخ التحديث:** نوفمبر 2026  
> **حالة النظام:** نظام متكامل تجاري وقابل للبيع (Enterprise Commercial Grade)  
> **بيئة التشغيل:** Python 3.13 | Django 5.x | Django REST Framework | Vue 3 | Tailwind CSS  

---

## 📑 جدول المحتويات (Table of Contents)

1. [نظرة عامة على النظام والمعمارية الأساسية](#1-نظرة-عامة-على-النظام-والمعمارية-الأساسية)
2. [معمارية تعدد الشركات والمستأجرين (Multi-Tenancy)](#2-معمارية-تعدد-الشركات-والمستأجرين-multi-tenancy)
3. [نظام الألوان والتصميم (Design System & 3-Color Palette)](#3-نظام-الألوان-والتصميم-design-system--3-color-palette)
4. [التوطين والبيئة المصرية (Egyptian Localization & Compliance)](#4-التوطين-والبيئة-المصرية-egyptian-localization--compliance)
5. [التفصيل الشامل للموديولات (Module-by-Module Directory)](#5-التفصيل-الشامل-للموديولات-module-by-module-directory)
   - [الموديول 1: النواة والمستأجرين (Core & Tenancy)](#الموديول-1-النواة-والمستأجرين-core--tenancy)
   - [الموديول 2: إدارة المخازن (WMS - Warehouse Management)](#الموديول-2-إدارة-المخازن-wms---warehouse-management)
   - [الموديول 3: دليل المواد والأصناف (Item Master & Catalog)](#الموديول-3-دليل-المواد-والأصناف-item-master--catalog)
   - [الموديول 4: إدارة المشتريات والتوريد (Procurement & Supply Chain)](#الموديول-4-إدارة-المشتريات-والتوريد-procurement--supply-chain)
   - [الموديول 5: إدارة المبيعات والعملاء (Sales & CRM)](#الموديول-5-إدارة-المبيعات-والعملاء-sales--crm)
   - [الموديول 6: المحاسبة العامة والمالية (Accounting & General Ledger)](#الموديول-6-المحاسبة-العامة-والمالية-accounting--general-ledger)
   - [الموديول 7: المقاولات والمشاريع (Contracting & RCMS)](#الموديول-7-المقاولات-والمشاريع-contracting--rcms)
   - [الموديول 8: نقاط البيع والمطاعم (Restaurant POS & KDS)](#الموديول-8-نقاط-البيع-والمطاعم-restaurant-pos--kds)
   - [الموديول 9: المساعد الذكي (AI Assistant Copilot)](#الموديول-9-المساعد-الذكي-ai-assistant-copilot)
6. [دورات العمل المتكاملة بين الموديولات (Cross-Module Workflows)](#6-دورات-العمل-المتكاملة-بين-الموديولات-cross-module-workflows)
7. [دليل المطور العملي: كيف تضيف ميزة جديدة؟ (Step-by-Step Developer Guide)](#7-دليل-المطور-العملي-كيف-تضيف-ميزة-جديدة-step-by-step-developer-guide)
8. [أوامر الإدارة والنشر والصيانة (Deployment & Operations)](#8-أوامر-الإدارة-والنشر-والصيانة-deployment--operations)

---

## 1. نظرة عامة على النظام والمعمارية الأساسية

نظام **Redivio ERP** مصمم بمعمارية هجينة متطورة تجمع بين كفاءة Django في إدارة البيانات والأمان، ومرونة Vue 3 في واجهات المستخدم اللحظية بدون تعقيدات بناء Single Page App منفصلة تتطلب خوادم مستقلة:

```
[ المتصفح / العميل ]
       │
       ▼  (HTML + Vue 3 Reactive Components)
[ Django Templates & Layout Engine ]
       │
       ▼  (RESTful JSON Endpoints via DRF)
[ Django REST Framework ViewSets ]
       │
       ▼  (Multi-Tenant Isolation Layer)
[ OpcoAwareMixin / Tenant Middleware ]
       │
       ▼  (Django ORM + Transaction Atomic)
[ Database Engine (PostgreSQL / SQLite) ]
```

### المبادئ الهندسية الأساسية (Core Engineering Principles):
1. **عزل الشركات الصارم (Zero Data Leakage):** لا يمكن لأي مستخدم رؤية بيانات شركة لا يمتلك صلاحية الوصول إليها.
2. **القيود المحاسبية المزدوجة (Double-Entry Bookkeeping):** كل حركة مالية تولد قيود أستاذ عام متوازنة (Debit = Credit).
3. **العمليات الذرية (Atomic Operations):** استخدام `transaction.atomic()` لجميع العمليات الحساسة (إنشاء الفواتير، صرف المخزون، الاستلام، سداد الدفعات).
4. **الأمان والموثوقية (API Bulletproofing):** تعريف صريح للـ `queryset` في كل ViewSet لمنع انهيار موجه الراوتر `basename assertion`.

---

## 2. معمارية تعدد الشركات والمستأجرين (Multi-Tenancy)

تعتمد Redivio معمارية **الهيكل الهرمي للشركات (Hierarchical Multi-Tenancy)**:

```
          [ Holding Company (الشركة القابضة) ]
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
[ Operating Company A ]   [ Operating Company B ]
          │
     ┌────┴────┐
     ▼         ▼
  [Plant 1] [Plant 2]
     │
[Locations] -> [Storage Bins]
```

### كيف تعمل تصفية البيانات في الباك إند؟
في كافة الـ ViewSets يتم استخدام الـ `OpcoAwareMixin` أو الدالة المساعدة `get_request_opco_id(request)`:

1. **فحص الـ Query Parameters:** `?opco=ID` أو `?opco_id=ID`.
2. **فحص Request Body:** في طلبات POST/PUT يتم قراءة `request.data['opco']`.
3. **فحص الجلسة (Session):** قراءة `request.session['active_opco_id']`.
4. **فحص الترويسات (HTTP Headers):** قراءة `X-Opco-Id`.

```python
# مثال لتطبيق التصفية في أي ViewSet جديد:
class CustomEntityViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = CustomEntity.objects.none()  # يمنع خطأ basename
    serializer_class = CustomEntitySerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # يتم فلترة opco تلقائياً بواسطة OpcoAwareMixin
        return qs
```

---

## 3. نظام الألوان والتصميم (Design System & 3-Color Palette)

يلتزم النظام بنظام ألوان ثلاثي محدد وصارم يمنح واجهة المستخدم مظهراً مؤسسياً راقياً وسهل القراءة:

| اللون | كود HEX | تصنيف Tailwind | الاستخدام الرئيسي |
| :--- | :--- | :--- | :--- |
| **الأزرق الأساسي (Primary Blue)** | `#0066FF` | `blue-600` / `indigo-600` | أزرار الحفظ الرئيسية، علامات التبويب النشطة، المؤشرات المالية الحيوية، هوية العلامة التجارية |
| **الرمادي الأردوازي (Slate Gray)** | `#64748B` | `slate-500` / `slate-700` | النصوص التوضيحية، خطوط الجداول، الحقول غير المفعلة، الأيقونات الثانوية |
| **الأبيض النقي (Pure White)** | `#FFFFFF` | `bg-white` / `text-white` | خلفيات البطاقات، مساحات العمل، أسطح النوافذ المنبثقة (Modals) |

> [!IMPORTANT]
> يمنع استخدام درجات ألوان عشوائية أو تدرجات صاخبة خارج لوحة الألوان المعتمدة لضمان الاحترافية وقابلية البيع للشركات الكبرى.

---

## 4. التوطين والبيئة المصرية (Egyptian Localization & Compliance)

النظام مهيأ افتراضياً للعمل في السوق المصري والشركات الإقليمية:

1. **العملة الرسمية:** الجنيه المصري (`EGP` / `ج.م`) عبر دالة التنسيق الموحدة `formatCurrency(val)`.
2. **ضريبة القيمة المضافة المصرية:** النسبة القياسية **14%** (`VAT 14%`).
3. **حسابات الضرائب في الدليل المحاسبي:**
   - ضريبة القيمة المضافة للمخرجات (المبيعات): التزام حالي كود `2121`.
   - ضريبة القيمة المضافة للمدخلات (المشتريات): أصل متداول كود `1161`.
4. **كود الدولة الافتراضي:** جمهورية مصر العربية (`+20` / `Egypt`).
5. **ترقيم الوثائق التلقائي الذكي:**
   - أوامر البيع: `SO-YYYY-0001`
   - أوامر الشراء: `PO-YYYY-0001`
   - فواتير المبيعات: `INV-YYYY-0001`
   - أذون الصرف: `DO-YYYY-0001`
   - أذون الاستلام المخزني: `GRN-YYYY-0001`

---

## 5. التفصيل الشامل للموديولات (Module-by-Module Directory)

---

### الموديول 1: النواة والمستأجرين (Core & Tenancy)
* **المسار في المشروع:** `apps/core/`
* **المسؤولية:** إدارة المستخدمين، الأدوار والصلاحيات، الهيكل التنظيمي (الشركات والمصانع)، خطط الاشتراكات الشهرية/السنوية، ونظام المحادثات والمتابعات (Chatter & Activities).

#### ملفات الـ Backend:
* `apps/core/models.py`:
  - `OpCo`: الكيان الأساسي للشركة (الحقول: الاسم، الكود، الخطة، نوع العملة، الشركة الأم).
  - `CompanyUser`: ربط المستخدمين بالشركات وتحديد الصلاحية (`admin`, `manager`, `user`, `accountant`).
  - `SubscriptionRequest`: إدارة طلبات ترقية الباقات وتفعيل الحسابات.
  - `ChatterMessage` & `ActivitySchedule`: نظام الملاحظات وتكليف المهام والمتابعات الشبيه بـ Odoo Chatter.
* `apps/core/views.py`:
  - `OpCoViewSet`: إدارة الشركات والتبديل بينها.
  - `PlantViewSet`: إدارة المصانع والمستودعات المركزية.
  - `LocationViewSet` & `StorageBinViewSet`: إدارة المواقع والأرفف التخزينية.
  - `CompanyUserViewSet`: إدارة المستخدمين ودعوتهم وتحديد أدوارهم.
  - `ChatterMessageViewSet` & `ActivityScheduleViewSet`: إدارة سجل المحادثات والأنشطة المرتبطة بأي كائن.
  - `CheckAuthAPI` & `switch_active_company`: نقاط النهاية لجلب بيانات الجلسة وتبديل الشركة النشطة.
* `apps/core/serializers.py`: محولات البيانات لجميع نماذج النواة.
* `apps/core/urls.py`: مسارات واجهات الـ Core.

#### ملفات الـ Frontend:
* `templates/base.html`: الهيكل الرئيسي للصفحات واستدعاء مكتبات Vue وTailwind وFontAwesome.
* `templates/index.html`: لوحة التحكم الشاملة التي تحتضن كافة التبويبات والموديولات.
* `templates/components/header.html`: الشريط العلوي (اختيار الشركة النشطة، الملف الشخصي، الإشعارات، تبديل الوضع الليلي والنهاري).
* `templates/components/sidebar.html`: القائمة الجانبية الذكية التي تعرض الموديولات المتاحة بناءً على باقة المستأجر.
* `templates/components/org_builder.html`: مصمم الهيكل التنظيمي التفاعلي للشركات والمصانع والأرفف.
* `templates/components/odoo_chatter.html`: نافذة المحادثة وإسناد المهام أسفل الوثائق.
* `templates/components/subscription_modal.html`: نافذة ترقية الخطط والاشتراكات وسداد الرسوم.
* `redivio_project/static/js/modules/org_builder.js`: منطق Vue التفاعلي لبناء شجرة الشركات.
* `redivio_project/static/js/modules/userManager.js`: إدارة مستخدمي الشركات والصلاحيات.

---

### الموديول 2: إدارة المخازن (WMS - Warehouse Management)
* **المسار في المشروع:** `apps/wms/`
* **المسؤولية:** تتبع الأرصدة الحية، حركات الوارد والمنصرف، تحويلات بين المستودعات، الهالك، والجرد الفعلي للأرصدة.

#### ملفات الـ Backend:
* `apps/wms/models.py`:
  - `Plant`: المصنع أو الفرع الرئيسي.
  - `StorageLocation`: الموقع التخزيني داخل المصنع (مثال: مستودع المواد الخام).
  - `StorageBin`: الرف أو الخانة الدقيقة (اللوكيشن الأدق).
  - `StockQuant`: رصيد المادة الفعلي الموجود في رف محدد مع دعم التتبع بالسيريال ورقم التشغيلة (Batch).
  - `StockMove`: السجل التاريخي لكل حركة وارد أو صادر أو تحويل.
  - `WarehouseTransfer`: أمر تحويل مخزني بين فرعين أو رفين.
  - `StockScrap`: تسوية الهالك والتالف وتخفيض الأرصدة المخزنية تلقائياً.
* `apps/wms/views.py`:
  - `StockQuantViewSet`: جلب أرصدة المخازن الحالية وتقارير كروت الصنف.
  - `StockMoveViewSet`: تسجيل واستعراض حركات المخازن المباشرة.
  - `WarehouseTransferViewSet`: تنفيذ أوامر النقل بين المواقع.
  - `StockScrapViewSet`: تسجيل تسويات الهالك والمفقود.
  - `wms_stats`: مؤشرات أداء المخازن (قيمة المخزون، الأصناف الحرجة، عدد الحركات).
* `apps/wms/serializers.py`: محولات بيانات الـ WMS.
* `apps/wms/urls.py`: مسارات واجهات المستودعات.

#### ملفات الـ Frontend:
* `templates/wms/opening_inventory.html`: شاشة إدخال الأرصدة الافتتاحية والجرد الدوري.
* `templates/wms/direct_stock_move.html`: شاشة حركات المخازن المباشرة (إدخال يدوي / صرف تشغيل).
* `templates/wms/inventory_moves.html`: تقرير حركات المخزون الشامل.
* `templates/wms/inventory_item_report.html`: كارت الصنف التفصيلي (Stock Card).
* `templates/wms/print_move.html` & `print_audit.html`: قوالب طباعة أذون الحركات المخزنية وتقارير الجرد.
* `redivio_project/static/js/modules/inventory.js`: دوال جلب الأرصدة، فحص الـ Low Stock، ومعالجة الحركات.

---

### الموديول 3: دليل المواد والأصناف (Item Master & Catalog)
* **المسار في المشروع:** `apps/item_master/`
* **المسؤولية:** شجرة المجموعات، كود الصنف (SKU)، الباركود الدولي، وحدات القياس (UOM)، ومعاملات التحويل بين الوحدات.

#### ملفات الـ Backend:
* `apps/item_master/models.py`:
  - `Category`: تصنيف الأصناف الشجري.
  - `Material`: الصنف الرئيسي (الاسم، SKU، الباركود، وحدة القياس الأساسية والبديلة، سعر البيع والشراء، حد الطلب).
  - `SaleGroup`: المجموعات البيعية المخصصة لنقاط البيع السريعة.
* `apps/item_master/views.py`:
  - `MaterialViewSet`: إدارة الأصناف واستيرادها دفعة واحدة من ملفات Excel/CSV والتحقق من حدود الباقة.
  - `CategoryViewSet` & `SaleGroupViewSet`: إدارة التصنيفات والمجموعات.
* `apps/item_master/serializers.py`: التحقق من صحة الأسعار الإيجابية وتناسق معاملات التحويل.
* `apps/item_master/urls.py`: مسارات دليل المواد.

#### ملفات الـ Frontend:
* `templates/components/item_master_list.html`: جدول عرض وتصفية الأصناف مع البحث الفوري ودعم الباركود.
* `templates/components/item_master_modal.html`: نافذة إضافة وتعديل الصنف بدقة عالية.
* `templates/components/categories_list.html`: شاشة تنظيم مجموعات الأصناف.
* `templates/components/item_variants_modal.html`: إدارة متغيرات الأصناف (الألوان والمقاسات).
* `redivio_project/static/js/modules/itemMaster.js`: دوال التحقق من صحة الصنف ورفع ملفات الاستيراد.

---

### الموديول 4: إدارة المشتريات والتوريد (Procurement & Supply Chain)
* **المسار في المشروع:** `apps/procurement/`
* **المسؤولية:** دورة المشتريات الكاملة: طلب شراء (PR) ➔ طلب أسعار (RFQ) ➔ بوابة الموردين العامة ➔ عروض الأسعار (SQ) ➔ مصفوفة المقارنة ➔ أمر الشراء (PO) ➔ إذن الاستلام المخزني (GRN) ➔ مردودات المشتريات (RTV).

#### ملفات الـ Backend:
* `apps/procurement/models.py`:
  - `Vendor`: بيانات الموردين وأرصدتهم.
  - `PurchaseRequisition` (PR): طلب الشراء الداخلي من الأقسام.
  - `RequestForQuotation` (RFQ): طلب عرض السعر الموجه للموردين مع توكن خاص بالبوابة الخارجية.
  - `SupplierQuotation` (SQ): عروض الأسعار المستلمة من الموردين.
  - `QuotationComparison`: المقارنة الفنية والمالية واختيار العرض الفائز آلياً.
  - `PurchaseOrder` (PO) & `PurchaseOrderLine`: أمر الشراء المعتمد.
  - `StockReceipt` (GRN): إذن الاستلام المخزني الفعلي.
  - `PurchaseReturn` (RTV): مرتجع مشتريات إلى المورد.
* `apps/procurement/views.py`:
  - `VendorViewSet`: إدارة الموردين وكشف حساب المورد التراكمي (Vendor Ledger).
  - `PurchaseOrderViewSet`: إنشاء واعتماد أوامر الشراء وتنفيذ استلام البضائع.
  - `public_rfq_portal`: بوابة خارجية آمنة يدخل إليها المورد برابط مخصص لتسجيل أسعاره مباشرة دون الحاجة لإنشاء حساب في النظام.
  - `print_po_pdf` & `print_grn_pdf`: تصدير أوامر الشراء وأذون الاستلام للطباعة الرسمية.
* `apps/procurement/serializers.py`: تحويلات دورة المشتريات والتحقق من الكميات الموجبة والأسعار.
* `apps/procurement/urls.py`: مسارات واجهات المشتريات.

#### ملفات الـ Frontend:
* `templates/procurement/procurement_dashboard.html`: لوحة متابعة دورة المشتريات ومؤشراتها.
* `templates/procurement/vendors_list.html`: شاشة دليل الموردين ومتابعة أرصدتهم.
* `templates/procurement/vendor_ledger.html`: كشف الحساب التاريخي للمورد (مشتريات، مدفوعات، مرتجعات).
* `templates/procurement/public_rfq_portal.html`: بوابة عروض أسعار الموردين المستقلة المتجاوبة مع الهواتف.
* `templates/procurement/print_po.html` & `print_grn.html`: قوالب الطباعة الرسمية لشعار الشركة وبيانات التوريد.

---

### الموديول 5: إدارة المبيعات والعملاء (Sales & CRM)
* **المسار في المشروع:** `apps/sales/`
* **المسؤولية:** إدارة العملاء، عروض الأسعار، أوامر البيع (SO)، أذون الصرف والتسليم (Stock Delivery / GDN)، فواتير المبيعات، ومردودات العملاء (RFC).

#### ملفات الـ Backend:
* `apps/sales/models.py`:
  - `Customer`: سجل العملاء والحد الائتماني والبيانات الضريبية.
  - `SalesOrder` & `SalesOrderLine`: أمر البيع التجاري متضمناً حساب الخصومات وضريبة القيمة المضافة (14%).
  - `StockDelivery`: إذن صرف البضاعة من المخازن للعميل.
  - `SalesInvoice`: فاتورة المبيعات الرسمية.
  - `CustomerPayment`: سند استلام دفعة من العميل وتخفيض رصيده.
  - `SalesReturn`: إرجاع بضاعة من العميل إلى المستودع.
* `apps/sales/views.py`:
  - `CustomerViewSet`: إدارة العملاء والبحث بالاسم أو الهاتف.
  - `SalesOrderViewSet`: إنشاء وتعديل أوامر البيع وإطلاق أذون الصرف وإصدار الفواتير.
  - `SalesInvoiceViewSet`: ترحيل فواتير المبيعات آلياً لدفتر الأستاذ العام وتوليد القيود المحاسبية.
  - `print_so_pdf`, `print_delivery_pdf`, `print_invoice_pdf`: طباعة أوامر البيع وأذون الصرف والفواتير الضريبية مع رمز الاستجابة السريع (QR Code).
* `apps/sales/serializers.py`: تحويلات المبيعات والتحقق من حسابات الضرائب ونسب الخصم.

#### ملفات الـ Frontend:
* `templates/sales/dashboard.html`: لوحة معلومات المبيعات (حجم المبيعات، الفواتير المستحقة، متوسط قيمة الطلب).
* `templates/sales/orders_list.html`: جدول أوامر البيع مع إمكانية الصرف والإلغاء وإصدار الفواتير.
* `templates/sales/customers_list.html`: دليل العملاء وأرصدتهم.
* `templates/sales/invoices_list.html`: قائمة فواتير المبيعات وحالات سدادها وترحيلها.
* `templates/sales/print_invoice.html`: قالب الفاتورة الضريبية المعتمدة المتوافقة مع متطلبات مصلحة الضرائب المصرية (ETA).

---

### الموديول 6: المحاسبة العامة والمالية (Accounting & General Ledger)
* **المسار في المشروع:** `apps/accounting/`
* **المسؤولية:** شجرة الحسابات الهرمية (COA)، مراكز التكلفة، سندات القيد اليومية، الأستاذ العام (General Ledger)، فواتير المشتريات، سندات القبض والصرف، والتقارير الختامية (ميزان المراجعة، الأرباح والخسائر، الميزانية العمومية).

#### ملفات الـ Backend:
* `apps/accounting/models.py`:
  - `Account`: شجرة الحسابات الهرمية (الأصول، الالتزامات، حقوق الملكية، الإيرادات، المصروفات).
  - `CostCenter`: مراكز التكلفة لتوزيع المصروفات والإيرادات على المشاريع والأقسام.
  - `JournalEntry` & `JournalEntryLine`: قيود اليومية المحاسبية المزدوجة.
  - `GLEntry`: جدول حركات الأستاذ العام الفعلي غير القابل للتعديل بعد الترحيل.
  - `PurchaseInvoice`: فاتورة الشراء الموردة مع حساب ضريبة المدخلات.
  - `PaymentEntry`: سند قبض أو صرف مالي مع ربطه بالفواتير وتحديث أرصدة الخزينة والبنوك.
* `apps/accounting/views.py`:
  - `AccountViewSet`: استعراض الشجرة وتوليد الدليل المحاسبي القياسي المعتمد تلقائياً (`seed-coa`).
  - `JournalEntryViewSet`: تسجيل واعتماد وترحيل سندات القيد.
  - `GLEntryViewSet`: استعلامات الأستاذ العام السريعة.
  - `PurchaseInvoiceViewSet`: ترحيل فواتير الشراء وإلغاؤها وعكس قيودها بأمان.
  - `PaymentEntryViewSet`: اعتماد سندات السداد وتحديث حسابات الموردين والعملاء.
  - `FinancialReportsViewSet`: محرك التقارير المالية المتطورة (ميزان المراجعة، قائمة الدخل، الميزانية العمومية).
* `apps/accounting/services.py`: دالة `seed_default_chart_of_accounts(opco)` لتوليد شجرة حسابات قياسية متكاملة عند تأسيس الشركة.
* `apps/accounting/urls.py`: مسارات واجهات المحاسبة.

#### ملفات الـ Frontend:
* `templates/accounting/chart_of_accounts.html`: مستعرض شجرة الحسابات التفاعلي الشجري.
* `templates/accounting/journal_entries.html`: شاشة إدخال قيود اليومية ومراقبة توازن المدين والدائن لحظياً.
* `templates/accounting/general_ledger.html`: شاشة دفتر الأستاذ العام وتصفية الحركات حسب التواريخ والأطراف.
* `templates/accounting/purchase_invoices.html`: شاشة فواتير المشتريات وإدارتها.
* `templates/accounting/payment_entries.html`: شاشة سندات الصرف والقبض.
* `templates/accounting/financial_reports.html`: شاشة التقارير المالية (Trial Balance, P&L, Balance Sheet) بتسلسل شجري ودعم التصدير والطباعة.
* `templates/components/purchase_invoice_details_modal.html`: نافذة تفاصيل وبنود فاتورة المشتريات.

---

### الموديول 7: المقاولات والمشاريع (Contracting & RCMS)
* **المسار في المشروع:** `apps/contracting/`
* **المسؤولية:** إدارة مشاريع المقاولات، العقود الرئيسية وعقود مقاولي الباطن، مقايسات الأعمال وجداول الكميات (BOQ)، حصر الكميات الفعلي، المستخلصات (Abstracts)، العهد النقدية للمواقع ومصروفاتها، الشيكات البنكية ومتابعة تحصيلها، أوامر التصنيع وأوامر التعتيق والتحميل.

#### ملفات الـ Backend:
* `apps/contracting/models.py`:
  - `Project`: سجل المشروع وتواريخ البدء والانتهاء ونسب الإنجاز.
  - `JobContract` & `ContractExtension`: العقود الأساسية والملاحق الزمنية والمالية.
  - `JobCostSheet` & `JobCostLine`: مقايسة المشروع وتكاليف بنود الأعمال التقديرية.
  - `QuantitySurvey`: دفاتر حصر الأعمال المنفذة في الموقع.
  - `ContractAbstract`: مستخلصات العملاء ومقاولي الباطن ونسب الاستقطاع وضمان الأعمال.
  - `CheckTransaction`: محفظة الشيكات الواردة والصادرة وحالاتها (تحت التحصيل، محصل، مرتد).
  - `SiteCustody` & `SiteCustodyExpense`: عهد مهندسي المواقع وتسوية المصروفات.
  - `FabricationOrder`, `ManufacturingOrder`, `LoadingNote`: إدارة التصنيع والتشغيل بالمصانع والورش ونقل المنتجات للمواقع.
* `apps/contracting/views.py`: كافة الـ ViewSets المخصصة لخدمة دورة حياة مشاريع المقاولات مع تصفية تعدد الشركات.
* `apps/contracting/serializers.py`: تحويلات المقاولات وضمان صحة الحسابات المالية.
* `apps/contracting/urls.py`: مسارات واجهات المقاولات.

#### ملفات الـ Frontend:
* `templates/contracting/dashboard.html`: لوحة مؤشرات أداء المشاريع والعقود وموقف التحصيل.
* `templates/contracting/projects_list.html`: قائمة المشاريع ومتابعة تقدم الإنجاز.
* `templates/contracting/contracts_list.html`: عقود المالك ومقاولي الباطن.
* `templates/contracting/cost_sheets_list.html`: جداول كميات المشاريع وتكاليف البنود.
* `templates/contracting/abstracts_list.html`: شاشة المستخلصات وحساب الدفعات.
* `templates/contracting/checks_list.html`: حافظة الشيكات البنكية ومتابعة تواريخ الاستحقاق.
* `templates/contracting/custody_list.html`: متابعة عهد المواقع ومصروفات كل مشروع.
* `templates/contracting/fabrication_list.html` & `loading_notes_list.html`: أوامر التصنيع والتشغيل وإذن شحن وتعتيق المواد للمواقع.

---

### الموديول 8: نقاط البيع والمطاعم (Restaurant POS & KDS)
* **المسار في المشروع:** `apps/restaurant_pos/`
* **المسؤولية:** شاشات الكاشير السريعة للمطاعم والكافيهات ومحلات التجزئة، إدارة الطاولات والبارتشنات التفاعلية، شاشة المطبخ الذكية (KDS)، فتح وإغلاق ورديات الكاشير، أكواد الخصومات والعروض.

#### ملفات الـ Backend:
* `apps/restaurant_pos/models.py`:
  - `RestaurantFloor`: طوابق وصالات المطعم.
  - `RestaurantTable`: طاولات الصالة وإحداثياتها وحالتها (متاحة، مشغولة، محجوزة).
  - `POSTerminal`: أجهزة الكاشير ونقاط البيع.
  - `POSSession`: ورديات الكاشير وتتبع الرصيد الافتتاحي والنقدي الفعلي والعجز/الزيادة.
  - `POSOrder` & `POSOrderItem`: طلبات نقطة البيع والخصومات وطرق الدفع.
  - `PromoCode`: كوبونات الخصم وقواعد تطبيقها.
* `apps/restaurant_pos/views.py`:
  - `POSOrderViewSet`: إنشاء الطلبات والخصم التلقائي من المخزون واسترجاع الطلبات.
  - `RestaurantFloorViewSet` & `RestaurantTableViewSet`: إدارة تخطيط الصالة وتحديث حالات الطاولات لحظياً.
  - `POSTerminalViewSet`: إدارة نقاط البيع والربط بالفروع.
  - `open_session` & `close_session`: إدارة فتح وإغلاق ورديات الكاشير بدقة مالية متناهية.
* `apps/restaurant_pos/urls.py`: مسارات واجهات الـ POS.

#### ملفات الـ Frontend:
* `templates/pos/terminal.html`: واجهة الكاشير التفاعلية فائقة السرعة مع دعم شاشات اللمس والباركود.
* `templates/pos/floor_layout.html`: خريطة الصالة التفاعلية مع إمكانية سحب وإسقاط الطاولات وفتح الطلبات بضغطة زر.
* `templates/pos/kds.html`: شاشة المطبخ التفاعلية (Kitchen Display System) مع مؤشرات ألوان للأوامر المتأخرة والجاهزة للتسليم.
* `templates/pos/dashboard.html` & `order_history.html`: تقارير مبيعات الورديات والطلبات السابقة.
* `templates/pos/settings.html`: إعدادات نقاط البيع والصالات وأكواد الخصم.

---

### الموديول 9: المساعد الذكي (AI Assistant Copilot)
* **المسار في المشروع:** `apps/ai_assistant/`
* **المسؤولية:** مساعد ذكي مدمج داخل شاشات الـ ERP مدعوم بنماذج Gemini AI لمساعدة المستخدمين والرد الفوري على الاستفسارات وتوجيههم داخل موديولات النظام.

#### ملفات الـ Backend:
* `apps/ai_assistant/views.py`: دالة `chat_api` التي تقرأ `GEMINI_API_KEY` من بيئة السيرفر وتتصل بـ `google.generativeai` وتجيب على استفسارات المستخدمين بشكل احترافي.
* `apps/ai_assistant/urls.py`: مسار `/ai/chat/`.

#### ملفات الـ Frontend:
* `templates/components/ai_chat.html`: نافذة الدردشة العائمة المتجاوبة في الزاوية السفلية من النظام مع أيقونة تفاعلية وزر لفتح وإغلاق المحادثة.

---

## 6. دورات العمل المتكاملة بين الموديولات (Cross-Module Workflows)

### دورة المبيعات القياسية (Order-to-Cash Workflow):
```
[ Customer ]
     │
     ▼
[ Sales Order (SO) ] 
     │ (تأكيد الطلب)
     ├─────────────────────────────────────────┐
     ▼                                         ▼
[ Stock Delivery (GDN) ]                 [ Sales Invoice ]
     │                                         │
     ▼                                         ▼
[ WMS Stock Quant Deduction ]            [ GL Posting (ترحيل الأستاذ العام) ]
  (تخفيض رصيد الصنف في الرف)               ├─ مدين: ح/ العملاء (1130)
                                           ├─ دائن: ح/ إيرادات المبيعات (4110)
                                           └─ دائن: ح/ أمانات ضريبة المخرجات (2121)
                                                       │
                                                       ▼
                                            [ Payment Entry (سند التحصيل) ]
                                              ├─ مدين: ح/ الخزينة أو البنك (1110)
                                              └─ دائن: ح/ العملاء (1130)
```

### دورة المشتريات القياسية (Procure-to-Pay Workflow):
```
[ Purchase Requisition (PR) ]
     │
     ▼
[ Request for Quotation (RFQ) ] ──> [ Public Vendor Portal ]
     │                                       │
     ▼                                       ▼
[ Quotation Comparison ] <────────── [ Supplier Quotations ]
     │ (اختيار العرض الفائز)
     ▼
[ Purchase Order (PO) ]
     │ (وصول البضاعة)
     ├─────────────────────────────────────────┐
     ▼                                         ▼
[ Stock Receipt (GRN) ]                  [ Purchase Invoice (Bill) ]
     │                                         │
     ▼                                         ▼
[ WMS Stock Quant Addition ]             [ GL Posting (ترحيل الأستاذ العام) ]
  (زيادة رصيد الصنف في الرف)               ├─ مدين: ح/ تكلفة المشتريات/المخزون (1140)
                                           ├─ مدين: ح/ أصول ضريبة المدخلات (1161)
                                           └─ دائن: ح/ الموردين (2110)
                                                       │
                                                       ▼
                                            [ Payment Entry (سند الصرف) ]
                                              ├─ مدين: ح/ الموردين (2110)
                                              └─ دائن: ح/ الخزينة أو البنك (1110)
```

---

## 7. دليل المطور العملي: كيف تضيف ميزة جديدة؟ (Step-by-Step Developer Guide)

إذا أردت كديفلوبر إضافة شاشة وموديل جديد (مثلاً: إدارة خطابات الضمان `LetterOfGuarantee`):

### الخطوة 1: تعريف الموديل في الباك إند
في `apps/contracting/models.py`:
```python
class LetterOfGuarantee(models.Model):
    opco = models.ForeignKey('core.OpCo', on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    lg_number = models.CharField(max_length=64, unique=True)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    bank_name = models.CharField(max_length=128)
    expiry_date = models.DateField()
    status = models.CharField(max_length=20, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.lg_number} - {self.bank_name}"
```

### الخطوة 2: إنشاء الـ Migration
```bash
python manage.py makemigrations contracting
python manage.py migrate
```

### الخطوة 3: إنشاء الـ Serializer
في `apps/contracting/serializers.py`:
```python
class LetterOfGuaranteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LetterOfGuarantee
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
```

### الخطوة 4: إنشاء الـ ViewSet وتأمين الـ Multi-Tenancy
في `apps/contracting/views.py`:
```python
class LetterOfGuaranteeViewSet(BaseOpCoViewSet):
    queryset = LetterOfGuarantee.objects.none()  # حماية من خطأ basename
    serializer_class = LetterOfGuaranteeSerializer
    model = LetterOfGuarantee
```

### الخطوة 5: تسجيل المسار في الراوتر
في `apps/contracting/urls.py`:
```python
router.register(r'letters-of-guarantee', LetterOfGuaranteeViewSet, basename='contracting-lg')
```

### الخطوة 6: بناء واجهة المستخدم في الـ Frontend
1. أنشئ القالب الجديد `templates/contracting/lg_list.html`.
2. استدعه في `templates/index.html` داخل حاوية الـ `view === 'contracting_module'`:
```html
<div v-if="contractingTab === 'lg'" class="absolute inset-0 overflow-y-auto">
    {% include "contracting/lg_list.html" %}
</div>
```
3. أضف دوال الـ Fetch والـ Submit في كائن Vue الرئيسي داخل `redivio_project/static/js/main.js`.

---

## 8. أوامر الإدارة والنشر والصيانة (Deployment & Operations)

### تشغيل الفحص والتحقق من صحة النظام:
```bash
python manage.py check
```

### تشغيل السيرفر المحلي للتطوير:
```bash
python manage.py runserver 127.0.0.1:8000
```

### تجميع الملفات الثابتة للإنتاج:
```bash
python manage.py collectstatic --noinput
```

### تحديث الخادم السحابي (PythonAnywhere Deployment):
```bash
cd ~/redivio_core
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
touch /var/www/ahmedali717_pythonanywhere_com_wsgi.py
```

---
**تم إعداد هذا التوثيق ليكون المرجع الأساسي المكتبي والعملي لجميع مهندسي البرمجيات العاملين على منصة Redivio ERP.**
