import { utils } from './modules/utils.js';
import { inventoryModule } from './modules/inventory.js';
import { orgModule } from './modules/org_builder.js';
import { itemMasterModule } from './modules/itemMaster.js';

console.log("🚀 REDIVIO Core v1.0.5 Loaded");
console.log("🌍 Current Language Mode (isArabic):", window.is_arabic);

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            searchQuery: '',
            scannerInstance: null,
            isScanning: false, // لازم يتعرف هنا عشان الـ HTML يشوفه
            barcodeQuery: '',
            // 🚀 ضيف المتغير ده هنا في أول سطر
            activeOperation: null,
            showBrandDropdown: false,
            showActivityLog: false,
            showNotificationsDropdown: false,
            
            // SaaS Configurations
            systemMode: 'modular',
            purchasedModules: [],

            // 🚀 التعديل الأول: ضيف السطرين دول هنا بالظبط
            showQtyModal: false,
            scannedItemData: {
                material_id: null,
                material_name: '',
                sku: '',
                ordered_qty: 0,
                scan_qty: 1
            },

            // 1. جعل الموديول الموحد هو الشاشة الافتراضية (اختياري)
            view: 'dashboard',
            inventoryMoves: [],
            // 🚀 إضافة المتغير الجديد للتبديل بين الأصناف والأرصدة
            inventoryTab: 'levels',
            salesTab: 'dashboard',
            soSearch: '',
            accountingTab: 'dashboard',
            customers: [],
            salesOrders: [],
            salesInvoices: [],
            customerPayments: [],
            reportFilters: {
                material_id: '',
                location_id: '',
                date_from: '',
                date_to: ''
            },
            loading: false,
            sidebarCollapsed: false,
            isArabic: window.is_arabic,
            isEditing: false,
            isAdvancedMode: false,
            notifications: [],

            confirmModal: {
                show: false,
                onConfirm: null,
                onCancel: null
            },

            // 2. تحديث القائمة الجانبية لتكون "موديولات" بدلاً من شاشات
            sidebarGroups: {
                settings: [
                    { id: 'global_config', name: { ar: 'الإعدادات العامة', en: 'Global Config' }, icon: 'fas fa-cogs' },
                    { id: 'users', name: { ar: 'المستخدمين', en: 'Users' }, icon: 'fas fa-users' }
                ],
                operations: [
                    { id: 'org_builder', name: { ar: 'بناء الهيكل', en: 'Org Builder' }, icon: 'fas fa-sitemap' },
                    // موديول واحد شامل للمخزون
                    { id: 'inventory_module', name: { ar: 'RIMS (المخزون)', en: 'RIMS (Inventory)' }, icon: 'fas fa-archive' },
                    { id: 'procurement_module', name: { ar: 'RPMS (المشتريات)', en: 'RPMS (Procurement)' }, icon: 'fas fa-shopping-cart' },
                    { id: 'sales_module', name: { ar: 'إدارة المبيعات', en: 'Sales & CRM' }, icon: 'fas fa-cart-shopping' },
                    { id: 'accounting_module', name: { ar: 'المحاسبة والمالية', en: 'Accounting' }, icon: 'fas fa-file-invoice-dollar' }
                ]
            },


            ...(utils.state || {}),
            ...(inventoryModule.state || {}),

            user: { name: '...', role: '...', is_superuser: false },

            config: {
                company_name: '',
                is_holding: false,
                tax_id: '',
                cr_number: '',
                created_at: null,
                logo: null
            },

            license: {
                daysRemaining: 15,
                companyName: '...',
                isExpired: false
            },
            topMaterials: [],

            activeUsers: [
                { id: 1, name: 'Ahmed Ali', role: 'Administrator', status: 'online', last_action: 'Dashboard View' },
                { id: 2, name: 'Sara Kamel', role: 'Sales Manager', status: 'online', last_action: 'Creating Invoice' },
                { id: 3, name: 'Omar Zaid', role: 'WMS Supervisor', status: 'away', last_action: 'Stock Count' }
            ],
            kpis: {
                inventory: { total_items: 0, stock_qty: 0, dead_stock: 0, critical_items: 0 },
                sales: { total: 0, delivered: 0, remaining_delivery: 0, invoiced: 0, remaining_invoice: 0 },
                procurement: { total: 0, received: 0, invoiced: 0, paid: 0 },
                finance: { invoices: 0, collected: 0, remaining: 0 },
                vendors: 0,
                customers_count: 0
            },
            allOpcos: [],
            opcos: [],

            subsidiaries: [],
            plants: [],
            locations: [],
            bins: [],
            materials_list: [],
            inventoryList: [],
            wms_stats: {},
            selectedItemCard: null,
            vendors: [],
            selectedVendor: null,
            vendorLedger: null,
            purchase_orders: [],
            pending_pos: [],

            showModal: false,
            materialTab: 'general',
            modalType: '',
            draggedType: null,
            activeOpcoId: null,
            parentOpcoId: null,
            activePlantId: null,
            activeLocationId: null,
            imagePreview: null,
            selectedFile: null,
            newLogoFile: null,

            modalTitles: {
                plant: { ar: 'إضافة منشأة جديدة', en: 'Add New Facility' },
                location: { ar: 'إضافة موقع تخزين', en: 'Add Storage Location' },
                bin: { ar: 'إضافة رف/حاوية', en: 'Add New Bin' },
                material: { ar: 'تعريف صنف جديد', en: 'Define New Material' },
                stock_entry: { ar: 'إذن استلام / تحويل مخزني', en: 'Stock Inbound / Transfer' },
                po: { ar: 'أمر توريد جديد', en: 'New Purchase Order' },
                opco: { ar: 'إضافة شركة تابعة / مشغلة', en: 'Add Subsidiary / OpCo' },
                salesorder: { ar: 'أمر بيع جديد', en: 'New Sales Order' },
                customer: { ar: 'بيانات عميل جديد', en: 'Customer Information' },

                // 🚀 السطور اللي كانت ناقصة وعاملة المشكلة تم إضافتها هنا:
                view_po: { ar: 'تفاصيل أمر التوريد', en: 'Purchase Order Details' },
                payment: { ar: 'تحصيل دفعة مالية', en: 'Record Payment' },
                delivery: { ar: 'صرف بضاعة', en: 'Order Delivery' },
                so_delivery: { ar: 'صرف بضاعة من أمر بيع', en: 'WMS Sales Delivery' }
            },

            forms: {
                ...(inventoryModule.state?.forms || {}),
                opco: { id: null, code: '', name: '', currency: 'USD', parent: null, is_holding: false },
                plant: { id: null, opco: null, code: '', name: '' },
                location: { id: null, plant: null, code: '', name: '' },
                bin: { id: null, storage_location: null, code: '' },
                material: {
                    id: null,
                    sku: '',
                    name: '',
                    category: '',
                    base_uom: 'PCS',
                    barcode: '',
                    standard_price: 0,
                    // 🚀 الهيكل الجديد لدعم تعدد الشركات
                    company_assignments: [
                        { opco_id: null, bins: [], primary_bin: null }
                    ],
                    tracking: 'none',
                    reorder_level: 0,
                    max_level: 0
                },
                po: {
                    id: null,
                    vendor: '',
                    po_number: '',
                    is_tax_inclusive: false, // شامل الضريبة؟
                    tax_rate: 15, // نسبة الضريبة الافتراضية
                    lines: [{ material: '', quantity: 1, unit_price: 0 }]
                },

                stock_entry: { 
                    items: [], 
                    po_id: '', 
                    filterType: 'ALL', 
                    groupBy: 'none', 
                    payment_method: 'CASH', 
                    tax_rate: 15,
                    date_from: '',
                    date_to: '',
                    contact_search: ''
                },
                customer: { id: null, code: '', name: '', tax_id: '', email: '', phone: '', address: '' },
                salesorder: {
                    id: null,
                    customer: '',
                    so_number: `SO-${Date.now()}`,
                    status: 'DRAFT',
                    total_amount: 0,
                    tax_amount: 0,
                    grand_total: 0,
                    lines: [{ material: '', quantity: 1, unit_price: 0 }]
                },
                payment: {
                    invoice: null,
                    customer: null,
                    amount: 0,
                    method: 'CASH',
                    reference: ''
                }
            }
        };
    },

    computed: {


        filteredMaterials() {
            let list = this.materials_list || [];

            // 1. فلترة بالشركة الحالية
            if (this.activeOpcoId) {
                list = list.filter(item => {
                    if (!item.company_assignments) return true;
                    return item.company_assignments.some(a => parseInt(a.opco_id) === parseInt(this.activeOpcoId));
                });
            }

            // 2. فلترة بنص البحث (لو المستخدم كتب حاجة)
            if (!this.searchQuery) return list;

            const query = this.searchQuery.toLowerCase();
            return list.filter(item =>
                (item.name && item.name.toLowerCase().includes(query)) ||
                (item.sku && item.sku.toLowerCase().includes(query)) ||
                (item.barcode && item.barcode.toLowerCase().includes(query))
            );
        },

        availableBinsForMaterial() {
            if (!this.activeOpcoId) return this.bins;
            return this.bins.filter(bin => {
                const location = this.locations.find(l => l.id === bin.storage_location);
                if (!location) return false;
                const plant = this.plants.find(p => p.id === location.plant);
                return plant && parseInt(plant.opco) === parseInt(this.activeOpcoId);
            });
        },

        currentSubsidiaries() {
            if (!this.activeOpcoId) return [];
            const activeId = parseInt(this.activeOpcoId);
            return this.opcos.filter(o => {
                const parentId = (o.parent && typeof o.parent === 'object') ? o.parent.id : o.parent;
                return parentId !== null && parseInt(parentId) === activeId;
            });
        },

        materials() {
            return this.materials_list || [];
        },

        filteredInventory() {
            if (!this.activeOpcoId) return this.inventoryList;
            return this.inventoryList.filter(item => item.opco_id === parseInt(this.activeOpcoId));
        },

        activeLocationName() {
            const loc = this.locations.find(l => l.id === this.activeLocationId);
            return loc ? loc.name : '...';
        },

        licenseStatus() {
            return this.license;
        },

        // 🚀 حسابات أمر التوريد (الضرائب والإجماليات)
        poLineTotal() {
            if (!this.forms.po || !this.forms.po.lines) return 0;
            return this.forms.po.lines.reduce((sum, line) => sum + ((line.quantity || 0) * (line.unit_price || 0)), 0);
        },
        poTaxAmount() {
            if (!this.forms.po) return 0;
            const rate = (this.forms.po.tax_rate || 0) / 100;
            if (this.forms.po.is_tax_inclusive) {
                // لو السعر شامل الضريبة، بنستخرج الضريبة من الإجمالي
                return this.poLineTotal - (this.poLineTotal / (1 + rate));
            } else {
                // لو غير شامل، بنضرب الإجمالي في النسبة
                return this.poLineTotal * rate;
            }
        },
        poSubtotal() {
            if (!this.forms.po) return 0;
            if (this.forms.po.is_tax_inclusive) {
                return this.poLineTotal - this.poTaxAmount;
            } else {
                return this.poLineTotal;
            }
        },
        poGrandTotal() {
            if (!this.forms.po) return 0;
            if (this.forms.po.is_tax_inclusive) {
                return this.poLineTotal; // الإجمالي هو نفس السعر المكتوب
            } else {
                return this.poLineTotal + this.poTaxAmount; // الإجمالي + الضريبة
            }
        },

        // --- Sales Module Computed ---
        filteredCustomers() {
            if (!this.customerSearch) return this.customers;
            const q = this.customerSearch.toLowerCase();
            return this.customers.filter(c => c.name.toLowerCase().includes(q) || (c.code && c.code.toLowerCase().includes(q)));
        },
        filteredSalesOrders() {
            if (!this.soSearch) return this.salesOrders;
            const q = this.soSearch.toLowerCase();
            return this.salesOrders.filter(o => o.so_number.toLowerCase().includes(q) || (o.customer_name && o.customer_name.toLowerCase().includes(q)));
        },
        totalMonthlySales() {
            return this.salesInvoices.reduce((sum, inv) => sum + parseFloat(inv.total_amount || 0), 0);
        },
        totalUnpaidInvoices() {
            return this.salesInvoices.filter(i => i.status !== 'PAID').reduce((sum, inv) => sum + (parseFloat(inv.total_amount) - parseFloat(inv.paid_amount)), 0);
        },
        totalPaidInvoices() {
            return this.salesInvoices.reduce((sum, inv) => sum + parseFloat(inv.paid_amount || 0), 0);
        },

        localizedViewName() {
            const views = {
                'dashboard': { ar: 'لوحة التحكم', en: 'Dashboard' },
                'org_builder': { ar: 'هيكلة المنظمة', en: 'Org Builder' },
                'inventory_module': { ar: 'RIMS (المخزون)', en: 'RIMS (Inventory)' },
                'procurement_module': { ar: 'RPMS (المشتريات)', en: 'RPMS (Procurement)' },
                'sales_module': { ar: 'إدارة المبيعات', en: 'Sales & CRM' },
                'accounting_module': { ar: 'المحاسبة والمالية', en: 'Accounting' },
                'global_config': { ar: 'إعدادات النظام', en: 'Global Settings' },
                'users': { ar: 'إدارة المستخدمين', en: 'User Management' },
                'item_master': { ar: 'سجل الأصناف', en: 'Item Master' },
                'vendors_list': { ar: 'سجل الموردين', en: 'Vendors' },
                'vendor_ledger': { ar: 'كشف حساب مورد', en: 'Vendor Ledger' }
            };
            const current = views[this.view] || { ar: this.view, en: this.view };
            return this.isArabic ? current.ar : current.en;
        },

        displayMoves() {
            // ... same logic as before, just used for the main list
            let list = this.filteredMovesForStats || [];
            const filters = this.forms.stock_entry;
            
            // Apply Type Filter only for the list/table display
            if (filters.filterType !== 'ALL') {
                list = list.filter(m => m.move_type === filters.filterType);
            }

            // 5. Grouping/Sorting logic
            if (filters.groupBy === 'material') {
                list = [...list].sort((a, b) => (a.material_name || '').localeCompare(b.material_name || ''));
            } else if (filters.groupBy === 'contact') {
                list = [...list].sort((a, b) => (a.vendor_name || a.customer_name || '').localeCompare(b.vendor_name || b.customer_name || ''));
            } else {
                list = [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
            }
            
            return list;
        },

        filteredMovesForStats() {
            let list = this.inventoryMoves || [];
            const filters = this.forms.stock_entry;
            
            // 1. Filter by Date Range
            if (filters.date_from) {
                list = list.filter(m => m.created_at.split('T')[0] >= filters.date_from);
            }
            if (filters.date_to) {
                list = list.filter(m => m.created_at.split('T')[0] <= filters.date_to);
            }

            // 2. Filter by Contact Search
            if (filters.contact_search) {
                const q = filters.contact_search.toLowerCase();
                list = list.filter(m => 
                    (m.vendor_name && m.vendor_name.toLowerCase().includes(q)) ||
                    (m.customer_name && m.customer_name.toLowerCase().includes(q))
                );
            }

            // 3. Filter by Global Search
            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                list = list.filter(m => 
                    (m.material_name && m.material_name.toLowerCase().includes(q)) ||
                    (m.reference && m.reference.toLowerCase().includes(q))
                );
            }
            
            // Sort by date desc by default
            return [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        },

        contactAggregates() {
            // ✅ Fix: Use displayMoves instead of inventoryMoves so top filters work on aggregation too
            const list = this.displayMoves || [];
            const aggregates = {};

            list.forEach(m => {
                const contactId = m.customer || m.vendor;
                const contactName = m.vendor_name || (m.customer_name) || (m.customer ? this.customers.find(c => c.id === m.customer)?.name : null) || 'Unknown';
                
                if (!contactId && !m.vendor_name) return;

                const key = contactId ? `id_${contactId}` : `name_${m.vendor_name}`;
                if (!aggregates[key]) {
                    aggregates[key] = {
                        name: contactName,
                        id: contactId,
                        in_qty: 0,
                        out_qty: 0,
                        total_qty: 0,
                        total_value: 0,
                        move_count: 0
                    };
                }

                const qty = parseFloat(m.quantity) || 0;
                if (m.move_type === 'IN') {
                    aggregates[key].in_qty += qty;
                    aggregates[key].total_qty += qty;
                    aggregates[key].total_value += (qty * (parseFloat(m.unit_cost) || 0));
                } else {
                    aggregates[key].out_qty += qty;
                    aggregates[key].total_qty -= qty;
                    aggregates[key].total_value += (qty * (parseFloat(m.sales_price) || 0));
                }
                aggregates[key].move_count++;
            });

            return Object.values(aggregates).sort((a, b) => b.total_value - a.total_value);
        },

        // --- Manual Move Totals ---
        manualMoveTotalBeforeTax() {
            const entry = this.forms.stock_entry;
            if (!entry || !entry.items) return 0;
            return entry.items.reduce((sum, item) => {
                const qty = parseFloat(item.quantity) || 0;
                const price = entry.receipt_type === 'PURCHASE' ? (parseFloat(item.unit_cost) || 0) : (parseFloat(item.sales_price) || 0);
                return sum + (qty * price);
            }, 0);
        },
        manualMoveTaxAmount() {
            const entry = this.forms.stock_entry;
            const rate = (parseFloat(entry.tax_rate) || 0) / 100;
            return this.manualMoveTotalBeforeTax * rate;
        },
        manualMoveGrandTotal() {
            return this.manualMoveTotalBeforeTax + this.manualMoveTaxAmount;
        }
    },

    watch: {
        activeOpcoId(newId) {
            if (newId) this.syncGlobalConfig(newId);
        }
    },

    mounted() {
        // إضافة مستمع للنقرات الخارجية لإغلاق القوائم المنسدلة
        document.addEventListener('mousedown', (e) => {
            const brandArea = document.querySelector('.brand-area-container');
            if (brandArea && !brandArea.contains(e.target)) {
                this.showBrandDropdown = false;
            }
            
            const notifArea = document.querySelector('.notif-area-container');
            if (notifArea && !notifArea.contains(e.target)) {
                this.showNotificationsDropdown = false;
            }
        });
        
        // Initial KPI calculation
        this.refreshKpis();
    },

    methods: {
        async fetchInventoryMoves() {
            try {
                const url = this.activeOpcoId ? `/api/wms/moves/?opco=${this.activeOpcoId}` : '/api/wms/moves/';
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.inventoryMoves = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) { console.error("Moves Fetch Error", e); }
        },

        printMove(move) {
            this.showToast(this.isArabic ? "جاري تحضير الطباعة..." : "Preparing Print...", "info");
            window.open(`/api/wms/moves/${move.id}/print/`, '_blank');
        },

        editMove(move) {
            this.isEditing = true;
            this.modalType = 'stock_entry';
            this.activeOperation = 'manual';
            this.forms.stock_entry = {
                id: move.id,
                receipt_type: move.move_type === 'IN' ? 'PURCHASE' : 'ISSUE',
                items: [{ 
                    material_id: move.material_id || move.material, 
                    material_name: move.material_name,
                    quantity: parseFloat(move.quantity) || 0, 
                    unit_cost: parseFloat(move.unit_cost) || 0,
                    sales_price: parseFloat(move.sales_price) || 0
                }],
                bin_id: move.dest_bin || move.source_bin || '',
                contact_id: (move.vendor && typeof move.vendor === 'object') ? move.vendor.id : (move.vendor || ''),
                manual_contact_name: move.vendor_name || '',
                reference: move.reference || '',
                payment_method: move.payment_method || 'CASH',
                tax_rate: parseFloat(move.tax_rate) || 15
            };
            this.showModal = true;
        },

        manualMoveSubtotal(item) {
            const price = this.forms.stock_entry.receipt_type === 'PURCHASE' ? (item.unit_cost || 0) : (item.sales_price || 0);
            return (item.quantity || 0) * price;
        },
        
        async fetchLastPrice(item) {
            if (!item.material_id) return;
            try {
                const moveType = this.forms.stock_entry.receipt_type === 'PURCHASE' ? 'IN' : 'OUT';
                const url = `/api/wms/moves/last_price/?material_id=${item.material_id}&move_type=${moveType}&opco=${this.activeOpcoId}`;
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    if (this.forms.stock_entry.receipt_type === 'PURCHASE') {
                        item.unit_cost = data.price;
                    } else {
                        item.sales_price = data.price;
                    }
                }
            } catch (e) { console.error("Last Price Error:", e); }
        },

        formatCurrency(value) {
            const currency = (this.activeOpco && this.activeOpco.currency) ? this.activeOpco.currency.toUpperCase() : 'SAR';
            return new Intl.NumberFormat(this.isArabic ? 'ar-SA' : 'en-US', {
                style: 'currency',
                currency: currency,
                maximumFractionDigits: 0
            }).format(value || 0);
        },

        refreshKpis() {
            // 📦 1. حسابات المخزون (Inventory)
            this.kpis.inventory.total_items = (this.materials_list || []).length;
            this.kpis.inventory.stock_qty = (this.inventoryList || []).reduce((acc, item) => acc + (item.quantity || 0), 0);
            
            this.kpis.inventory.critical_items = (this.inventoryList || []).filter(item => {
                const material = (this.materials_list || []).find(m => m.id === item.material_id);
                return material && (item.quantity < (material.reorder_level || 5));
            }).length;
            
            this.kpis.inventory.dead_stock = (this.inventoryList || []).filter(item => item.quantity > 500).length;

            // 💰 2. حسابات المبيعات (Sales)
            const soData = this.salesOrders || [];
            this.kpis.sales.total = soData.reduce((acc, so) => acc + (parseFloat(so.grand_total || so.total_amount) || 0), 0);
            this.kpis.sales.delivered = soData.filter(so => so.status === 'DELIVERED').reduce((acc, so) => acc + (parseFloat(so.grand_total) || 0), 0);
            this.kpis.sales.remaining_delivery = this.kpis.sales.total - this.kpis.sales.delivered;
            
            const invData = this.salesInvoices || [];
            this.kpis.sales.invoiced = invData.reduce((acc, inv) => acc + (parseFloat(inv.total_amount) || 0), 0);
            this.kpis.sales.remaining_invoice = this.kpis.sales.total - this.kpis.sales.invoiced;

            // 🛒 3. حسابات المشتريات (Procurement)
            const poData = this.purchase_orders || [];
            this.kpis.procurement.total = poData.reduce((acc, po) => acc + (parseFloat(po.total_amount) || 0), 0);
            this.kpis.procurement.received = poData.filter(po => po.status === 'RECEIVED').reduce((acc, po) => acc + (parseFloat(po.total_amount) || 0), 0);
            this.kpis.procurement.invoiced = this.kpis.procurement.received * 0.9; 
            this.kpis.procurement.paid = this.kpis.procurement.invoiced * 0.8;

            // 🏦 4. حسابات المالية (Finance)
            this.kpis.finance.invoices = this.kpis.sales.invoiced;
            this.kpis.finance.collected = invData.reduce((acc, inv) => acc + (parseFloat(inv.paid_amount || 0)), 0);
            this.kpis.finance.remaining = this.kpis.finance.invoices - this.kpis.finance.collected;

            // 👥 عدادات إضافية
            this.kpis.vendors = (this.vendors || []).length;
            this.kpis.customers_count = (this.customers || []).length;
        },
        ...utils.methods,
        ...itemMasterModule.methods,

        // داخل methods في main.js
        // ابحث عن generateItemReport واستبدلها بهذا الكود
        // داخل قسم methods في ملف main.js
        startOperation(type) {
            // 1. تحديد التابة النشطة في المودال
            this.activeOperation = type;

            // 2. مصفوفة العمليات التي تعتبر "إضافة" (Incoming)
            const incomingOps = ['po_receipt', 'mrp_receipt', 'so_return', 'incoming_transfer'];

            // 3. تهيئة كائن الـ stock_entry وتحديد نوع الحركة فوراً
            if (!this.forms.stock_entry) {
                this.forms.stock_entry = { items: [], po_id: '' };
            }

            // هنا السر: لو العملية في قائمة الإضافة، النوع IN، غير كدة OUT
            this.forms.stock_entry.move_type = incomingOps.includes(type) ? 'IN' : 'OUT';

            // تصفير البيانات للبدء في عملية جديدة
            this.forms.stock_entry.items = [{ material_id: '', quantity: 1, unit_cost: 0, sales_price: 0 }];
            this.forms.stock_entry.po_id = '';
            this.forms.stock_entry.payment_method = 'CASH';
            this.forms.stock_entry.tax_rate = 15;

            // لو العملية شراء، نجهز أوامر التوريد
            if (type === 'po_receipt') {
                this.fetchPendingPOs();
            }

            // لو العملية مبيعات، نجهز أوامر البيع القابلة للصرف
            if (type === 'so_delivery') {
                this.fetchSalesOrders();
            }
            
            this.showModal = true;
            this.modalType = 'stock_entry';
        },

        async generateItemReport() {
            // 1. التحقق من اختيار صنف أولاً
            if (!this.reportFilters.material_id) {
                alert(this.isArabic ? 'برجاء اختيار الصنف أولاً' : 'Please select a material first');
                return;
            }

            this.loading = true; // تشغيل علامة التحميل (Spinner)

            try {
                // 2. تجهيز روابط البحث (Query Parameters)
                const params = new URLSearchParams({
                    material_id: this.reportFilters.material_id,
                    date_from: this.reportFilters.date_from || '',
                    date_to: this.reportFilters.date_to || '',
                    location_id: this.reportFilters.location_id || ''
                });

                // 3. طلب البيانات من السيرفر (تأكد أن الرابط مطابق لـ urls.py)
                const response = await fetch(`/api/wms/moves/?${params.toString()}`);

                if (!response.ok) throw new Error('Network response was not ok');

                const data = await response.json();

                // 4. وضع البيانات في المصفوفة لعرضها في الجدول
                this.inventoryMoves = data;

            } catch (error) {
                console.error("Error generating report:", error);
                alert(this.isArabic ? 'حدث خطأ أثناء جلب البيانات' : 'Error fetching report data');
            } finally {
                this.loading = false; // إيقاف علامة التحميل
            }
        },


        async fetchPurchaseOrders() {
            try {
                const url = this.activeOpcoId
                    ? `/api/orders/?opco=${this.activeOpcoId}`
                    : '/api/orders/';
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    // 🚀 التعديل هنا: إضافة showDetails لكل أمر توريد عشان الـ Expand يشتغل
                    const list = Array.isArray(data) ? data : (data.results || []);
                    this.purchase_orders = list.map(po => ({
                        ...po,
                        showDetails: false // الحالة الافتراضية للتفاصيل إنها مقفولة
                    }));
                }
            } catch (e) {
                console.error("Error fetching POs:", e);
            }
        },

        // --- Sales Module Methods ---
        async fetchSalesData() {
            this.loading = true;
            await Promise.all([
                this.fetchCustomers(),
                this.fetchSalesOrders(),
                this.fetchSalesInvoices(),
                this.fetchPayments()
            ]);
            this.loading = false;
        },
        async fetchCustomers() {
            const url = this.activeOpcoId ? `/api/customers/?opco=${this.activeOpcoId}` : '/api/customers/';
            try {
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.customers = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) { console.error("Error fetching customers:", e); }
        },

        async fetchSalesOrders() {
            const url = this.activeOpcoId ? `/api/sales-orders/?opco=${this.activeOpcoId}` : '/api/sales-orders/';
            try {
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    // 🚀 إضافة الخاصية هنا ضروري جداً
                    this.salesOrders = data.map(so => ({
                        ...so,
                        showDetails: false
                    }));
                }
            } catch (e) { console.error("Error fetching SOs:", e); }
        },

        async fetchSalesInvoices() {
            const url = this.activeOpcoId ? `/api/sales-invoices/?opco=${this.activeOpcoId}` : '/api/sales-invoices/';
            try {
                const res = await fetch(url);
                if (res.ok) this.salesInvoices = await res.json();
            } catch (e) { console.error("Error fetching sales invoices:", e); }
        },

        async generateInvoice(so) {
            this.showToast(this.isArabic ? "جاري إصدار الفاتورة..." : "Generating invoice...", "success");
            try {
                const res = await fetch(`/api/sales-orders/${so.id}/generate_invoice/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': this.getCookie('csrftoken'),
                        'Content-Type': 'application/json'
                    }
                });
                const data = await res.json();
                if (res.ok) {
                    this.showToast(this.isArabic ? "تم إصدار الفاتورة بنجاح" : "Invoice generated successfully", "success");
                    await this.fetchSalesOrders();
                    await this.fetchSalesInvoices();
                    await this.fetchCustomers(); // لتحديث أرصدة العملاء فوراً
                } else {
                    this.showToast(data.error || (this.isArabic ? "فشل إصدار الفاتورة" : "Failed to generate invoice"), "error");
                }
            } catch (e) {
                console.error("Error generating invoice:", e);
                this.showToast("Network Error", "error");
            }
        },

        async fetchPayments() {
            try {
                const res = await fetch('/api/customer-payments/');
                if (res.ok) this.customerPayments = await res.json();
            } catch (e) {
                console.error("Error fetching payments:", e);
            }
        },
        getStatusClass(status) {
            const classes = {
                'DRAFT': 'bg-slate-50 text-slate-500 border-slate-200',
                'CONFIRMED': 'bg-blue-50 text-blue-600 border-blue-200',
                'DELIVERED': 'bg-emerald-50 text-emerald-600 border-emerald-200',
                'SHIPPED': 'bg-indigo-50 text-indigo-600 border-indigo-200',
                'UNPAID': 'bg-rose-50 text-rose-600 border-rose-200',
                'PAID': 'bg-emerald-50 text-emerald-600 border-emerald-200',
                'PARTIAL': 'bg-amber-50 text-amber-600 border-amber-200',
                'CANCELLED': 'bg-red-50 text-red-600 border-red-200'
            };
            return classes[status] || 'bg-slate-50 text-slate-400 border-slate-200';
        },
        formatNumber(num) {
            return parseFloat(num || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        },

        async fetchVendors() {
            try {
                const url = this.activeOpcoId
                    ? `/api/vendors/?opco=${this.activeOpcoId}`
                    : '/api/vendors/';
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.vendors = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) {
                console.error("Error fetching vendors:", e);
            }
        },

        async fetchVendorLedger(vendor) {
            this.loading = true;
            try {
                const res = await fetch(`/api/vendors/${vendor.id}/ledger/`);
                if (res.ok) {
                    this.vendorLedger = await res.json();
                    this.selectedVendor = vendor;
                    this.view = 'vendor_ledger';
                }
            } catch (e) {
                console.error("Error fetching ledger:", e);
                this.showToast(this.isArabic ? "خطأ في جلب كشف الحساب" : "Error fetching ledger", 'error');
            } finally {
                this.loading = false;
            }
        },

        calculatePOTotal(po) {
            if (!po.lines || po.lines.length === 0) return '0.00';
            const total = po.lines.reduce((sum, line) => sum + (line.quantity * line.unit_price), 0);
            return total.toFixed(2);
        },

        // 🚀 إضافة دالة الطباعة (Print)
        printPO(poId) {
            this.showToast(this.isArabic ? "جاري تحضير ملف الطباعة..." : "Preparing document...", "success");
            // الرابط ده المفروض يفتح صفحة الـ PDF اللي جانغو بيعملها
            window.open(`/print/po/${poId}/`, '_blank');
        },

        printSO(id) {
            window.open(`/print/so/${id}/`, '_blank');
        },

        printGRN(receiptId) {
            this.showToast(this.isArabic ? "جاري تجهيز إذن الاستلام للطباعة..." : "Preparing GRN document...", "success");
            window.open(`/print/grn/${receiptId}/`, '_blank');
        },

        printDelivery(deliveryId) {
            if (!deliveryId || deliveryId === 'undefined') {
                this.showToast(this.isArabic ? "خطأ: رقم الإذن غير موجود" : "Error: Delivery ID is missing", 'error');
                return;
            }
            this.showToast(this.isArabic ? "جاري تجهيز إذن الصرف للطباعة..." : "Preparing Delivery Note...", "success");
            window.open(`/print/delivery/${deliveryId}/`, '_blank');
        },

        // 🚀 1. الدالة اللي كانت مفقودة وعاملة الإيرور (ربط الانتر)
        processBarcodeManual() {
            if (!this.barcodeQuery) return;
            this.processScannedBarcode(this.barcodeQuery.trim());
        },

        // 🚀 2. دالة تشغيل الكاميرا (النسخة الذكية لـ EAN-13)
        startCameraScan() {
            this.isScanning = true;
            this.$nextTick(() => {
                if (this.scannerInstance) {
                    try { this.scannerInstance.clear(); } catch (e) { }
                }

                this.scannerInstance = new Html5Qrcode("reader", {
                    formatsToSupport: [Html5QrcodeSupportedFormats.EAN_13]
                });

                const config = {
                    fps: 10,
                    qrbox: { width: 300, height: 120 },
                    experimentalFeatures: {
                        useBarCodeDetectorIfSupported: true
                    }
                };

                this.scannerInstance.start(
                    { facingMode: "environment" },
                    config,
                    (decodedText) => {
                        if (this.scannerInstance && this.scannerInstance.getState() === Html5QrcodeScannerState.SCANNING) {
                            this.scannerInstance.pause();
                        }
                        this.processScannedBarcode(decodedText);
                    }
                ).catch(err => {
                    console.error("Camera Error:", err);
                    this.isScanning = false;
                });
            });
        },

        // 🚀 3. الدالة الذكية للبحث في قاعدة البيانات ثم أمر التوريد
        processScannedBarcode(barcode) {
            if (!this.forms.stock_entry.items || this.forms.stock_entry.items.length === 0) {
                this.showToast(this.isArabic ? "برجاء اختيار أمر التوريد أولاً" : "Select PO first", 'error');
                if (this.scannerInstance && this.isScanning) this.scannerInstance.resume();
                return;
            }

            const matchedMaterial = this.materials_list.find(
                m => (m.barcode && m.barcode.toString() === barcode.toString()) ||
                    (m.sku && m.sku.toLowerCase() === barcode.toLowerCase()) ||
                    (m.id && m.id.toString() === barcode.toString())
            );

            if (!matchedMaterial) {
                this.showToast(this.isArabic ? `الباركود (${barcode}) غير مسجل في بيانات الأصناف!` : `Barcode not registered!`, 'error');
                this.barcodeQuery = '';
                if (this.scannerInstance && this.isScanning) {
                    setTimeout(() => this.scannerInstance.resume(), 1500);
                }
                return;
            }

            const foundItemInPO = this.forms.stock_entry.items.find(
                item => item.material_id === matchedMaterial.id || item.sku === matchedMaterial.sku
            );

            if (foundItemInPO) {
                this.scannedItemData = {
                    material_id: foundItemInPO.material_id,
                    material_name: foundItemInPO.material_name,
                    sku: foundItemInPO.sku,
                    ordered_qty: foundItemInPO.ordered_qty,
                    scan_qty: 1
                };
                this.showQtyModal = true;
                this.barcodeQuery = '';

                setTimeout(() => {
                    if (this.$refs.qtyInput) {
                        this.$refs.qtyInput.focus();
                        this.$refs.qtyInput.select();
                    }
                }, 400);

            } else {
                this.showToast(this.isArabic ? `الصنف (${matchedMaterial.name}) غير مطلوب في أمر التوريد الحالي!` : `Item not in this PO!`, 'error');
                this.barcodeQuery = '';
                if (this.scannerInstance && this.isScanning) {
                    setTimeout(() => this.scannerInstance.resume(), 1500);
                }
            }
        },

        // 🚀 4. تأكيد الكمية
        confirmScannedQty() {
            const itemIndex = this.forms.stock_entry.items.findIndex(
                i => i.material_id === this.scannedItemData.material_id
            );

            if (itemIndex !== -1) {
                const item = this.forms.stock_entry.items[itemIndex];
                const balance = item.ordered_qty - (item.received_before || 0);
                const addedQty = parseFloat(this.scannedItemData.scan_qty) || 1;
                const currentInForm = parseFloat(item.received_qty) || 0;

                // 🛡️ صمام الأمان: منع استلام كمية أكبر من المتبقي
                if ((currentInForm + addedQty) > balance) {
                    this.showToast(
                        this.isArabic
                            ? `خطأ: الكمية المتبقية هي ${balance} فقط!`
                            : `Error: Remaining balance is only ${balance}!`,
                        'error'
                    );
                    return; // وقف العملية
                }

                item.received_qty = currentInForm + addedQty;
                this.showToast(this.isArabic ? `تم إضافة ${addedQty}` : `Added ${addedQty}`, 'success');
            }

            this.closeQtyModal();
        },

        // 🚀 5. إغلاق النافذة
        closeQtyModal() {
            this.showQtyModal = false;
            if (this.scannerInstance && this.isScanning) {
                if (this.scannerInstance.getState() === Html5QrcodeScannerState.PAUSED) {
                    this.scannerInstance.resume();
                }
            }
        },

        // 🚀 6. إيقاف الكاميرا
        async stopScanner() {
            if (this.scannerInstance) {
                try {
                    await this.scannerInstance.stop();
                    this.scannerInstance = null;
                    this.isScanning = false;
                } catch (err) {
                    console.warn("Stop failed:", err);
                }
            }
        },

        // 🚀 دالة تحميل قالب الاستيراد (Template)
        downloadTemplate() {
            // أسماء الأعمدة (لازم الباك-إند يكون متبرمج يقرأ الأسماء دي بالظبط)
            const headers = ['SKU*', 'Name*', 'Category', 'Base_UOM', 'Barcode', 'Tracking'];

            // صف تجريبي عشان المستخدم يفهم الفورمات
            const exampleRow = ['ITEM-001', 'مثال: أسمنت بورتلاندي', 'Raw Materials', 'BAG', '123456789012', 'none'];

            // تجميع الملف
            let csvContent = "data:text/csv;charset=utf-8,\uFEFF"
                + headers.join(",") + "\n"
                + exampleRow.join(",");

            // إنشاء الرابط وتنزيل الملف
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `Item_Import_Template.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();

            this.showToast(this.isArabic ? "تم تحميل قالب الاستيراد" : "Template downloaded", "success");
        },

        // 1. دوال التحكم في سطور أمر التوريد
        addPOLine() {
            this.forms.po.lines.push({ material: '', quantity: 1, unit_price: 0 });
        },
        removePOLine(index) {
            if (this.forms.po.lines.length > 1) {
                this.forms.po.lines.splice(index, 1);
            } else {
                this.showToast(this.isArabic ? "يجب أن يحتوي الأمر على صنف واحد على الأقل" : "PO must have at least one line", 'error');
            }
        },

        // --- Sales Order Line Management ---
        addSalesOrderLine() {
            this.forms.salesorder.lines.push({ material: '', quantity: 1, unit_price: 0 });
        },
        removeSalesOrderLine(index) {
            if (this.forms.salesorder.lines.length > 1) {
                this.forms.salesorder.lines.splice(index, 1);
            } else {
                this.showToast(this.isArabic ? "يجب أن يحتوي الأمر على صنف واحد على الأقل" : "SO must have at least one line", 'error');
            }
        },


        exportToExcel() {
            const list = this.filteredMaterials || [];
            if (list.length === 0) {
                this.showToast(this.isArabic ? "لا توجد بيانات لتصديرها" : "No data to export", "error");
                return;
            }

            const headers = this.isArabic
                ? ['المعرف', 'الكود (SKU)', 'اسم الصنف', 'التصنيف', 'وحدة القياس']
                : ['ID', 'SKU', 'Name', 'Category', 'UOM'];

            const rows = list.map(item => [
                item.id,
                item.sku || '---',
                item.name || '---',
                item.category || '---',
                item.base_uom || 'PCS'
            ]);

            let csvContent = "data:text/csv;charset=utf-8,\uFEFF"
                + headers.join(",") + "\n"
                + rows.map(e => e.join(",")).join("\n");

            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `Items_Export.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();

            this.showToast(this.isArabic ? "تم التصدير بنجاح" : "Exported successfully", "success");
        },

        triggerImport() {
            this.$refs.excelInput.click();
        },

        async handleExcelImport(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            formData.append('opco_id', this.activeOpcoId);

            try {
                this.loading = true;
                this.showToast(this.isArabic ? "جاري المعالجة..." : "Processing...", "success");

                const res = await fetch('/api/materials/import/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: formData
                });

                if (res.ok) {
                    await this.fetchMaterialsList(); // تحديث الداتا
                    this.showToast(this.isArabic ? "تم الاستيراد بنجاح" : "Imported successfully", "success");
                } else {
                    this.showToast(this.isArabic ? "فشل الاستيراد، تأكد من الملف" : "Import failed", "error");
                }
            } catch (e) {
                this.showToast("Network Error", "error");
            } finally {
                this.loading = false;
                event.target.value = '';
            }
        },

        getOpcoName(opcoId) {
            const opco = this.allOpcos.find(o => o.id === opcoId);
            return opco ? opco.name : '...';
        },

        getOperationTitle() {
            const titles = {
                'po_receipt': this.isArabic ? 'إضافة من أمر توريد' : 'Purchase Receipt',
                'mrp_receipt': this.isArabic ? 'إضافة من أمر تصنيع' : 'Production Receipt',
                'so_return': this.isArabic ? 'مرتجع من أمر بيع' : 'Sales Return',
                'incoming_transfer': this.isArabic ? 'استلام تحويل مخزني' : 'Incoming Transfer',
                'so_delivery': this.isArabic ? 'صرف لأمر بيع' : 'Sales Delivery',
                'internal_transfer': this.isArabic ? 'تحويل مخزني داخلي' : 'Internal Transfer',
                'mrp_issue': this.isArabic ? 'صرف لأمر تصنيع' : 'Material Issue for Production',
                'scrap': this.isArabic ? 'تسجيل هالك' : 'Scrap Entry',
                'po_return': this.isArabic ? 'مردودات مشتريات' : 'Purchase Return'
            };
            return titles[this.activeOperation] || (this.isArabic ? 'عملية مخزنية' : 'Stock Operation');
        },

        startOperation(type) {
            this.activeOperation = type;
            // 🚀 لو العملية هي استلام من مورد، نادي أوامر التوريد فوراً
            if (type === 'po_receipt') {
                this.fetchPendingPOs();
            }
            // 🚚 لو العملية هي صرف لبيع، نادي أوامر البيع فوراً
            if (type === 'so_delivery') {
                this.fetchPendingSOs();
            }

            if (!this.forms.stock_entry) {
                this.forms.stock_entry = { items: [], po_id: '', so_id: '' };
            } else {
                this.forms.stock_entry.items = [];
                this.forms.stock_entry.po_id = '';
                this.forms.stock_entry.so_id = '';
            }
        },

        goBackToOperations() {
            // 1. إيقاف الكاميرا فوراً وبشكل صحيح
            if (this.isScanning) {
                // بننادي على المكتبة عشان توقف المسح وتنظف الـ DOM
                const html5QrCode = new Html5Qrcode("reader");
                if (html5QrCode.isScanning) {
                    html5QrCode.stop().then(() => {
                        console.log("Camera Stopped");
                    }).catch(err => {
                        console.warn("Stop failed:", err);
                    });
                }
            }

            // 2. تصفير كل الحالات (الـ Variables)
            this.activeOperation = null;
            this.isScanning = false;
            this.barcodeQuery = '';

            // تصفير بيانات الاستلام عشان لو فتحت أمر توريد تاني ميبقاش فيه داتا قديمة
            this.forms.stock_entry = {
                po_id: '',
                items: []
            };

            // إخفاء أي رسائل Toast قديمة
            this.loading = false;
        },

        // 🚀 إضافة اللوجيك الذكي لجلب الـ PO وتحديد الرف بناءً على الشركة
        async fetchPODetails() {
            const poId = this.forms.stock_entry.po_id;
            if (!poId) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/orders/${poId}/`);
                const data = await res.json();
                const currentOpcoId = parseInt(this.activeOpcoId);

                // 🚀 تحديد نوع الحركة "إضافة" فور اختيار الأمر
                this.forms.stock_entry.move_type = 'IN';

                this.forms.stock_entry.items = data.lines.map(i => {
                    const material = this.materials_list.find(m => m.id === i.material);

                    // استخراج الرف الافتراضي
                    let autoSelectedBin = i.default_bin || '';
                    if (!autoSelectedBin && material?.company_assignments) {
                        const assign = material.company_assignments.find(a => parseInt(a.opco_id) === currentOpcoId);
                        autoSelectedBin = assign?.primary_bin || (assign?.bins?.length > 0 ? assign.bins[0] : '');
                    }

                    return {
                        material_id: i.material,
                        material_name: i.material_name || material?.name || 'Unknown',
                        sku: i.material_sku || material?.sku || 'N/A',
                        ordered_qty: parseFloat(i.quantity),          // الطلب الأصلي
                        received_before: parseFloat(i.received_qty || 0), // المستلم سابقاً (من السيرفر)
                        received_qty: 0,                               // الكمية الحالية (صفر مؤقتاً)
                        bin_id: autoSelectedBin
                    };
                });

                this.showToast(this.isArabic ? "تم تحميل تفاصيل الأمر والكميات السابقة" : "PO details and history loaded", 'success');
            } catch (e) {
                this.showToast(this.isArabic ? "خطأ في جلب البيانات" : "Fetch error", 'error');
            } finally {
                this.loading = false;
            }
        },

        // 🚀 دالة جلب تفاصيل أمر البيع للصرف (SO Delivery)
        async fetchSODetailsForDelivery() {
            const soId = this.forms.stock_entry.so_id;
            if (!soId) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/wms/sales-orders/${soId}/`);
                const data = await res.json();
                const currentOpcoId = parseInt(this.activeOpcoId);

                // تحديد نوع الحركة "صرف" فور اختيار الأمر
                this.forms.stock_entry.move_type = 'OUT';

                this.forms.stock_entry.items = data.items.map(i => {
                    const material = this.materials_list.find(m => m.id === i.material_id);

                    // استخراج الرف الرئيسي لجلبه كافتراضي للصرف
                    let autoSelectedBin = '';
                    if (material?.company_assignments) {
                        const assign = material.company_assignments.find(a => parseInt(a.opco_id) === currentOpcoId);
                        autoSelectedBin = assign?.primary_bin || (assign?.bins?.length > 0 ? assign.bins[0] : '');
                    }

                    return {
                        material_id: i.material_id,
                        material_name: i.material_name || material?.name || 'Unknown',
                        sku: i.sku || material?.sku || 'N/A',
                        ordered_qty: parseFloat(i.ordered_qty),          // الطلب الأصلي
                        received_before: parseFloat(i.received_qty || 0), // المصروف سابقاً (من السيرفر)
                        received_qty: 0,                                  // الكمية الحالية (صفر مؤقتاً)
                        bin_id: autoSelectedBin
                    };
                });

                this.showToast(this.isArabic ? "تم تحميل تفاصيل أمر البيع والكميات المنصرفة" : "SO details and delivery history loaded", 'success');
            } catch (e) {
                this.showToast(this.isArabic ? "خطأ في جلب البيانات" : "Fetch error", 'error');
            } finally {
                this.loading = false;
            }
        },

        async fetchPendingPOs() {
            try {
                const url = this.activeOpcoId
                    ? `/api/orders/?status=CONFIRMED&opco=${this.activeOpcoId}`
                    : '/api/orders/?status=CONFIRMED';
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.pending_pos = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) {
                console.error("Error fetching POs:", e);
            }
        },

        async fetchPendingSOs() {
            try {
                const url = this.activeOpcoId
                   ? `/api/sales-orders/?status=CONFIRMED&opco=${this.activeOpcoId}`
                   : '/api/sales-orders/?status=CONFIRMED';
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.salesOrders = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) {
                console.error("Error fetching SOs:", e);
            }
        },

        async fetchStockMoves() {
            try {
                const response = await fetch('/api/wms/moves/');
                if (response.ok) {
                    const data = await response.json();
                    this.inventoryMoves = data;
                }
            } catch (error) {
                console.error("Failed to load moves:", error);
            }
        },
        // دالة لجلب سجل الحركات
        // الدالة الموحدة لجلب الحركات وعرضها في التقارير
        async fetchInventoryMoves() {
            this.loading = true;
            try {
                // نربط الفلاتر بالرابط (URL)
                let url = `/api/wms/moves/?material=${this.reportFilters.material_id}&location=${this.reportFilters.location_id}&from=${this.reportFilters.date_from}&to=${this.reportFilters.date_to}`;

                const response = await fetch(url);
                if (response.ok) {
                    const data = await response.json();
                    this.inventoryMoves = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (error) {
                console.error("Error fetching report:", error);
            } finally {
                this.loading = false;
            }
        },

        async validateReceipt() {
            const entry = this.forms.stock_entry;
            const isDelivery = this.activeOperation === 'so_delivery';

            // 1. التحقق من اختيار أمر التوريد / البيع
            if (!isDelivery && !entry.po_id) {
                this.showToast(this.isArabic ? "برجاء اختيار أمر توريد" : "Please select a PO", 'error');
                return;
            }
            if (isDelivery && !entry.so_id) {
                this.showToast(this.isArabic ? "برجاء اختيار أمر بيع" : "Please select a SO", 'error');
                return;
            }

            // 2. فلترة الأصناف المستلمة / المصروفة
            const itemsToProcess = entry.items.filter(i => parseFloat(i.received_qty) > 0);

            if (itemsToProcess.length === 0) {
                this.showToast(this.isArabic ? (isDelivery ? "يجب إدخال كمية صرف واحدة على الأقل" : "يجب إدخال كمية استلام واحدة على الأقل") : "Enter at least one quantity", 'error');
                return;
            }

            // 🚀 التحقق من الكميات المستلمة/المصروفة سابقا والمتبقية
            for (const item of itemsToProcess) {
                const balance = item.ordered_qty - (item.received_before || 0); // المتبقي الحقيقي
                if (item.received_qty > balance) {
                    this.showToast(
                        this.isArabic
                            ? `خطأ: الكمية المكتوبة لـ (${item.material_name}) وهي ${item.received_qty} أكبر من المتبقي في الأمر (${balance})`
                            : `Error: Quantity for ${item.material_name} exceeds remaining balance`,
                        'error'
                    );
                    return; // وقف العملية فوراً ومنع الإرسال للسيرفر
                }
            }

            // 3. التحقق من الرفوف
            const missingBins = itemsToProcess.filter(i => !i.bin_id);
            if (missingBins.length > 0) {
                this.showToast(this.isArabic ? "برجاء تحديد الرف لكل صنف" : "Select bins", 'error');
                return;
            }

            try {
                this.loading = true;

                // التمييز بين الاستلام والصرف (استخدام الروابط الموحدة الجديدة)
                const apiEndpoint = isDelivery ? '/api/stock-deliveries/' : '/api/stock-receipts/';
                const payload = {
                    opco: this.activeOpcoId,
                    items: itemsToProcess.map(item => ({
                        material: item.material_id, // تغيير material_id إلى material
                        quantity: item.received_qty,
                        storage_bin: item.bin_id    // تغيير bin_id إلى storage_bin
                    }))
                };

                if (isDelivery) {
                    payload.so = entry.so_id;
                } else {
                    payload.po = entry.po_id;
                }

                const response = await fetch(apiEndpoint, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (response.ok) {
                    const docNumber = data.receipt_number || data.delivery_number || "NEW-DOC";

                    this.showToast(
                        this.isArabic ? `تم حفظ الإذن رقم ${docNumber} بنجاح` : `Document ${docNumber} saved`,
                        'success'
                    );

                    // طباعة الإذن فوراً
                    const printMsg = isDelivery ? "هل تريد طباعة إذن الصرف الآن؟" : "هل تريد طباعة إذن الإضافة الآن؟";
                    const printMsgEn = isDelivery ? "Print Delivery Note now?" : "Print GRN now?";
                    if (confirm(this.isArabic ? printMsg : printMsgEn)) {
                        if (isDelivery) {
                            this.printDelivery(data.id);
                        } else {
                            this.printGRN(data.id);
                        }
                    }

                    this.goBackToOperations();
                    await this.refreshAllData();

                } else {
                    throw new Error(data.error || "Server Error");
                }
            } catch (e) {
                console.error("Move Error:", e);
                this.showToast(e.message, 'error');
            } finally {
                this.loading = false;
            }
        },


        async quickAddVendor() {
            const vendorName = prompt(this.isArabic ? "أدخل اسم المورد الجديد:" : "Enter new vendor name:");
            if (!vendorName) return;

            // إنشاء كود مبدئي للمورد
            const vendorCode = "V-" + Math.floor(Math.random() * 10000);

            try {
                this.loading = true;
                const res = await fetch('/api/vendors/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ name: vendorName, code: vendorCode, opco: this.activeOpcoId })
                });

                if (res.ok) {
                    const newVendor = await res.json();
                    this.vendors.push(newVendor); // إضافته للقائمة فوراً
                    this.forms.po.vendor = newVendor.id; // اختياره تلقائياً في الفورم
                    this.showToast(this.isArabic ? "تم إضافة المورد بنجاح" : "Vendor added", "success");
                }
            } catch (e) {
                this.showToast("Error adding vendor", "error");
            } finally {
                this.loading = false;
            }
        },

        // 🚀 دالة تنسيق التاريخ عشان الجدول يظهر بشكل شيك وميضربش إيرور
        formatDate(dateStr) {
            if (!dateStr) return '---';
            const date = new Date(dateStr);
            return date.toLocaleDateString('ar-EG', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        // أضف هذه الدوال داخل methods
        addCompanyRow() {
            // التأكد من وجود الكائن والمصفوفة أولاً لتجنب الـ TypeError
            if (!this.forms.material.company_assignments) {
                this.forms.material.company_assignments = [];
            }

            this.forms.material.company_assignments.push({
                opco_id: '',
                bins: [],
                primary_bin: null
            });
        },

        getBinsByOpco(opcoId) {
            if (!opcoId) return [];
            return this.bins.filter(bin => {
                const location = this.locations.find(l => l.id === bin.storage_location);
                const plant = location ? this.plants.find(p => p.id === location.plant) : null;
                return plant && parseInt(plant.opco) === parseInt(opcoId);
            });
        },

        addBinToRow(index, event) {
            const binId = parseInt(event.target.value);
            if (!binId) return;
            const row = this.forms.material.company_assignments[index];
            if (!row.bins.includes(binId)) {
                row.bins.push(binId);
            }
            event.target.value = ""; // تصفير الاختيار بعد الإضافة
        },

        removeBinFromRow(rowIndex, binId) {
            const row = this.forms.material.company_assignments[rowIndex];
            row.bins = row.bins.filter(id => id !== binId);
            if (row.primary_bin === binId) row.primary_bin = null;
        },

        getBinCodeById(binId) {
            const bin = this.bins.find(b => b.id === binId);
            return bin ? bin.code : '...';
        },

        // 🚀 نظام التنبيهات الاحترافي في منتصف الشاشة
        showToast(message, type = 'success') {
            console.log("Toast Triggered:", message, type);
            const toast = document.createElement('div');
            toast.className = `custom-toast ${type}`;
            toast.style.cssText = "position:fixed; top:50%; left:50%; transform:translate(-50%, -50%); z-index:9999; padding:20px; color:white; border-radius:10px; text-align:center; min-width:200px; box-shadow: 0 15px 35px rgba(0,0,0,0.3);";
            toast.style.backgroundColor = type === 'success' ? '#28a745' : '#dc3545';

            toast.innerHTML = `
                <div class="toast-content">
                    <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-triangle'}" style="font-size: 2.5rem;"></i>
                    <div style="margin-top:10px; font-weight:600;">${message}</div>
                </div>
            `;
            document.body.appendChild(toast);

            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transition = 'opacity 0.5s ease';
                setTimeout(() => toast.remove(), 500);
            }, 3000);
        },

        async switchCompany(companyId) {
            try {
                this.loading = true;
                const response = await fetch('/api/switch-company/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ company_id: companyId })
                });

                const data = await response.json();

                if (data.success) {
                    this.activeOpcoId = companyId;
                    window.location.reload();
                } else {
                    // ✅ استخدام التنبيه الاحترافي
                    this.showToast(this.isArabic ? "عذراً، لا تملك صلاحية الوصول لهذه الشركة" : "Access denied for this company", 'error');
                }
            } catch (error) {
                console.error("Switch Company Error:", error);
                this.showToast(this.isArabic ? "حدث خطأ أثناء التبديل" : "Error while switching", 'error');
            } finally {
                this.loading = false;
            }
        },

        getPlantNameByBin(binId) {
            const bin = this.bins.find(b => b.id === binId);
            if (!bin) return '...';
            const location = this.locations.find(l => l.id === bin.storage_location);
            if (!location) return '...';
            const plant = this.plants.find(p => p.id === location.plant);
            return plant ? plant.name : '...';
        },

        fixImagePath(path) {
            if (!path) return null;
            if (path.includes('localhost') || path.includes('127.0.0.1')) {
                const parts = path.split('/media/');
                return '/media/' + parts[1];
            }
            if (!path.startsWith('http') && !path.startsWith('/')) {
                return '/' + path;
            }
            return path;
        },

        getCookie(name) {
            let cookieValue = null;
            if (document.cookie && document.cookie !== '') {
                const cookies = document.cookie.split(';');
                for (let i = 0; i < cookies.length; i++) {
                    const cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        },

        syncGlobalConfig(opcoId) {
            if (!opcoId || this.allOpcos.length === 0) return;

            const active = this.allOpcos.find(o => o.id === parseInt(opcoId));
            if (active) {
                const finalLogo = this.fixImagePath(active.logo);
                this.config = {
                    company_name: active.name || '',
                    is_holding: !!active.is_holding,
                    tax_id: active.tax_id || '',
                    cr_number: active.cr_number || '',
                    logo: finalLogo
                };
                this.imagePreview = finalLogo;
            }
        },

        startClock() { utils.methods.startClock(this); },
        triggerReadySystem() { utils.methods.triggerReadySystem(this); },

        handleImageUpload(event) {
            const file = event.target.files[0];
            if (!file) return;

            this.selectedFile = file;
            const reader = new FileReader();
            reader.onload = (e) => {
                this.imagePreview = e.target.result;
            };
            reader.readAsDataURL(file);

            if (this.modalType === 'material' || this.view === 'item_master') {
                itemMasterModule.methods.handleImageUpload(event, this);
            }
        },

        handleLogoUpload(event) {
            const file = event.target.files[0];
            if (file) {
                this.newLogoFile = file;
                const previewUrl = URL.createObjectURL(file);
                this.imagePreview = previewUrl;
                this.config.logo = previewUrl;
            }
        },

        async openItemCard(item) { await inventoryModule.methods.openItemCard(item, this); },
        addItemRow() { inventoryModule.methods.addItemRow(this); },
        removeItemRow(index) { inventoryModule.methods.removeItemRow(index, this); },
        async fetchSODetails() { await inventoryModule.methods.fetchSODetails(this); },
        onSOMaterialSelect() { inventoryModule.methods.onSOMaterialSelect(this); },

        getPlantsForOpco(id) { return orgModule.methods.getPlantsForOpco(this, id); },
        getLocationsForPlant(id) { return orgModule.methods.getLocationsForPlant(this, id); },
        getBinsForLocation(id) { return orgModule.methods.getBinsForLocation(this, id); },
        getBinsCount(id) { return orgModule.methods.getBinsCount(this, id); },
        handleDrop(targetType, parentId) { orgModule.methods.handleDrop(this, targetType, parentId); },
        onDragStart(type) { this.draggedType = type; },
        startDrag(type) { this.onDragStart(type); },

        editMaterial(material) {
            itemMasterModule.methods.editMaterial(material, this);
        },

        editItem(type, item) {

            if (type === 'po' && ['Received', 'Confirmed'].includes(item.status)) {
                this.showToast(
                    this.isArabic ? "لا يمكن تعديل أمر توريد تم استلامه أو تأكيده" : "Cannot edit a Received/Confirmed PO",
                    "error"
                );
                return;
            }

            this.isEditing = true;
            this.modalType = type;
            this.showModal = true;

            if (type === 'material') {
                const itemData = JSON.parse(JSON.stringify(item));

                this.forms.material = {
                    id: itemData.id,
                    sku: itemData.sku,
                    name: itemData.name,
                    category: itemData.category,
                    base_uom: itemData.base_uom,
                    barcode: itemData.barcode,
                    tracking: itemData.tracking || 'none',
                    reorder_level: itemData.reorder_level || 0,
                    max_level: itemData.max_level || 0,
                    standard_price: itemData.standard_price || 0,
                    // 🚀 التعديل الجوهري هنا لملء الجدول الديناميكي عند التعديل
                    // نحول البيانات المسطحة القادمة من السيرفر إلى مصفوفة الـ Assignments
                    company_assignments: itemData.company_assignments || [
                        {
                            opco_id: itemData.opco,
                            bins: itemData.storage_locations_ids || [],
                            primary_bin: itemData.current_primary_bin || null
                        }
                    ]
                };

                if (item.image) {
                    this.imagePreview = this.fixImagePath(item.image);
                } else {
                    this.imagePreview = null;
                }
            } else {
                this.forms[type] = JSON.parse(JSON.stringify(item));
            }
        },

        setPrimaryBin(binId) {
            // 1. تحديث قيمة الرف الرئيسي في نموذج الصنف
            this.forms.material.primary_bin = binId;

            // 2. التأكد من أن الرف المختار كـ Primary موجود أصلاً في قائمة الرفوف المختارة
            if (!this.forms.material.assigned_bins.includes(binId)) {
                this.forms.material.assigned_bins.push(binId);
            }

            // 3. تنبيه بصرى سريع للمستخدم
            this.showToast(
                this.isArabic ? "تم تحديد الرف كوجهة افتراضية للاستلام" : "Primary bin set for Putaway",
                'success'
            );
        },

        // دالة محسنة لاختيار/إلغاء اختيار الرفوف
        toggleBinSelection(binId) {
            const index = this.forms.material.assigned_bins.indexOf(binId);
            if (index > -1) {
                // إذا كان المستخدم يلغي اختيار رف هو أصلاً الرف الرئيسي
                if (this.forms.material.primary_bin === binId) {
                    this.forms.material.primary_bin = null;
                }
                this.forms.material.assigned_bins.splice(index, 1);
            } else {
                this.forms.material.assigned_bins.push(binId);
            }
        },

        async deleteItem(type, id) {
            // 🛡️ صمام الأمان: حماية الكيان الأساسي من الحذف
            if (type === 'opco') {
                const targetOpco = (this.opcos || []).find(o => o.id === id);

                // منع حذف الشركة إذا كانت هي القابضة (Holding) أو الشركة الأم (التي ليس لها Parent)
                if (targetOpco && (targetOpco.is_holding || !targetOpco.parent)) {
                    this.showToast(
                        this.isArabic ? "لا يمكن حذف الشركة الأساسية للمنظومة" : "The primary entity cannot be deleted",
                        'error'
                    );
                    return; // إيقاف العملية فوراً
                }
            }

            // 1️⃣ إظهار المودال المخصص للتأكيد
            this.confirmModal.show = true;

            // 2️⃣ تعريف وظيفة "عند التأكيد" (Logic الحذف الفعلي)
            this.confirmModal.onConfirm = async () => {
                this.confirmModal.show = false; // إخفاء المودال فوراً
                try {
                    this.loading = true;
                    const res = await fetch(`/api/${type}s/${id}/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': this.getCookie('csrftoken')
                        }
                    });

                    if (res.ok) {
                        // تحديث البيانات في الواجهة
                        await this.refreshAllData();
                        // إظهار رسالة نجاح احترافية في منتصف الشاشة
                        this.showToast(this.isArabic ? "تم الحذف بنجاح" : "Deleted successfully", 'success');
                    } else {
                        // معالجة فشل الحذف (مثلاً لوجود بيانات مرتبطة)
                        const errorData = await res.text();
                        console.error("Delete Error:", errorData);
                        this.showToast(this.isArabic ? "فشل الحذف: قد يكون العنصر مرتبطاً ببيانات أخرى" : "Delete failed: Item may be linked to other data", 'error');
                    }
                } catch (e) {
                    console.error("Network Error:", e);
                    this.showToast(this.isArabic ? "حدث خطأ في الشبكة أثناء الحذف" : "Network error during deletion", 'error');
                } finally {
                    this.loading = false;
                }
            };

            // 3️⃣ تعريف وظيفة "عند الإلغاء"
            this.confirmModal.onCancel = () => {
                this.confirmModal.show = false;
                // لا يتم اتخاذ أي إجراء آخر
            };
        },

        async submitForm() {
            // 1. التعامل مع حفظ الإعدادات العامة (خارج المودال)
            if (this.view === 'global_config' && !this.showModal) {
                return await this.saveGlobalConfig();
            }

            const type = this.modalType;
            if (!type || !this.forms[type]) return;

            // 2. التحقق من منطق الشركات التابعة (Business Logic)
            if (type === 'opco' && this.forms.opco.parent) {
                const parentCompany = this.allOpcos.find(o => o.id === parseInt(this.forms.opco.parent));
                if (parentCompany && !parentCompany.is_holding) {
                    this.showToast(
                        this.isArabic ? "لا يمكن إضافة شركة تابعة إلا تحت شركة قابضة (Holding)" : "Subsidiaries can only be added under a Holding company",
                        'error'
                    );
                    return;
                }
            }

            const isEdit = this.isEditing;
            const id = this.forms[type].id;

            // 3. تحديد الرابط ونوع الطلب
            let url = isEdit ? `/api/${type}s/${id}/` : `/api/${type}s/`;
            let method = isEdit ? 'PATCH' : 'POST';
            const csrftoken = this.getCookie('csrftoken');

            // تصحيح مسارات الـ API الخاصة بكل موديل
            if (type === 'po') url = isEdit ? `/api/orders/${id}/` : `/api/orders/`;
            else if (type === 'salesorder') url = isEdit ? `/api/sales-orders/${id}/` : `/api/sales-orders/`;
            else if (type === 'customer') url = isEdit ? `/api/customers/${id}/` : `/api/customers/`;
            else if (type === 'delivery') url = '/api/stock-deliveries/';
            else if (type === 'stock_entry') {
                url = '/api/wms/moves/';
            }

            try {
                this.loading = true;
                let payload;
                let headers = { 'X-CSRFToken': csrftoken };

                const useFormData = (type === 'material' || type === 'opco');

                if (useFormData) {
                    payload = new FormData();
                    const data = this.forms[type];

                    // 🚀 إضافة الـ opco لـ FormData
                    if (!data.opco && this.activeOpcoId) {
                        payload.append('opco', this.activeOpcoId);
                    }

                    Object.keys(data).forEach(key => {
                        if (type === 'material' && key === 'company_assignments') {
                            const validAssignments = data[key].filter(assign => assign.opco_id);
                            payload.append('company_assignments', JSON.stringify(validAssignments));
                        }
                        else if (data[key] !== null && !['logo', 'image', 'assigned_bins', 'primary_bin', 'company_assignments'].includes(key)) {
                            let val = data[key];
                            if (typeof val === 'boolean') val = val ? 'true' : 'false';
                            payload.append(key, val);
                        }
                    });

                    if (this.selectedFile) {
                        const fileKey = (type === 'material') ? 'image' : 'logo';
                        payload.append(fileKey, this.selectedFile);
                    }
                }
                else {
                    headers['Content-Type'] = 'application/json';

                    // 🚀 🚀 التعديل الجوهري هنا لضمان إرسال opco مع الـ JSON
                    let finalData = { ...this.forms[type] };

                    // إذا كان الحقل opco فارغ، نستخدم الشركة النشطة حالياً
                    if (!finalData.opco && this.activeOpcoId) {
                        finalData.opco = this.activeOpcoId;
                    }

                    payload = JSON.stringify(finalData);
                }

                // تنفيذ الطلب
                const response = await fetch(url, {
                    method: method,
                    headers: headers,
                    body: payload
                });

                if (response.ok) {
                    this.showModal = false;
                    this.selectedFile = null;
                    this.imagePreview = null;
                    await this.refreshAllData();
                    this.showToast(this.isArabic ? "تم حفظ البيانات بنجاح" : "Data saved successfully", 'success');
                } else {
                    const errorResponse = await response.text();
                    this.showToast(this.isArabic ? "فشل الحفظ: " + errorResponse : "Save failed: " + errorResponse, 'error');
                }
            } catch (error) {
                console.error("Network Error:", error);
                this.showToast(this.isArabic ? "حدث خطأ في الشبكة أو السيرفر" : "Network or Server error", 'error');
            } finally {
                this.loading = false;
            }
        },


        async onOpcoChange() {
            const opcoId = this.activeOpcoId;
            if (!opcoId) return;

            try {
                this.loading = true;
                this.syncGlobalConfig(opcoId);
                await this.getListData();
                await this.fetchVendors();
                await this.fetchCustomers();
                await this.fetchWMSStats();
            } catch (error) {
                console.error("Error during OpCo change:", error);
            } finally {
                this.loading = false;
            }
        },

        async saveGlobalConfig() {
            const targetId = this.activeOpcoId;
            if (!targetId) return;

            try {
                this.loading = true;
                const formData = new FormData();
                formData.append('name', this.config.company_name);
                formData.append('is_holding', this.config.is_holding ? 'true' : 'false');
                formData.append('tax_id', this.config.tax_id || '');
                formData.append('cr_number', this.config.cr_number || '');

                const activeOpco = this.allOpcos.find(o => o.id === parseInt(targetId));
                if (activeOpco) {
                    formData.append('code', activeOpco.code);
                }

                if (this.newLogoFile instanceof File) {
                    formData.append('logo', this.newLogoFile);
                }

                const url = `/api/opcos/${targetId}/`;

                const response = await fetch(url, {
                    method: 'PATCH',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    this.handleSaveSuccess(data);
                } else {
                    this.showToast(this.isArabic ? "فشل حفظ الإعدادات" : "Failed to save settings", 'error');
                }
            } catch (error) {
                console.error("Save Error:", error);
            } finally {
                this.loading = false;
            }
        },


        handleSaveSuccess(updatedData) {
            let logoUrl = updatedData.logo;
            if (logoUrl && !logoUrl.startsWith('http') && !logoUrl.startsWith('/')) {
                logoUrl = '/' + logoUrl;
            }

            const allIndex = this.allOpcos.findIndex(o => o.id === updatedData.id);
            if (allIndex !== -1) {
                this.allOpcos.splice(allIndex, 1, { ...updatedData, logo: logoUrl });
            }

            if (parseInt(this.activeOpcoId) === parseInt(updatedData.id)) {
                this.config = {
                    company_name: updatedData.name,
                    is_holding: updatedData.is_holding,
                    tax_id: updatedData.tax_id,
                    cr_number: updatedData.cr_number,
                    logo: logoUrl
                };
            }

            this.newLogoFile = null;
            // ✅ رسالة نجاح احترافية
            this.showToast(this.isArabic ? 'تم حفظ البيانات بنجاح' : 'Data saved successfully', 'success');
        },

        async refreshAllData() {
            this.loading = true;
            try {
                await this.fetchAll();
                await Promise.all([
                    this.fetchDashboardData(),
                    this.getListData(),
                    this.fetchWMSStats(),
                    this.fetchMaterialsList(),
                    this.fetchPurchaseOrders(),
                    this.fetchInventoryMoves(),
                    this.fetchCustomers(),
                    this.fetchVendors()
                ]);
                if (this.activeOpcoId) this.syncGlobalConfig(this.activeOpcoId);
            } catch (e) {
                console.error("Error in refreshAllData:", e);
            } finally {
                this.loading = false;
            }
        },

        async checkAuth() {
            try {
                const res = await fetch('/api/check-auth/');
                const data = await res.json();
                if (data.authenticated) {
                    this.user = {
                        name: data.user,
                        is_superuser: data.is_superuser,
                        role: data.role
                    };

                    this.license = {
                        daysRemaining: data.days_remaining,
                        companyName: data.holding_name,
                        isExpired: data.days_remaining <= 0
                    };
                    
                    this.systemMode = data.system_mode || 'modular';
                    this.purchasedModules = data.purchased_modules || [];
                    
                    // Filter Sidebar based on purchased modules
                    if (this.purchasedModules.length > 0) {
                        this.sidebarGroups.operations = this.sidebarGroups.operations.filter(mod => {
                            if (mod.id === 'org_builder') return true; // Always allow Org Builder
                            // Map sidebar ID to setup module ID
                            const idMap = {
                                'inventory_module': 'wms',
                                'procurement_module': 'proc',
                                'sales_module': 'sales',
                                'accounting_module': 'sales' // Assuming accounting belongs to sales suite
                            };
                            return this.purchasedModules.includes(idMap[mod.id] || mod.id);
                        });
                    }
                    
                    // If Stand Alone, jump directly to the single module and skip Executive Command Center
                    if (this.systemMode === 'standalone') {
                        const defaultModule = this.sidebarGroups.operations.find(m => m.id !== 'org_builder');
                        if (defaultModule) {
                            this.view = defaultModule.id;
                        }
                    }

                    await this.fetchAll();
                    this.activeOpcoId = data.company_id || (this.allOpcos[0] ? this.allOpcos[0].id : null);
                    this.activeOpco = {
                        id: this.activeOpcoId,
                        name: data.company_name || 'REDIVIO',
                        currency: data.currency || 'SAR'
                    };
                    this.syncGlobalConfig(this.activeOpcoId);
                    await this.refreshAllData();
                }
            } catch (e) { console.error("Auth Error", e); }
        },

        async fetchAll() {
            try {
                const resAll = await fetch('/api/opcos/?all=true');
                this.allOpcos = await resAll.json();

                const endpoints = ['opcos', 'plants', 'locations', 'bins'];
                const results = await Promise.all(
                    endpoints.map(e => fetch(`/api/${e}/`).then(r => r.json()))
                );

                this.opcos = results[0];
                this.plants = results[1];
                this.locations = results[2];
                this.bins = results[3];
                // تحميل الموردين والمشتريات أيضاً
                this.fetchVendors();
                this.fetchPurchaseOrders();
            } catch (e) {
                console.error("Core Data Fetch Error:", e);
            }
        },

        async getListData() {
            try {
                const url = this.activeOpcoId ? `/api/inventory/?opco=${this.activeOpcoId}` : '/api/inventory/';
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.inventoryList = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) { console.error("Inventory Fetch Error", e); }
        },

        async fetchWMSStats() {
            try {
                const url = this.activeOpcoId ? `/api/wms/stats/?opco=${this.activeOpcoId}` : '/api/wms/stats/';
                const res = await fetch(url);
                if (res.ok) {
                    this.wms_stats = await res.json();
                    this.kpis.inventory.total_value = this.wms_stats.total_value || 0;
                    this.kpis.inventory.critical_items = this.wms_stats.low_stock || 0;

                    // 🚀 توليد الإشعارات ديناميكياً من بيانات المخزون المنخفض
                    this.notifications = [];
                    if (this.wms_stats.low_stock_list && this.wms_stats.low_stock_list.length > 0) {
                        this.wms_stats.low_stock_list.forEach(item => {
                            this.notifications.push({
                                type: 'low_stock',
                                title: this.isArabic ? 'انخفاض مخزون صنف' : 'Low Stock Alert',
                                message: this.isArabic 
                                    ? `الصنف #${item.sku} وصل للحد الأدنى (${item.current_qty})` 
                                    : `Item #${item.sku} reached minimum level (${item.current_qty})`,
                                time: this.isArabic ? 'الآن' : 'Now'
                            });
                        });
                    }
                }
            } catch (e) { console.error("Stats Error", e); }
        },

        async fetchDashboardData() {
            try {
                const res = await fetch('/api/dashboard-data/');
                const data = await res.json();
                if (data.kpis) {
                    // 🚀 التعديل: دمج البيانات بحذر للحفاظ على الهيكل
                    this.kpis.inventory.total_items = data.kpis.materials || 0;
                    this.kpis.inventory.stock_qty = data.kpis.stock_qty || 0;
                    this.kpis.procurement.total = data.kpis.pending_pos || 0;
                    this.kpis.vendors = data.kpis.vendors || 0;
                }
            } catch (e) { console.log("KPI fetch error"); }
        },
        // داخل methods في main.js
        async onMaterialSelect(item) {
            // 1. جلب بيانات الصنف شاملة الرفوف
            const res = await fetch(`/api/materials/${item.material_id}/`);
            const data = await res.json();

            // 2. البحث عن الرف اللي واخد تعليم "is_primary"
            const primary = data.material_bins.find(b => b.is_primary);

            if (primary) {
                this.forms.stock_entry.bin_id = primary.storage_bin;
                this.showToast(this.isArabic ? "تم تحديد الرف الافتراضي تلقائياً" : "Default bin selected", 'success');
            }
        },

        drillDownContact(agg) {
            // 1. Set the contact search filter
            this.forms.stock_entry.contact_search = agg.name;
            // 2. Switch back to "All" view to see individual moves
            this.forms.stock_entry.groupBy = 'none';
            // 3. Optional: Clear other filters if needed
            this.forms.stock_entry.filterType = 'ALL';
        },

        // 🚀 وظائف لوحة التحكم الحية (WMS Dashboard Actions)
        openReceiptModal(poId) {
            this.modalType = 'stock_entry';
            this.activeOperation = 'po_receipt'; // وضع الاستلام من أمر شراء
            this.forms.stock_entry.po_id = poId;
            this.showModal = true;
            this.fetchPODetailsForReceipt(); // جلب بيانات الأصناف للأمر
        },

        openDeliveryModal(soId) {
            this.modalType = 'stock_entry';
            this.activeOperation = 'so_delivery'; // وضع الصرف لأمر بيع
            this.forms.stock_entry.so_id = soId;
            this.showModal = true;
            this.fetchSODetailsForDelivery(); // جلب بيانات الأصناف للأمر
        },

        printInventoryReport() {
            this.showToast(this.isArabic ? "جاري تحضير تقرير الجرد..." : "Preparing Inventory Report...", 'info');
            window.open('/api/wms/inventory/print_audit/?format=pdf', '_blank');
        },

        viewStagnantStock() {
            this.view = 'inventory_module';
            this.inventoryTab = 'levels';
            this.showToast(this.isArabic ? "جاري عرض الأصناف الحالية" : "Viewing Current Stock Levels", 'info');
        },

        openModal(type, data = null) {
            this.isEditing = false;
            this.modalType = type;
            this.materialTab = 'general';
            this.showModal = true;
            this.imagePreview = null;
            this.selectedFile = null;

            if (type === 'salesorder') {
                this.forms.salesorder = {
                    id: null, customer: '', so_number: `SO-${Date.now()}`,
                    status: 'DRAFT', total_amount: 0, tax_amount: 0, grand_total: 0,
                    lines: [{ material: '', quantity: 1, unit_price: 0 }]
                };
            } else if (type === 'customer') {
                this.forms.customer = { id: null, code: '', name: '', tax_id: '', email: '', phone: '', address: '' };
            } else if (type === 'plant') {
                this.forms.plant = { id: null, opco: this.activeOpcoId, code: '', name: '' };
            } else if (type === 'location') {
                this.forms.location = { id: null, plant: this.activePlantId, code: '', name: '' };
            } else if (type === 'bin') {
                this.forms.bin = { id: null, storage_location: this.activeLocationId, code: '' };
            } else if (type === 'material') {
                this.forms.material = {
                    id: null, sku: '', name: '', category: '', base_uom: 'PCS', barcode: '',
                    company_assignments: [{ opco_id: this.activeOpcoId, bins: [], primary_bin: null }],
                    tracking: 'none', reorder_level: 0, max_level: 0
                };
            } else if (type === 'stock_entry') {
                this.activeOperation = 'manual';
                this.forms.stock_entry = { 
                    receipt_type: 'PURCHASE', 
                    items: data && data.items ? data.items : [{ material_id: '', quantity: 1, unit_cost: 0 }], 
                    target_plant: this.activePlantId || '', 
                    bin_id: '', contact_id: '', manual_contact_name: '' 
                };
            } else if (type === 'po' || type === 'purchase_order') {
                const hasProcurement = this.purchasedModules && (this.purchasedModules.includes('procurement') || this.purchasedModules.includes('proc'));
                if (this.systemMode === 'modular' && hasProcurement) {
                    this.modalType = 'po';
                    this.forms.po = { 
                        vendor: '', 
                        po_number: `PO-${Date.now()}`, 
                        lines: data && data.items ? data.items : [{ material: '', quantity: 1, unit_price: 0 }], 
                        tax_rate: 15, is_tax_inclusive: false 
                    };
                    this.fetchVendors();
                } else {
                    this.modalType = 'stock_entry';
                    this.activeOperation = 'manual';
                    this.forms.stock_entry = { 
                        receipt_type: 'PURCHASE', 
                        items: data && data.items ? data.items.map(i => ({
                            material_id: i.material,
                            quantity: i.quantity,
                            unit_cost: i.unit_price
                        })) : [{ material_id: '', quantity: 1, unit_cost: 0 }],
                        target_plant: this.activePlantId || '', 
                        bin_id: '', contact_id: '', manual_contact_name: '' 
                    };
                    this.showToast(this.isArabic ? "تم فتح إذن استلام (Standalone Mode)" : "Opened Stock Receipt (Standalone)", 'info');
                }
            } else if (type === 'opco') {
                this.forms.opco = {
                    id: null, code: data ? data.code : '', name: '',
                    currency: 'USD', parent: data ? data.parent : (this.activeOpcoId || null), is_holding: false
                };
            }
        },

        createPOFromLowStock() {
            if (!this.wms_stats.low_stock_list || this.wms_stats.low_stock_list.length === 0) {
                this.showToast(this.isArabic ? "لا توجد أصناف تحت حد الطلب" : "No items below reorder point", 'info');
                return;
            }

            // حساب الكمية المطلوبة = الحد الأقصى - الرصيد الحالي
            const lines = this.wms_stats.low_stock_list.map(item => ({
                material: item.id,
                sku: item.sku,
                name: item.name,
                quantity: Math.max(0, item.max_level - item.current_qty),
                unit_price: 0
            }));

            this.openModal('purchase_order', { items: lines });
        },
        async fetchPurchaseOrders() {
            try {
                // هنجيب كل أوامر التوريد الخاصة بالشركة الحالية
                const url = this.activeOpcoId
                    ? `/api/orders/?opco=${this.activeOpcoId}`
                    : '/api/orders/';
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.purchase_orders = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) {
                console.error("Error fetching POs:", e);
            }
        },

        async updatePOStatus(poId, newStatus) {
            try {
                this.loading = true;
                const res = await fetch(`/api/orders/${poId}/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ status: newStatus })
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم تحديث حالة الطلب بنجاح" : "PO Status Updated", 'success');
                    await this.fetchPurchaseOrders(); // تحديث الجدول فوراً
                }
            } catch (e) {
                this.showToast("Network Error", 'error');
            } finally {
                this.loading = false;
            }
        },

        // ضيف دي جوه الـ methods
        viewPODetails(po) {
            this.modalType = 'view_po'; // هنحتاج نجهز Modal يعرض البيانات
            this.forms.po = JSON.parse(JSON.stringify(po)); // نسخ بيانات الأمر للفورم
            this.showModal = true;
            this.showToast(this.isArabic ? "جاري عرض تفاصيل الأمر" : "Viewing PO Details", 'success');
        },

        // دالة لبدء عملية الصرف بناءً على أمر البيع
        startDelivery(so) {
            this.view = 'inventory_module';
            this.activeOperation = 'so_delivery'; // تحديد نوع العملية (صورة 2)
            this.modalType = 'delivery';
            this.showModal = true;

            // تجهيز بيانات الصرف بناءً على أصناف أمر البيع
            this.forms.delivery = {
                so: so.id,
                items: so.lines.map(line => ({
                    material: line.material,
                    quantity: line.quantity - line.shipped_quantity,
                    storage_bin: ''
                }))
            };
        },

        printInvoice(id) {
            window.open(`/api/print/invoice/${id}/`, '_blank');
        },

        printGRN(id) {
            window.open(`/api/print/grn/${id}/`, '_blank');
        },

        printPO(id) {
            window.open(`/api/print/po/${id}/`, '_blank');
        },

        printDelivery(id) {
            window.open(`/api/print/delivery/${id}/`, '_blank');
        },

        async fetchSODetailsForDelivery() {
            const soId = this.forms.stock_entry.so_id;
            if (!soId) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/sales-orders/${soId}/`);
                if (res.ok) {
                    const so = await res.json();
                    // تصفير القائمة القديمة وملئها بالأصناف المطلوبة للصرف
                    this.forms.stock_entry.items = so.lines
                        .filter(l => l.remaining_quantity > 0)
                        .map(line => ({
                            material_id: line.material,
                            material_name: line.material_name,
                            sku: line.material_sku,
                            ordered_qty: line.quantity,
                            received_before: line.shipped_quantity,
                            received_qty: line.remaining_quantity, // الكمية الافتراضية هي المتبقي
                            bin_id: line.suggested_bin || ''
                        }));
                }
            } catch (e) {
                console.error("Error fetching SO details:", e);
            } finally {
                this.loading = false;
            }
        },

        openPaymentModal(invoice) {
            this.modalType = 'payment';
            this.forms.payment = {
                invoice: invoice.id,
                invoice_number: invoice.invoice_number,
                customer: invoice.customer,
                customer_name: invoice.customer_name,
                amount: invoice.total_amount - invoice.paid_amount,
                method: 'CASH',
                reference: ''
            };
            this.showModal = true;
        },

        async submitPayment() {
            try {
                this.loading = true;
                const payload = {
                    opco: this.activeOpcoId,
                    invoice: this.forms.payment.invoice,
                    customer: this.forms.payment.customer,
                    amount: this.forms.payment.amount,
                    method: this.forms.payment.method,
                    reference: this.forms.payment.reference,
                    payment_number: `PAY-${Date.now()}`
                };

                const res = await fetch('/api/customer-payments/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم تسجيل الدفعة بنجاح" : "Payment recorded", 'success');
                    this.showModal = false;
                    await this.fetchSalesInvoices();
                    await this.fetchCustomers();
                    await this.fetchPayments();
                } else {
                    const err = await res.json();
                    this.showToast(err.error || "Payment failed", 'error');
                }
            } catch (e) {
                this.showToast("Network Error", 'error');
            } finally {
                this.loading = false;
            }
        },

        async updateSOStatus(soId, newStatus) {
            try {
                this.loading = true;
                const res = await fetch(`/api/sales-orders/${soId}/`, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ status: newStatus })
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم تأكيد الأمر بنجاح" : "Order Confirmed", 'success');
                    await this.fetchSalesOrders(); // تحديث القائمة عشان زرار الشاحنة يظهر
                }
            } catch (e) {
                this.showToast("Error", 'error');
            } finally {
                this.loading = false;
            }
        },

        async fetchMaterialsList() {
            try {
                const res = await fetch('/api/materials/');
                if (res.ok) {
                    const data = await res.json();
                    this.materials_list = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) { console.error(e); }
        },

        getBinLocationName(binId) {
            const bin = this.bins.find(b => b.id === binId);
            if (!bin) return '...';
            const loc = this.locations.find(l => l.id === bin.storage_location);
            return loc ? loc.name : '...';
        },

    },

    mounted() {
        this.checkAuth();
        this.startClock();
        this.fetchAll();
        this.fetchMaterialsList();
        this.fetchWMSStats();
    }
}).mount('#app');