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
            posTab: 'cashier',
            posReportTab: 'detailed_sales',
            posMode: localStorage.getItem('pos_mode') || 'restaurant',
            activePOSSession: null,
            posTerminals: [],
            selectedTerminalId: localStorage.getItem('selected_terminal_id') || '',
            posOpeningBalance: 0.00,
            showTerminalFormModal: false,
            terminalForm: { id: null, code: '', name: '', terminal_type: 'DIRECT', is_active: true, allowed_users: [] },
            posCart: [],
            posSearch: '',
            posCategory: 'all',
            posPaymentMethod: 'cash',
            posStats: { total_revenue: 0, cash_total: 0, instapay_total: 0, credit_total: 0, top_items: [], ingredients: [] },
            posSelectedCartIndex: null,
            posShowNumpad: false,
            // 📅 فلاتر لوحة تحكم المطعم
            posDashboardFilters: {
                from: '',
                to: ''
            },
            posNumpadBuffer: '',
            posOrderType: 'DINE_IN',
            posTableNumber: '',
            posTableId: null,
            posExistingOrderId: null,
            posGuestCount: 1,
            posFloors: [],
            posTables: [],
            activeFloorId: null,
            isLayoutEditMode: false,
            draggedTable: null,
            dragOffset: { x: 0, y: 0 },
            selectedLayoutTable: null,
            showTableActionModal: false,
            showTableModal: false,
            showFloorModal: false,
            tableForm: { id: null, number: '', seats_limit: 4, shape: 'square', current_guests: 1, position_x: 50, position_y: 50 },
            floorForm: { id: null, name: '', number: 1 },
            posActiveCashierId: null,
            posSessionsHistory: [],
            selectedSession: null,
            posOrdersHistory: [],
            kdsOrders: [],
            kdsInterval: null,
            kdsCurrentTime: new Date(),
            draggedOrder: null,
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
            posOrdersState: {}, // { orderId: status },

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
                    { id: 'accounting_module', name: { ar: 'المحاسبة والمالية', en: 'Accounting' }, icon: 'fas fa-file-invoice-dollar' },
                    { id: 'restaurant_pos_module', name: { ar: 'نقاط البيع (POS)', en: 'POS System' }, icon: 'fas fa-cash-register' }
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

            showSubscriptionModal: false,

            license: {
                daysRemaining: 15,
                companyName: '...',
                isExpired: false,
                plan: 'free',
                skuLimit: 50,
                daysLimit: 15,
                skuCount: 0
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
            companyUsers: [],
            userSearch: '',
            allOpcos: [],
            opcos: [],

            subsidiaries: [],
            plants: [],
            locations: [],
            bins: [],
            materials_list: [],
            sale_groups: [],
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
                so_delivery: { ar: 'صرف بضاعة من أمر بيع', en: 'WMS Sales Delivery' },
                user: { ar: 'إدارة حساب مستخدم', en: 'User Account Management' }
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
                    sales_price: 0,
                    tax_rate: 15,
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
                },
                user: { id: null, email: '', role: 'cashier', company: null, password: '' }
            }
        };
    },

    computed: {
        activeFloorTables() {
            return (this.posTables || []).filter(t => t.floor === this.activeFloorId);
        },
        activeDineInTables() {
            return (this.posTables || []).filter(t => t.status === 'occupied' && t.active_order_detail);
        },
        posCategories() {
            // سنستخدم المجموعات البيعية بدلاً من الفئات العامة في الـ POS
            return this.sale_groups || [];
        },
        filteredPosItems() {
            // فلترة الأصناف التي تحمل علامة POS Item فقط
            let items = (this.materials_list || []).filter(i => i.is_pos_item);
            
            // فلترة الأصناف بناءً على نقطة البيع النشطة المحددة (إذا تم تقييد الصنف)
            if (this.selectedTerminalId) {
                const terminalId = parseInt(this.selectedTerminalId);
                items = items.filter(i => {
                    if (!i.allowed_terminals || i.allowed_terminals.length === 0) {
                        return true; // متاح للجميع افتراضياً
                    }
                    return i.allowed_terminals.includes(terminalId);
                });
            }
            
            if (this.posCategory !== 'all') {
                // الفلترة هنا تتم بناءً على ID المجموعة البيعية
                items = items.filter(i => i.sale_group === this.posCategory);
            }
            if (this.posSearch) {
                const q = this.posSearch.toLowerCase();
                items = items.filter(i => (i.name && i.name.toLowerCase().includes(q)) || (i.sku && i.sku.toLowerCase().includes(q)));
            }
            return items;
        },
        cartSubtotal() {
            return this.posCart.reduce((sum, item) => sum + (item.price * item.qty), 0);
        },
        cartTax() {
            let totalTax = 0;
            this.posCart.forEach(item => {
                const rate = (parseFloat(item.tax_rate) || 15) / 100;
                totalTax += (parseFloat(item.price) * parseFloat(item.qty)) * rate;
            });
            return Math.round(totalTax * 100) / 100;
        },
        groupedSessions() {
            const groups = {};
            this.posSessionsHistory.forEach(s => {
                const date = new Date(s.start_time).toLocaleDateString(this.isArabic ? 'ar-EG' : 'en-US', {
                    year: 'numeric', month: 'long', day: 'numeric'
                });
                if (!groups[date]) groups[date] = [];
                groups[date].push(s);
            });
            return groups;
        },
        cartTotal() {
            return Math.round((this.cartSubtotal + this.cartTax) * 100) / 100;
        },
        activeOpco() {
            if (!this.activeOpcoId || !this.allOpcos.length) return null;
            
            // البحث عن الشركة الحالية
            const opco = this.allOpcos.find(o => parseInt(o.id) === parseInt(this.activeOpcoId));
            if (!opco) return null;

            // 🚀 منطق الوراثة (Inheritance Logic)
            // إذا كانت الشركة فرعية وليس لها لوجو، نبحث في الشركة الأم وهكذا
            let current = opco;
            let finalLogo = current.logo;
            let finalColor = current.brand_color;

            // محاولة جلب اللوجو واللون من الهيكل الهرمي
            let depth = 0;
            while ((!finalLogo || !finalColor) && current.parent && depth < 5) {
                const parentId = parseInt(current.parent);
                const parent = this.allOpcos.find(o => o.id === parentId);
                if (parent) {
                    if (!finalLogo) finalLogo = parent.logo;
                    if (!finalColor || finalColor === '#6366f1') finalColor = parent.brand_color;
                    current = parent;
                    depth++;
                } else {
                    break;
                }
            }

            return {
                ...opco,
                logo: this.fixImagePath(finalLogo),
                brand_color: finalColor || '#6366f1'
            };
        },

        filteredMaterials() {
            let list = this.materials_list || [];

            // 1. فلترة بالشركة الحالية
            if (this.activeOpcoId) {
                list = list.filter(item => {
                    if (!item.company_assignments) return true;
                    return item.company_assignments.some(a => parseInt(a.opco_id) === parseInt(this.activeOpcoId));
                });
            }

            // 2. تصفية إضافية لموديول المطاعم (اختياري: يمكنك فلترة الأصناف هنا إذا رغبت)
            if (this.view === 'restaurant_pos_module' && this.posTab === 'recipes') {
                // سنعرض كل الأصناف حالياً لتمكين إدارة المكونات أيضاً
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
                'dashboard': { ar: 'لوحة التحكم المركزية', en: 'Command Center' },
                'org_builder': { ar: 'بناء الهيكل التنظيمي', en: 'Organization Builder' },
                'inventory_module': { ar: 'RIMS (المخزون والعمليات)', en: 'RIMS (Inventory)' },
                'procurement_module': { ar: 'RPMS (المشتريات والموردين)', en: 'RPMS (Procurement)' },
                'sales_module': { ar: 'إدارة المبيعات والعملاء', en: 'Sales & CRM' },
                'accounting_module': { ar: 'المحاسبة والمالية', en: 'Accounting' },
                'restaurant_pos_module': { ar: 'نقاط البيع (POS)', en: 'POS System' },
                'global_config': { ar: 'إعدادات النظام الرئيسية', en: 'Enterprise Settings' },
                'users': { ar: 'إدارة طاقم العمل', en: 'Staff Management' },
                'item_master': { ar: 'سجل الأصناف الرئيسي', en: 'Global Item Master' },
                'vendors_list': { ar: 'سجل الموردين', en: 'Vendors' },
                'vendor_ledger': { ar: 'كشف حساب مورد', en: 'Vendor Ledger' }
            };
            const current = views[this.view] || { ar: this.view, en: this.view };
            return this.isArabic ? current.ar : current.en;
        },

        localizedViewDescription() {
            const descs = {
                'dashboard': { ar: 'نظرة عامة على أداء كافة الشركات والفروع', en: 'High-level overview of multi-company performance' },
                'org_builder': { ar: 'تصميم الهيكل الهرمي للشركات والمصانع والمستودعات', en: 'Design corporate hierarchy: Holdings, OpCos, Plants, and Bins' },
                'global_config': { ar: 'تكوين الهوية القانونية والضريبية للمنشأة', en: 'Configure legal identity, tax information, and corporate logo' },
                'users': { ar: 'التحكم في حسابات الموظفين وصلاحيات الوصول للنظام', en: 'Control employee accounts, roles, and system access levels' },
                'inventory_module': { ar: 'إدارة المخزون، التحويلات، وتتبع الأرصدة', en: 'Manage stock levels, transfers, and warehouse movements' },
                'restaurant_pos_module': { ar: 'إدارة المبيعات المباشرة، كاشير المطاعم، صالة الطعام، والمطبخ KDS', en: 'Manage direct sales, restaurant orders, floor layouts, and kitchen display (KDS)' }
            };
            const current = descs[this.view] || { ar: '', en: '' };
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
            if (newId) {
                this.syncGlobalConfig(newId);
                if (this.view === 'restaurant_pos_module') {
                    this.fetchPOSTerminals();
                }
            }
        },
        view(newView) {
            if (newView === 'users') this.fetchCompanyUsers();
            if (newView === 'org_builder') this.fetchAll();
            if (newView === 'global_config' && this.activeOpcoId) this.syncGlobalConfig(this.activeOpcoId);
            if (newView === 'restaurant_pos_module') {
                this.fetchPOSTerminals();
            }
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
        if (this.activeOpcoId) {
            this.fetchPOSTerminals();
        } else {
            this.checkActivePOSSession();
        }
        
        // 🚀 KDS Timer & Polling
        setInterval(() => { this.kdsCurrentTime = new Date(); }, 1000);
        this.kdsInterval = setInterval(() => {
            if (this.view === 'restaurant_pos_module' && this.posTab === 'kitchen') {
                this.fetchKDSOrders();
            }
            if (this.view === 'users') {
                this.fetchCompanyUsers();
            }
            if (this.view === 'restaurant_pos_module') {
                this.checkPOSStatusUpdates();
            }
        }, 3000);

        // Core Init
        this.checkAuth();
        this.startClock();
        this.fetchAll();
        this.fetchMaterialsList();
        this.fetchWMSStats();

        // 🚀 Watch activeOpco to cache logo for preloader white-labeling
        this.$watch('activeOpco', (newOpco) => {
            if (newOpco && newOpco.logo) {
                try {
                    localStorage.setItem('global_config', JSON.stringify({ logo: newOpco.logo }));
                } catch (e) {}
            }
        }, { deep: true });

        // 🚀 Hide preloader gracefully after mounting has settled
        setTimeout(() => {
            const preloader = document.getElementById('global-preloader');
            if (preloader) {
                preloader.classList.add('fade-out');
                setTimeout(() => {
                    preloader.remove();
                }, 500);
            }
        }, 400);
    },

    methods: {
        setPOSMode(mode) {
            this.posMode = mode;
            localStorage.setItem('pos_mode', mode);
            if (mode === 'direct') {
                if (this.posOrderType === 'DINE_IN') {
                    this.posOrderType = 'TAKEAWAY';
                }
                if (['floor_layout', 'kitchen'].includes(this.posTab)) {
                    this.posTab = 'cashier';
                }
            }
        },
        async fetchFloorsAndTables() {
            try {
                this.loading = true;
                const [floorsRes, tablesRes] = await Promise.all([
                    fetch('/api/pos/floors/?opco=' + this.activeOpcoId),
                    fetch('/api/pos/tables/?opco=' + this.activeOpcoId)
                ]);
                if (floorsRes.ok) this.posFloors = await floorsRes.json();
                if (tablesRes.ok) this.posTables = await tablesRes.json();
                
                if (this.posFloors.length > 0 && !this.activeFloorId) {
                    this.activeFloorId = this.posFloors[0].id;
                }
            } catch (e) {
                console.error("Error fetching floors/tables:", e);
                this.showToast(this.isArabic ? "خطأ في تحميل الطوابق والترابيزات" : "Error loading floors/tables", "error");
            } finally {
                this.loading = false;
            }
        },

        selectFloor(floorId) {
            this.activeFloorId = floorId;
        },

        toggleLayoutEditMode() {
            this.isLayoutEditMode = !this.isLayoutEditMode;
            if (!this.isLayoutEditMode) {
                this.showToast(this.isArabic ? "تم حفظ تخطيط الصالة" : "Floor layout saved", "success");
            }
        },

        getChairStyle(index, total, shape) {
            // Distribute seats around the table shape
            const angle = (2 * Math.PI * index) / total - Math.PI / 2;
            const radius = shape === 'round' ? 52 : 55; // distance from center of table in px
            const x = Math.round(Math.cos(angle) * radius);
            const y = Math.round(Math.sin(angle) * radius);
            return {
                position: 'absolute',
                left: `calc(50% + ${x}px)`,
                top: `calc(50% + ${y}px)`,
                transform: 'translate(-50%, -50%)',
                width: '12px',
                height: '12px'
            };
        },

        startTableDrag(table, event) {
            if (!this.isLayoutEditMode) return;
            this.draggedTable = table;
            
            const rect = event.currentTarget.getBoundingClientRect();
            const parentRect = document.getElementById('layout-canvas').getBoundingClientRect();
            
            // Calculate mouse offset inside the table card
            this.dragOffset = {
                x: event.clientX - rect.left,
                y: event.clientY - rect.top
            };
            event.preventDefault();
        },

        dragTable(event) {
            if (!this.draggedTable) return;
            const canvas = document.getElementById('layout-canvas');
            const rect = canvas.getBoundingClientRect();
            
            // Calculate absolute position relative to canvas
            const x = event.clientX - rect.left - this.dragOffset.x;
            const y = event.clientY - rect.top - this.dragOffset.y;
            
            // Translate to percentage (0 to 100)
            let pctX = Math.round((x / rect.width) * 100);
            let pctY = Math.round((y / rect.height) * 100);
            
            // Clamp coordinates inside canvas boundaries
            pctX = Math.max(0, Math.min(90, pctX));
            pctY = Math.max(0, Math.min(88, pctY));
            
            this.draggedTable.position_x = pctX;
            this.draggedTable.position_y = pctY;
        },

        async endTableDrag() {
            if (!this.draggedTable) return;
            const table = this.draggedTable;
            this.draggedTable = null;
            
            // Save coordinates via API
            try {
                await fetch(`/api/pos/tables/${table.id}/`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        position_x: table.position_x,
                        position_y: table.position_y
                    })
                });
            } catch (e) {
                console.error("Error saving drag coordinates:", e);
            }
        },

        handleTableClick(table) {
            if (this.isLayoutEditMode) {
                this.openTableModal(table);
            } else {
                this.openTableActions(table);
            }
        },

        openTableActions(table) {
            this.selectedLayoutTable = table;
            this.tableForm.current_guests = table.current_guests || 1;
            this.showTableActionModal = true;
        },

        async changeTableStatusAPI(tableId, status) {
            try {
                this.loading = true;
                const endpoint = status === 'available' ? 'release_table' : (status === 'cleaning' ? 'release_table' : 'assign_order');
                
                let res;
                if (status === 'available' || status === 'cleaning') {
                    res = await fetch(`/api/pos/tables/${tableId}/release_table/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                    });
                } else {
                    res = await fetch(`/api/pos/tables/${tableId}/`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                        body: JSON.stringify({ status })
                    });
                }

                if (res.ok) {
                    if (status === 'cleaning') {
                        // explicitly keep table status as cleaning
                        await fetch(`/api/pos/tables/${tableId}/`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                            body: JSON.stringify({ status: 'cleaning' })
                        });
                    }
                    this.showToast(this.isArabic ? "تم تحديث حالة الترابيزة" : "Table status updated", "success");
                    this.showTableActionModal = false;
                    await this.fetchFloorsAndTables();
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        async startOrderFromLayout(table, guests) {
            try {
                this.loading = true;
                // Mark table as occupied in the DB
                const res = await fetch(`/api/pos/tables/${table.id}/`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        status: 'occupied',
                        current_guests: guests
                    })
                });
                
                if (res.ok) {
                    this.posTableNumber = table.number;
                    this.posTableId = table.id;  // Track table ID for order linking
                    this.posGuestCount = guests;
                    this.posOrderType = 'DINE_IN';
                    this.posCart = [];
                    this.posTab = 'cashier';
                    this.showTableActionModal = false;
                    this.showToast(this.isArabic ? "بدء طلب محلي جديد" : "Dine-in order started", "success");
                    await this.fetchFloorsAndTables();
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        viewActiveTableOrder(table) {
            this.posTableNumber = table.number;
            this.posTableId = table.id;  // Track table ID for order linking
            this.posGuestCount = table.current_guests || 1;
            this.posOrderType = 'DINE_IN';

            // ✅ Load existing order items into cart so cashier can continue / checkout
            if (table.active_order_detail && table.active_order_detail.lines && table.active_order_detail.lines.length > 0) {
                this.posCart = table.active_order_detail.lines.map(line => ({
                    id: line.material,
                    name: line.material_name,
                    qty: line.qty,
                    price: parseFloat(line.unit_price),
                    subtotal: parseFloat(line.subtotal),
                    kitchen_notes: line.kitchen_notes || ''
                }));
                // Store the existing order ID so we update instead of creating new
                this.posExistingOrderId = table.active_order_detail.id;
            } else {
                this.posCart = [];
                this.posExistingOrderId = null;
            }

            this.posTab = 'cashier';
            this.showTableActionModal = false;
            this.showToast(this.isArabic ? "متابعة طلب الترابيزة" : "Viewing table order", "info");
        },

        recallTableOrder(table) {
            this.viewActiveTableOrder(table);
        },

        discardOrderEdits() {
            this.posCart = [];
            this.posTableNumber = '';
            this.posTableId = null;
            this.posExistingOrderId = null;
            this.posGuestCount = 1;
            this.posTab = 'floor_layout';
            this.showToast(this.isArabic ? "تم إلغاء تعديل الطلب" : "Order edit discarded", "info");
        },

        async payExistingOrder() {
            if (!this.posExistingOrderId) return;
            if (this.posCart.length === 0) {
                this.showToast(this.isArabic ? "الطلب فارغ!" : "Cart is empty!", "error");
                return;
            }

            try {
                this.loading = true;
                // 1. Save any pending changes to the dine-in order draft
                const saveRes = await fetch('/api/pos/orders/save_dine_in/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        session: this.activePOSSession.id,
                        table_number: this.posTableNumber,
                        guest_count: this.posGuestCount,
                        existing_order_id: this.posExistingOrderId,
                        lines: this.posCart.map(i => ({
                            material: i.id,
                            qty: i.qty,
                            unit_price: parseFloat(i.price.toFixed(2)),
                            subtotal: parseFloat((i.price * i.qty).toFixed(2)),
                            kitchen_notes: i.kitchen_notes || ''
                        }))
                    })
                });

                if (!saveRes.ok) {
                    const err = await saveRes.json();
                    this.showToast(err.error || "Error saving order", "error");
                    return;
                }

                const order = await saveRes.json();
                const orderId = order.id;
                const orderTotal = parseFloat(order.total_amount || 0);

                // Stop loading state so Swal can show
                this.loading = false;

                // 2. Prompt for payment method
                const { value: method } = await Swal.fire({
                    title: this.isArabic ? `طلب شيك - ترابيزة ${this.posTableNumber}` : `Bill Request - Table ${this.posTableNumber}`,
                    html: `
                        <div style="text-align:right; direction:rtl; margin-bottom: 16px; padding: 12px; background:#f8fafc; border-radius:12px;">
                            <div style="font-size:12px; color:#64748b; font-weight:bold; margin-bottom:4px;">${this.isArabic ? 'الإجمالي المستحق' : 'Total Amount Due'}</div>
                            <div style="font-size:28px; font-weight:900; color:#10b981; font-family:monospace;">${this.formatCurrency(orderTotal)}</div>
                        </div>
                        <div style="font-size:11px; color:#64748b; font-weight:bold; margin-bottom:8px; text-align:right;">${this.isArabic ? 'اختر طريقة الدفع:' : 'Select payment method:'}</div>
                    `,
                    input: 'radio',
                    inputOptions: {
                        'cash':     this.isArabic ? '💵 نقداً (Cash)'         : '💵 Cash',
                        'instapay': this.isArabic ? '📱 إلكتروني (InstaPay)'  : '📱 InstaPay',
                        'credit':   this.isArabic ? '📋 آجل (Credit)'         : '📋 Credit'
                    },
                    inputValue: 'cash',
                    showCancelButton: true,
                    confirmButtonText: this.isArabic ? '✅ تأكيد الدفع' : '✅ Confirm Payment',
                    cancelButtonText: this.isArabic ? 'إلغاء' : 'Cancel',
                    confirmButtonColor: '#10b981',
                });

                if (!method) return;

                this.loading = true;
                // 3. Process payment
                const payRes = await fetch(`/api/pos/orders/${orderId}/process_payment/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({ payment_method: method })
                });

                if (payRes.ok) {
                    this.showToast(
                        this.isArabic ? `✅ تم الدفع بنجاح! الترابيزة ${this.posTableNumber} - ${this.formatCurrency(orderTotal)}` : `✅ Payment done! Table ${this.posTableNumber} - ${this.formatCurrency(orderTotal)}`,
                        "success"
                    );
                    // Print receipt using the updated order details
                    this.printReceipt(order, this.posCart);
                    
                    // Clear the cashier cart and reset terminal table fields
                    this.posCart = [];
                    this.posExistingOrderId = null;
                    this.posTableNumber = '';
                    this.posGuestCount = 1;
                    this.posTab = 'floor_layout';
                    this.refreshAllData();
                } else {
                    const err = await payRes.json();
                    this.showToast(err.error || "Payment Failed", "error");
                }
            } catch (e) {
                console.error("Pay Existing Order Error:", e);
                this.showToast("Network Error", "error");
            } finally {
                this.loading = false;
            }
        },

        onTerminalTableChange() {
            if (!this.posTableNumber) return;
            const table = this.posTables.find(t => t.number === this.posTableNumber);
            if (table) {
                // Adjust guest count if it exceeds seats capacity
                if (this.posGuestCount > table.seats_limit) {
                    this.posGuestCount = table.seats_limit;
                }
            }
        },

        getSelectedTableOccupancyWarning() {
            if (this.posOrderType !== 'DINE_IN' || !this.posTableNumber) return '';
            const table = this.posTables.find(t => t.number === this.posTableNumber);
            if (table && this.posGuestCount > table.seats_limit) {
                return this.isArabic 
                    ? `تنبيه: عدد الأفراد يتجاوز سعة الترابيزة (${table.seats_limit} كراسي)!` 
                    : `Warning: Guests count exceeds table capacity (${table.seats_limit} seats)!`;
            }
            return '';
        },

        openFloorModal(floorId = null) {
            if (floorId) {
                const floor = this.posFloors.find(f => f.id === floorId);
                this.floorForm = {
                    id: floor.id,
                    name: floor.name,
                    number: floor.number
                };
            } else {
                this.floorForm = {
                    id: null,
                    name: '',
                    number: this.posFloors.length + 1
                };
            }
            this.showFloorModal = true;
        },

        async saveFloor() {
            if (!this.floorForm.name) {
                this.showToast(this.isArabic ? "اسم الدور مطلوب" : "Floor name is required", "error");
                return;
            }
            
            try {
                this.loading = true;
                const method = this.floorForm.id ? 'PUT' : 'POST';
                const url = this.floorForm.id ? `/api/pos/floors/${this.floorForm.id}/` : '/api/pos/floors/';
                
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        name: this.floorForm.name,
                        number: this.floorForm.number
                    })
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم حفظ بيانات الدور" : "Floor details saved", "success");
                    this.showFloorModal = false;
                    await this.fetchFloorsAndTables();
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        async deleteFloor(floorId) {
            const { isConfirmed } = await Swal.fire({
                title: this.isArabic ? 'هل أنت متأكد؟' : 'Are you sure?',
                text: this.isArabic ? 'سيتم حذف الدور وجميع الترابيزات الملحقة به!' : 'This will delete the floor and all its tables!',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'نعم، احذف' : 'Yes, delete',
                cancelButtonText: this.isArabic ? 'إلغاء' : 'Cancel'
            });

            if (!isConfirmed) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/pos/floors/${floorId}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم حذف الدور بنجاح" : "Floor deleted successfully", "success");
                    this.activeFloorId = null;
                    await this.fetchFloorsAndTables();
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        openTableModal(table = null) {
            if (table) {
                this.tableForm = {
                    id: table.id,
                    number: table.number,
                    seats_limit: table.seats_limit,
                    shape: table.shape,
                    position_x: table.position_x,
                    position_y: table.position_y
                };
            } else {
                this.tableForm = {
                    id: null,
                    number: '',
                    seats_limit: 4,
                    shape: 'square',
                    position_x: 50,
                    position_y: 50
                };
            }
            this.showTableModal = true;
        },

        async saveTable() {
            if (!this.tableForm.number) {
                this.showToast(this.isArabic ? "رقم الترابيزة مطلوب" : "Table number is required", "error");
                return;
            }
            
            try {
                this.loading = true;
                const method = this.tableForm.id ? 'PUT' : 'POST';
                const url = this.tableForm.id ? `/api/pos/tables/${this.tableForm.id}/` : '/api/pos/tables/';
                
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        floor: this.activeFloorId,
                        number: this.tableForm.number,
                        seats_limit: this.tableForm.seats_limit,
                        shape: this.tableForm.shape,
                        position_x: this.tableForm.position_x,
                        position_y: this.tableForm.position_y
                    })
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم حفظ الترابيزة بنجاح" : "Table saved successfully", "success");
                    this.showTableModal = false;
                    await this.fetchFloorsAndTables();
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        async deleteTable(tableId) {
            const { isConfirmed } = await Swal.fire({
                title: this.isArabic ? 'هل أنت متأكد؟' : 'Are you sure?',
                text: this.isArabic ? 'هل تريد حذف هذه الترابيزة؟' : 'Do you want to delete this table?',
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'نعم، احذف' : 'Yes, delete',
                cancelButtonText: this.isArabic ? 'إلغاء' : 'Cancel'
            });

            if (!isConfirmed) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/pos/tables/${tableId}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم حذف الترابيزة" : "Table deleted", "success");
                    this.showTableModal = false;
                    this.showTableActionModal = false;
                    await this.fetchFloorsAndTables();
                }
            } catch (e) {
                console.error(e);
            } finally {
                this.loading = false;
            }
        },

        isItemOutofStock(item) {
            if (!item.recipe_lines || item.recipe_lines.length === 0) {
                return parseFloat(item.on_hand || 0) <= 0;
            }
            const unavailable = item.recipe_lines.filter(ing => parseFloat(ing.on_hand || 0) <= 0);
            return unavailable.length === item.recipe_lines.length;
        },

        hasMissingIngredients(item) {
            if (!item.recipe_lines || item.recipe_lines.length === 0) return false;
            const unavailable = item.recipe_lines.filter(ing => parseFloat(ing.on_hand || 0) <= 0);
            return unavailable.length > 0 && unavailable.length < item.recipe_lines.length;
        },

        getMissingIngredientsList(item) {
            if (!item.recipe_lines || item.recipe_lines.length === 0) return [];
            return item.recipe_lines.filter(ing => parseFloat(ing.on_hand || 0) <= 0).map(ing => ing.ingredient_name);
        },

        addToCart(item) {
            // Check BOM ingredients stock availability
            let autoNotes = '';
            if (item.recipe_lines && item.recipe_lines.length > 0) {
                const unavailable = item.recipe_lines.filter(ing => parseFloat(ing.on_hand || 0) <= 0);
                if (unavailable.length === item.recipe_lines.length) {
                    this.showToast(this.isArabic ? "عفواً، هذا الصنف غير متاح مؤقتاً لنفاد جميع المكونات" : "Sorry, this item is temporarily unavailable (all ingredients out of stock)", "error");
                    return;
                }
                if (unavailable.length > 0) {
                    autoNotes = this.isArabic 
                        ? `بدون: ${unavailable.map(ing => ing.ingredient_name).join('، ')}` 
                        : `Without: ${unavailable.map(ing => ing.ingredient_name).join(', ')}`;
                }
            }

            const price = parseFloat(item.sales_price || item.standard_price || 0);
            const onHand = parseFloat(item.on_hand || 0);
            const hasNoBOM = !item.recipe_lines || item.recipe_lines.length === 0;

            const existing = this.posCart.find(i => i.id === item.id);
            if (existing) {
                if (hasNoBOM && existing.qty + 1 > onHand) {
                    this.showToast(this.isArabic ? `عفواً، الرصيد المتاح ${onHand} فقط` : `Sorry, only ${onHand} available in stock`, "error");
                    return;
                }
                existing.qty++;
                if (autoNotes && !existing.kitchen_notes) {
                    existing.kitchen_notes = autoNotes;
                }
            } else {
                if (hasNoBOM && onHand <= 0) {
                    this.showToast(this.isArabic ? "عفواً، الصنف غير متوفر في المخزن" : "Sorry, item is out of stock", "error");
                    return;
                }
                this.posCart.push({
                    id: item.id,
                    name: item.name,
                    price: price,
                    tax_rate: item.tax_rate || 15,
                    qty: 1,
                    on_hand: onHand,
                    has_no_bom: hasNoBOM,
                    kitchen_notes: autoNotes
                });
            }
            this.posSelectedCartIndex = this.posCart.findIndex(i => i.id === item.id);
            this.posNumpadBuffer = '';
            this.posShowNumpad = true;
        },

        handleNumpadInput(val) {
            if (this.posSelectedCartIndex === null || this.posSelectedCartIndex >= this.posCart.length) return;
            const item = this.posCart[this.posSelectedCartIndex];
            
            let currentBuffer = this.posNumpadBuffer;
            if (val === 'BS') {
                currentBuffer = currentBuffer.slice(0, -1);
            } else if (val === 'C') {
                currentBuffer = '';
            } else if (val === '.') {
                if (!currentBuffer.includes('.')) currentBuffer += '.';
            } else {
                if (currentBuffer.length < 5) currentBuffer += val;
            }
            
            const newQty = parseFloat(currentBuffer) || 0;
            
            // 🚀 Stock Validation
            if (item.has_no_bom && newQty > item.on_hand) {
                this.showToast(this.isArabic ? `عفواً، أقصى كمية متاحة هي ${item.on_hand}` : `Max available stock is ${item.on_hand}`, "error");
                return;
            }

            this.posNumpadBuffer = currentBuffer;
            if (newQty > 0) {
                item.qty = newQty;
            } else if (this.posNumpadBuffer === '') {
                item.qty = 1;
            }
        },

        async editItemNotes(idx) {
            const line = this.posCart[idx];
            const { value: notes } = await Swal.fire({
                title: this.isArabic ? 'ملاحظات الطلب' : 'Item Notes',
                input: 'textarea',
                inputValue: line.kitchen_notes || '',
                inputPlaceholder: this.isArabic ? 'مثلاً: بدون بصل، فلفل زيادة...' : 'e.g. No onions, extra spicy...',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'حفظ' : 'Save',
                cancelButtonText: this.isArabic ? 'إلغاء' : 'Cancel'
            });
            if (notes !== undefined) {
                line.kitchen_notes = notes;
                this.showToast(this.isArabic ? "تم حفظ الملاحظات" : "Notes saved", "success");
            }
        },

        selectCartItem(index) {
            this.posSelectedCartIndex = index;
            this.posNumpadBuffer = '';
            this.posShowNumpad = true;
        },
        updateCartQty(idx, delta) {
            const item = this.posCart[idx];
            
            // 🚀 Stock Validation for increment
            if (delta > 0 && item.has_no_bom && item.qty + delta > item.on_hand) {
                this.showToast(this.isArabic ? `عفواً، الرصيد المتاح ${item.on_hand} فقط` : `Sorry, only ${item.on_hand} available in stock`, "error");
                return;
            }

            item.qty += delta;
            if (item.qty <= 0) {
                this.posCart.splice(idx, 1);
                if (this.posSelectedCartIndex === idx) this.posSelectedCartIndex = null;
            }
        },
        // 🍽️ DINE-IN: Save order as draft & send to kitchen (no payment yet)
        async sendDineInToKitchen() {
            if (!this.activePOSSession) {
                this.showToast(this.isArabic ? "برجاء فتح وردية أولاً!" : "Please start a session first!", "error");
                return;
            }
            if (this.posCart.length === 0) {
                this.showToast(this.isArabic ? "الطلب فارغ!" : "Cart is empty!", "error");
                return;
            }
            if (!this.posTableNumber) {
                this.showToast(this.isArabic ? "اختر ترابيزة أولاً!" : "Please select a table first!", "error");
                return;
            }

            try {
                this.loading = true;
                const res = await fetch('/api/pos/orders/save_dine_in/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        session: this.activePOSSession.id,
                        table_number: this.posTableNumber,
                        guest_count: this.posGuestCount,
                        existing_order_id: this.posExistingOrderId || null,
                        lines: this.posCart.map(i => ({
                            material: i.id,
                            qty: i.qty,
                            unit_price: parseFloat(i.price.toFixed(2)),
                            subtotal: parseFloat((i.price * i.qty).toFixed(2)),
                            kitchen_notes: i.kitchen_notes || ''
                        }))
                    })
                });

                if (res.ok) {
                    const order = await res.json();
                    this.posExistingOrderId = order.id;  // Track for future updates
                    this.showToast(
                        this.isArabic ? `✅ تم إرسال الطلب للمطبخ! الطاولة ${this.posTableNumber}` : `✅ Order sent to kitchen! Table ${this.posTableNumber}`,
                        "success"
                    );
                    // Clear cart and go back to floor view
                    this.posCart = [];
                    this.posExistingOrderId = null;
                    this.posTableNumber = '';
                    this.posGuestCount = 1;
                    this.posTab = 'floor_layout';
                    await this.fetchFloorsAndTables();
                } else {
                    const err = await res.json();
                    this.showToast(err.error || "Error saving order", "error");
                }
            } catch (e) {
                console.error("Send to Kitchen Error:", e);
                this.showToast("Network Error", "error");
            } finally {
                this.loading = false;
            }
        },

        // 💳 REQUEST BILL: Pay existing Dine-In draft order from Floor Layout
        async requestTableBill(table) {
            if (!table.active_order_detail) {
                this.showToast(this.isArabic ? "لا يوجد طلب مرتبط بهذه الترابيزة" : "No order linked to this table", "error");
                return;
            }

            const orderId = table.active_order_detail.id;
            const orderTotal = parseFloat(table.active_order_total || 0);

            // Show payment method selection
            const { value: method } = await Swal.fire({
                title: this.isArabic ? `طلب شيك - ترابيزة ${table.number}` : `Bill Request - Table ${table.number}`,
                html: `
                    <div style="text-align:right; direction:rtl; margin-bottom: 16px; padding: 12px; background:#f8fafc; border-radius:12px;">
                        <div style="font-size:12px; color:#64748b; font-weight:bold; margin-bottom:4px;">${this.isArabic ? 'الإجمالي المستحق' : 'Total Amount Due'}</div>
                        <div style="font-size:28px; font-weight:900; color:#10b981; font-family:monospace;">${this.formatCurrency(orderTotal)}</div>
                    </div>
                    <div style="font-size:11px; color:#64748b; font-weight:bold; margin-bottom:8px; text-align:right;">${this.isArabic ? 'اختر طريقة الدفع:' : 'Select payment method:'}</div>
                `,
                input: 'radio',
                inputOptions: {
                    'cash':     this.isArabic ? '💵 نقداً (Cash)'         : '💵 Cash',
                    'instapay': this.isArabic ? '📱 إلكتروني (InstaPay)'  : '📱 InstaPay',
                    'credit':   this.isArabic ? '📋 آجل (Credit)'         : '📋 Credit'
                },
                inputValue: 'cash',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? '✅ تأكيد الدفع' : '✅ Confirm Payment',
                cancelButtonText: this.isArabic ? 'إلغاء' : 'Cancel',
                confirmButtonColor: '#10b981',
            });

            if (!method) return;

            try {
                this.loading = true;
                // Process payment for existing draft order
                const payRes = await fetch(`/api/pos/orders/${orderId}/process_payment/`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({ payment_method: method })
                });

                if (payRes.ok) {
                    const payData = await payRes.json();
                    this.showToast(
                        this.isArabic ? `✅ تم الدفع بنجاح! الترابيزة ${table.number} - ${this.formatCurrency(orderTotal)}` : `✅ Payment done! Table ${table.number} - ${this.formatCurrency(orderTotal)}`,
                        "success"
                    );
                    // Print receipt using existing order detail
                    if (table.active_order_detail) {
                        this.printReceipt(table.active_order_detail, table.active_order_detail.lines);
                    }
                    this.showTableActionModal = false;
                    this.refreshAllData();
                } else {
                    const err = await payRes.json();
                    this.showToast(err.error || "Payment Failed", "error");
                }
            } catch (e) {
                console.error("Request Bill Error:", e);
                this.showToast("Network Error", "error");
            } finally {
                this.loading = false;
            }
        },

        async checkoutOrder() {
            if (!this.activePOSSession) {
                this.showToast(this.isArabic ? "برجاء فتح وردية أولاً!" : "Please start a session first!", "error");
                return;
            }
            if (this.posCart.length === 0) {
                this.showToast(this.isArabic ? "العربة فارغة!" : "Cart is empty!", "error");
                return;
            }
            
            // 🚀 Prompt for Payment Method during Checkout
            const { value: method } = await Swal.fire({
                title: this.isArabic ? 'اختر طريقة الدفع' : 'Select Payment Method',
                input: 'radio',
                inputOptions: {
                    'cash': this.isArabic ? 'نقداً (Cash)' : 'Cash',
                    'instapay': this.isArabic ? 'إلكتروني (InstaPay)' : 'InstaPay',
                    'credit': this.isArabic ? 'آجل (Credit)' : 'Credit'
                },
                inputValue: this.posPaymentMethod,
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'تأكيد ودفع' : 'Confirm & Pay'
            });

            if (!method) return;
            this.posPaymentMethod = method;
            
            try {
                this.loading = true;
                const res = await fetch('/api/pos/orders/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        session: this.activePOSSession.id,
                        order_type: this.posOrderType,
                        payment_method: this.posPaymentMethod,
                        table_number: this.posTableNumber,
                        guest_count: this.posGuestCount,
                        total_amount: parseFloat(this.cartTotal.toFixed(2)),
                        lines: this.posCart.map(i => ({
                            material: i.id,
                            qty: i.qty,
                            unit_price: parseFloat(i.price.toFixed(2)),
                            subtotal: parseFloat((i.price * i.qty).toFixed(2)),
                            kitchen_notes: i.kitchen_notes || ''
                        }))
                    })
                });

                if (res.ok) {
                    const order = await res.json();
                    
                    // Link Dine-In order to table
                    if (this.posOrderType === 'DINE_IN' && this.posTableNumber) {
                        const tableObj = this.posTables.find(t => t.number === this.posTableNumber);
                        if (tableObj) {
                            try {
                                await fetch(`/api/pos/tables/${tableObj.id}/assign_order/`, {
                                    method: 'POST',
                                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                                    body: JSON.stringify({ order_id: order.id, current_guests: this.posGuestCount })
                                });
                            } catch (e) {
                                console.error("Error assigning table during checkout:", e);
                            }
                        }
                    }
                    
                    // 2. Process Payment & Deduct Inventory (BOM Deduction)
                    const payRes = await fetch(`/api/pos/orders/${order.id}/process_payment/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                    });

                    if (payRes.ok) {
                        const payData = await payRes.json();
                        this.showToast(this.isArabic ? "تم تأكيد الطلب وخصم المكونات بنجاح!" : "Order Confirmed & Ingredients Deducted!", "success");
                        
                        // 🖨️ طباعة الإيصال تلقائياً
                        this.printReceipt(order, this.posCart);
                        
                        this.posCart = [];
                        this.posTableNumber = '';
                        this.posGuestCount = 1;
                        this.refreshAllData(); // 🚀 تحديث شامل لكل البيانات والتقارير وحركات المخزن فوراً
                    } else {
                        const err = await payRes.json();
                        this.showToast(err.error || "Payment Failed", "error");
                    }
                } else {
                    const err = await res.json();
                    this.showToast(JSON.stringify(err), "error");
                }
            } catch (e) {
                console.error("POS Checkout Error:", e);
                this.showToast("Network Error", "error");
            } finally {
                this.loading = false;
            }
        },
        printReceipt(order, cart) {
            const date = new Date().toLocaleString();
            const itemsHtml = cart.map(i => `
                <div class="item-row">
                    <div class="item-info">
                        <div class="item-name">${i.name || i.material_name}</div>
                        ${i.kitchen_notes ? `<div style="font-size:9px; color: #3b82f6; font-style:italic; font-weight:bold; margin: 2px 0;">* ${i.kitchen_notes}</div>` : ''}
                        <div class="item-details">${i.qty} x ${Number(i.price || i.unit_price).toFixed(2)}</div>
                    </div>
                    <div class="item-price">${((i.price || i.unit_price) * i.qty).toFixed(2)}</div>
                </div>
            `).join('');

            const total = Number(order.total_amount || this.cartTotal);
            const vat = Number(this.cartTax);
            const subtotal = total - vat;
            const brandColor = this.activeOpco && this.activeOpco.brand_color ? this.activeOpco.brand_color : '#1e293b';
            const currency = this.activeOpco ? this.activeOpco.currency : 'EGP';
            const orderRef = order.order_ref || 'DRAFT-POS';
            const cashierName = this.companyUsers.find(u => u.id === this.posActiveCashierId)?.user_details.email || this.user.email || 'Admin';
            
            // Corporate Logo (with SVG Fallback)
            let logoUrl = '';
            if (this.activeOpco && this.activeOpco.logo) {
                logoUrl = this.activeOpco.logo;
                if (logoUrl.startsWith('/')) {
                    logoUrl = window.location.origin + logoUrl;
                }
            } else {
                const logoSvg = `<svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="50" cy="50" r="48" fill="none" stroke="${brandColor}" stroke-width="2"/>
                    <text x="50" y="55" font-family="Arial" font-size="14" font-weight="bold" fill="${brandColor}" text-anchor="middle">LOGO</text>
                </svg>`;
                logoUrl = `data:image/svg+xml;base64,${btoa(logoSvg)}`;
            }
            
            // Barcode and QR APIs
            const barcodeUrl = `https://barcode.tec-it.com/barcode.ashx?data=${orderRef}&code=Code128&translate-esc=true`;
            const qrData = `REDIVIO-POS|${orderRef}|${total}|${this.activeOpco?.name || 'Restaurant'}`;
            const qrUrl = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(qrData)}`;

            const printWindow = window.open('', '_blank', 'width=450,height=850');
            const html = `
                <html>
                <head>
                    <title>Receipt - ${orderRef}</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
                        body { 
                            font-family: 'Inter', sans-serif; 
                            padding: 30px 20px; 
                            color: #1e293b; 
                            max-width: 380px; 
                            margin: 0 auto; 
                            background: #fff; 
                            line-height: 1.4; 
                        }
                        .header { text-align: center; margin-bottom: 25px; border-bottom: 3px solid ${brandColor}; padding-bottom: 20px; }
                        .logo-img { width: 80px; height: 80px; object-fit: contain; margin-bottom: 15px; }
                        .company-name { font-size: 24px; font-weight: 900; text-transform: uppercase; letter-spacing: -0.02em; color: ${brandColor}; }
                        .order-info { 
                            background: #f8fafc; 
                            padding: 15px; 
                            border-radius: 12px; 
                            margin: 20px 0; 
                            text-align: center;
                            border: 1px solid #e2e8f0;
                        }
                        .order-ref { font-weight: 900; font-size: 16px; color: ${brandColor}; margin-bottom: 5px; }
                        .order-meta { font-size: 11px; font-weight: 700; color: #64748b; text-transform: uppercase; }
                        .cashier-meta { font-size: 10px; font-weight: 900; color: #1e293b; margin-top: 8px; padding-top: 8px; border-top: 1px solid #e2e8f0; text-transform: uppercase; }
                        
                        .items { margin: 20px 0; }
                        .item-row { display: flex; justify-content: space-between; margin-bottom: 12px; }
                        .item-info { flex: 1; }
                        .item-name { font-weight: 800; font-size: 14px; color: #0f172a; }
                        .item-details { font-size: 11px; color: #64748b; font-weight: 600; }
                        .item-price { font-weight: 800; font-size: 14px; color: #0f172a; }
                        
                        .divider { border-top: 1px dashed #e2e8f0; margin: 15px 0; }
                        
                        .summary { margin-top: 20px; background: #f1f5f9; padding: 15px; border-radius: 12px; }
                        .summary-line { display: flex; justify-content: space-between; font-size: 13px; font-weight: 600; color: #475569; margin-bottom: 5px; }
                        .total-line { 
                            display: flex; 
                            justify-content: space-between; 
                            font-size: 22px; 
                            font-weight: 900; 
                            margin-top: 10px; 
                            padding-top: 10px; 
                            border-top: 2px solid ${brandColor}; 
                            color: ${brandColor};
                        }
                        
                        .barcodes { margin-top: 30px; text-align: center; }
                        .footer { text-align: center; margin-top: 30px; font-size: 10px; color: #94a3b8; font-weight: 600; }
                        
                        @media print {
                            body { padding: 10px; }
                        }
                    </style>
                </head>
                <body onload="window.print()">
                    <div class="header">
                        <img src="${logoUrl}" class="logo-img">
                        <div class="company-name">${this.activeOpco ? this.activeOpco.name : 'REDIVIO ERP'}</div>
                        <div style="font-size: 11px; font-weight: 700; color: #64748b; margin-top: 5px;">${date}</div>
                    </div>

                    <div class="order-info">
                        <div class="order-ref"># ${orderRef}</div>
                        <div class="order-meta">
                            ${this.isArabic ? 'النوع' : 'Type'}: ${order.order_type} | 
                            ${this.isArabic ? 'الدفع' : 'Pay'}: ${order.payment_method}
                        </div>
                        ${(order.order_type === 'DINE_IN' || order.table_number) ? `
                        <div class="order-meta" style="margin-top: 5px; font-weight: 800; color: #1e293b;">
                            ${this.isArabic ? 'الترابيزة' : 'Table'}: ${order.table_number || '---'} | 
                            ${this.isArabic ? 'عدد الأفراد' : 'Guests'}: ${order.guest_count || 1}
                        </div>
                        ` : ''}
                        <div class="cashier-meta">
                            ${this.isArabic ? 'الكاشير' : 'Cashier'}: ${cashierName}
                        </div>
                    </div>

                    <div class="items">
                        ${cart.map(i => {
                            const note = (i.kitchen_notes || i.notes || "").trim();
                            return `
                                <div class="item-row">
                                    <div class="item-info">
                                        <div class="item-name">${i.name || i.material_name}</div>
                                        ${note ? `<div style="font-size:10px; color: #2563eb; font-weight: 800; margin: 3px 0; border-left: 2px solid #2563eb; padding-left: 5px; font-style: italic;">* ${note}</div>` : ''}
                                        <div class="item-details">${i.qty} x ${Number(i.price || i.unit_price).toFixed(2)}</div>
                                    </div>
                                    <div class="item-price">${((i.price || i.unit_price) * i.qty).toFixed(2)}</div>
                                </div>
                            `;
                        }).join('')}
                    </div>

                    <div class="summary">
                        <div class="summary-line">
                            <span>${this.isArabic ? 'المجموع الفرعي' : 'Subtotal'}</span>
                            <span>${subtotal.toFixed(2)}</span>
                        </div>
                        <div class="summary-line">
                            <span>${this.isArabic ? 'الضريبة (15%)' : 'Tax (15%)'}</span>
                            <span>${vat.toFixed(2)}</span>
                        </div>
                        <div class="total-line">
                            <span>${this.isArabic ? 'الإجمالي' : 'TOTAL'}</span>
                            <span>${total.toFixed(2)} <small style="font-size: 14px;">${currency}</small></span>
                        </div>
                    </div>

                    <div class="barcodes">
                        <img src="${barcodeUrl}" style="height: 45px; width: auto; margin-bottom: 15px; filter: grayscale(1);">
                        <br>
                        <img src="${qrUrl}" style="width: 120px; height: 120px; border: 4px solid #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 8px;">
                        <div style="font-size: 10px; margin-top: 8px; font-weight: 800; letter-spacing: 0.1em; color: #94a3b8;">SCAN TO VERIFY</div>
                    </div>

                    <div class="footer">
                        <p>${this.isArabic ? 'شكراً لزيارتكم ونتمنى رؤيتكم قريباً' : 'THANK YOU FOR YOUR VISIT! SEE YOU AGAIN.'}</p>
                        <p style="font-size: 9px; margin-top: 8px;">${this.activeOpco?.tax_id ? 'Tax ID: ' + this.activeOpco.tax_id : ''}</p>
                        <p style="font-size: 8px; margin-top: 15px; opacity: 0.5;">Tax Invoice Generated by REDIVIO CLOUD POS</p>
                    </div>
                </body>
                </html>
            `;
            
            printWindow.document.open();
            printWindow.document.write(html);
            printWindow.document.close();
            
            setTimeout(() => {
                printWindow.focus();
                printWindow.print();
                printWindow.close();
            }, 600);
        },

        async endSession() {
            // 1. Show Preview First
            try {
                this.loading = true;
                const prevRes = await fetch('/api/pos/orders/session_preview/?opco=' + this.activeOpcoId);
                if (prevRes.ok) {
                    const summary = await prevRes.json();
                    const { value: actualBalance } = await Swal.fire({
                        title: this.isArabic ? 'إغلاق الوردية وتصفية الحساب' : 'Close Shift & Settlement',
                        html: `
                            <div style="text-align:right; font-size: 14px;" dir="rtl">
                                <p>رصيد البداية: <b>${Number(summary.opening_balance).toFixed(2)}</b></p>
                                <div style="margin: 10px 0; padding: 10px; bg-slate-50; border-radius: 10px; border: 1px solid #eee;">
                                    <p style="color:#059669">مبيعات كاش (+): <b>${Number(summary.cash_sales).toFixed(2)}</b></p>
                                    <p style="color:#6366f1">مبيعات إلكترونية (InstaPay): <b>${Number(summary.instapay_sales).toFixed(2)}</b></p>
                                    <p style="color:#f43f5e">مبيعات آجلة (Credit): <b>${Number(summary.credit_sales).toFixed(2)}</b></p>
                                </div>
                                <p>إجمالي المصاريف (-): <b style="color:red">${Number(summary.total_expenses).toFixed(2)}</b></p>
                                <hr>
                                <p style="font-size:18px">الرصيد الكاش المتوقع: <b style="color:#0f172a">${Number(summary.expected_cash).toFixed(2)}</b></p>
                                <p style="font-size:10px; color:#666">*(لا يشمل الفيزا أو الأونلاين)*</p>
                                <br>
                                <label>أدخل المبلغ الفعلي الموجود في الدرج الآن:</label>
                            </div>
                        `,
                        input: 'number',
                        inputAttributes: { step: '0.01' },
                        inputValue: summary.expected_cash,
                        showCancelButton: true,
                        confirmButtonText: this.isArabic ? 'تأكيد الإغلاق' : 'Confirm Close'
                    });

                    if (actualBalance === undefined || actualBalance === null) return;
                    
                    const res = await fetch('/api/pos/orders/close_session/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCookie('csrftoken')
                        },
                        body: JSON.stringify({ 
                            opco: this.activeOpcoId,
                            actual_balance: actualBalance
                        })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        this.activePOSSession = null;
                        this.showToast(this.isArabic ? "تم إغلاق الوردية" : "Shift closed");
                    }
                }
            } catch (e) {
                this.showToast("Error closing session", "error");
            } finally {
                this.loading = false;
            }
        },

        async addCashTransaction() {
            if (!this.activePOSSession) {
                this.showToast(this.isArabic ? "برجاء فتح وردية أولاً!" : "Please start a session first!", "error");
                return;
            }

            const { value: formValues } = await Swal.fire({
                title: this.isArabic ? 'إدارة النقدية بالخزينة' : 'Cash Drawer Management',
                html: `
                    <div style="text-align:right" dir="rtl" class="space-y-4">
                        <div class="mb-3">
                            <label style="font-weight:bold; font-size:12px; color:#666; display:block; margin-bottom:5px;">نوع العملية</label>
                            <select id="swal-type" class="swal2-input" style="margin: 0; width: 100%;">
                                <option value="IN">${this.isArabic ? 'إيداع / إضافة كاش (Cash In)' : 'Cash In'}</option>
                                <option value="OUT">${this.isArabic ? 'صرف / سحب كاش (Cash Out)' : 'Cash Out'}</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label style="font-weight:bold; font-size:12px; color:#666; display:block; margin-bottom:5px;">المبلغ</label>
                            <input id="swal-amount" class="swal2-input" type="number" step="0.01" placeholder="0.00" style="margin: 0; width: 100%;">
                        </div>
                        <div class="mb-3">
                            <label style="font-weight:bold; font-size:12px; color:#666; display:block; margin-bottom:5px;">السبب / البيان</label>
                            <input id="swal-reason" class="swal2-input" type="text" placeholder="${this.isArabic ? 'مثلاً: دفعة تمويل، شراء خضروات، عجز عهده...' : 'e.g. Cash supply, buying supplies...'}" style="margin: 0; width: 100%;">
                        </div>
                    </div>
                `,
                focusConfirm: false,
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'تأكيد وحفظ' : 'Confirm & Save',
                cancelButtonText: this.isArabic ? 'إلغاء' : 'Cancel',
                preConfirm: () => {
                    const type = document.getElementById('swal-type').value;
                    const amount = document.getElementById('swal-amount').value;
                    const reason = document.getElementById('swal-reason').value;
                    if (!amount || amount <= 0) {
                        Swal.showValidationMessage(this.isArabic ? 'برجاء إدخال مبلغ صحيح' : 'Please enter a valid amount');
                        return false;
                    }
                    if (!reason) {
                        Swal.showValidationMessage(this.isArabic ? 'برجاء إدخال سبب العملية' : 'Please enter a reason');
                        return false;
                    }
                    return { type, amount, reason };
                }
            });

            if (!formValues) return;

            try {
                this.loading = true;
                const res = await fetch('/api/pos/orders/add_transaction/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        type: formValues.type,
                        amount: formValues.amount,
                        reason: formValues.reason
                    })
                });
                
                if (res.ok) {
                    this.showToast(this.isArabic ? "تم تسجيل العملية وطباعة الإيصال" : "Transaction recorded & Receipt printed", "success");
                    
                    // 🚀 طباعة إيصال النقدية
                    this.printExpenseReceipt({
                        type: formValues.type,
                        amount: formValues.amount,
                        reason: formValues.reason,
                        cashier: this.user.name || 'Admin',
                        session_id: this.activePOSSession.id
                    });
                    
                    this.refreshAllData();
                } else {
                    const err = await res.json();
                    this.showToast(err.error || "Error", "error");
                }
            } catch (e) {
                this.showToast("Network Error", "error");
            } finally {
                this.loading = false;
            }
        },

        printExpenseReceipt(data) {
            const date = new Date().toLocaleString();
            const currency = this.activeOpco ? this.activeOpco.currency : 'EGP';
            const companyName = this.activeOpco ? this.activeOpco.name : 'REDIVIO POS';
            
            const printWindow = window.open('', '_blank', 'width=450,height=500');
            const html = `
                <html>
                <head>
                    <title>${data.type === 'IN' ? 'Receipt Voucher' : 'Expense Voucher'}</title>
                    <style>
                        body { font-family: 'Courier New', Courier, monospace; padding: 20px; text-align: center; line-height: 1.4; }
                        .header { border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }
                        .title { font-size: 20px; font-weight: bold; text-transform: uppercase; margin: 10px 0; }
                        .detail-row { display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px; }
                        .amount-box { border: 2px solid #000; padding: 15px; font-size: 24px; font-weight: bold; margin: 20px 0; }
                        .footer { margin-top: 30px; font-size: 12px; border-top: 1px dashed #000; padding-top: 10px; }
                        .signature { margin-top: 40px; display: flex; justify-content: space-between; }
                        .sig-line { border-top: 1px solid #000; width: 100px; padding-top: 5px; }
                    </style>
                </head>
                <body onload="window.print(); window.close();">
                    <div class="header">
                        <div class="title">${data.type === 'IN' ? (this.isArabic ? 'إيصال إيداع نقدية' : 'CASH IN VOUCHER') : (this.isArabic ? 'إيصال صرف نقدية' : 'CASH OUT VOUCHER')}</div>
                        <div>${companyName}</div>
                    </div>
                    
                    <div class="detail-row">
                        <span>Date / الوقت:</span>
                        <span>${date}</span>
                    </div>
                    <div class="detail-row">
                        <span>Session ID / الوردية:</span>
                        <span>#${data.session_id}</span>
                    </div>
                    <div class="detail-row">
                        <span>Cashier / الكاشير:</span>
                        <span>${data.cashier}</span>
                    </div>
                    
                    <div class="divider" style="border-top:1px dashed #000; margin:15px 0;"></div>
                    
                    <div style="text-align:left; margin-bottom:10px; font-weight:bold;">Reason / البيان:</div>
                    <div style="text-align:left; font-size:16px; margin-bottom:20px; padding:10px; background:#f9f9f9;">${data.reason}</div>
                    
                    <div class="amount-box">
                        ${Number(data.amount).toFixed(2)} ${currency}
                    </div>
                    
                    <div class="signature">
                        <div>
                            <div class="sig-line">Cashier</div>
                        </div>
                        <div>
                            <div class="sig-line">Supervisor</div>
                        </div>
                    </div>
                    
                    <div class="footer">
                        <p>REDIVIO POS System - Printed on ${date}</p>
                    </div>
                </body>
                </html>
            `;
            printWindow.document.write(html);
            printWindow.document.close();
        },

        exportReportToExcel(reportType) {
            let filename = '';
            let headers = [];
            let rows = [];
            
            const currency = this.activeOpco ? this.activeOpco.currency : 'EGP';

            if (reportType === 'detailed_sales') {
                filename = `Detailed_Sales_Report_${Date.now()}.csv`;
                headers = [
                    this.isArabic ? 'الاسم' : 'Item Name',
                    this.isArabic ? 'المجموعة' : 'Category',
                    this.isArabic ? 'الكمية المباعة' : 'Qty Sold',
                    this.isArabic ? 'إجمالي المبيعات' : 'Total Revenue',
                    this.isArabic ? 'إجمالي التكلفة' : 'Total Cost',
                    this.isArabic ? 'مجمل الربح' : 'Gross Profit'
                ];
                (this.posStats.top_items || []).forEach(item => {
                    const gross = item.total_sales - item.total_cost;
                    rows.push([
                        item.name,
                        item.category,
                        item.qty,
                        `${item.total_sales.toFixed(2)} ${currency}`,
                        `${item.total_cost.toFixed(2)} ${currency}`,
                        `${gross.toFixed(2)} ${currency}`
                    ]);
                });
            } else if (reportType === 'cash_log') {
                filename = `Cash_Drawer_Log_${Date.now()}.csv`;
                headers = [
                    this.isArabic ? 'التاريخ والوقت' : 'Date & Time',
                    this.isArabic ? 'نوع العملية' : 'Type',
                    this.isArabic ? 'المبلغ' : 'Amount',
                    this.isArabic ? 'السبب والبيان' : 'Reason / Description',
                    this.isArabic ? 'الكاشير' : 'Cashier'
                ];
                (this.posStats.cash_transactions || []).forEach(t => {
                    rows.push([
                        t.created_at,
                        t.type === 'IN' ? (this.isArabic ? 'إيداع' : 'Deposit') : (this.isArabic ? 'سحب / مصروفات' : 'Withdrawal'),
                        `${t.amount.toFixed(2)} ${currency}`,
                        t.reason,
                        t.cashier
                    ]);
                });
            } else if (reportType === 'pl_summary') {
                filename = `Profit_Loss_Summary_${Date.now()}.csv`;
                headers = [
                    this.isArabic ? 'البند' : 'Account Description',
                    this.isArabic ? 'المبلغ' : 'Amount'
                ];
                const stats = this.posStats;
                rows = [
                    [this.isArabic ? 'إجمالي الإيرادات مبيعات' : 'Total Sales Revenue', `${stats.total_revenue.toFixed(2)} ${currency}`],
                    [this.isArabic ? 'تكلفة البضاعة المباعة (COGS)' : 'Cost of Goods Sold (COGS)', `-${stats.total_cogs.toFixed(2)} ${currency}`],
                    [this.isArabic ? 'مجمل الربح' : 'Gross Profit', `${stats.gross_profit.toFixed(2)} ${currency}`],
                    [this.isArabic ? 'مشتريات مخزنية (-)' : 'Inventory Purchases (-)', `-${stats.total_purchases.toFixed(2)} ${currency}`],
                    [this.isArabic ? 'المصروفات التشغيلية والعمومية (-)' : 'Operational Expenses (-)', `-${stats.total_expenses.toFixed(2)} ${currency}`],
                    [this.isArabic ? 'التدفقات والمقبوضات النقدية (+)' : 'Cash Inflows (+)', `+${(stats.total_inflows || 0).toFixed(2)} ${currency}`],
                    [this.isArabic ? 'صافي الربح النهائي' : 'Final Net Profit', `${stats.net_profit.toFixed(2)} ${currency}`]
                ];
            }

            // Export to CSV with UTF-8 BOM
            let csvContent = "\uFEFF"; // UTF-8 BOM for Excel Arabic support
            csvContent += headers.join(",") + "\n";
            rows.forEach(row => {
                csvContent += row.map(val => {
                    const str = String(val === null || val === undefined ? '' : val).replace(/"/g, '""');
                    return `"${str}"`;
                }).join(",") + "\n";
            });
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement("a");
            if (link.download !== undefined) {
                const url = URL.createObjectURL(blob);
                link.setAttribute("href", url);
                link.setAttribute("download", filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        },

        printReportPDF(reportType) {
            const dateStr = new Date().toLocaleString();
            const currency = this.activeOpco ? this.activeOpco.currency : 'EGP';
            const companyName = this.activeOpco ? this.activeOpco.name : 'REDIVIO POS';
            
            let reportTitle = '';
            let contentHtml = '';

            if (reportType === 'detailed_sales') {
                reportTitle = this.isArabic ? 'تقرير مبيعات الأصناف بالتفصيل' : 'Detailed Item Sales Report';
                let rowsHtml = '';
                (this.posStats.top_items || []).forEach(item => {
                    const gross = item.total_sales - item.total_cost;
                    rowsHtml += `
                        <tr>
                            <td>${item.name}</td>
                            <td>${item.category}</td>
                            <td class="text-center">${item.qty}</td>
                            <td class="text-right">${item.total_sales.toFixed(2)} ${currency}</td>
                            <td class="text-right">${item.total_cost.toFixed(2)} ${currency}</td>
                            <td class="text-right ${gross >= 0 ? 'text-green' : 'text-red'}">${gross.toFixed(2)} ${currency}</td>
                        </tr>
                    `;
                });
                
                contentHtml = `
                    <table>
                        <thead>
                            <tr>
                                <th>${this.isArabic ? 'اسم الصنف' : 'Item Name'}</th>
                                <th>${this.isArabic ? 'المجموعة' : 'Category'}</th>
                                <th class="text-center">${this.isArabic ? 'الكمية' : 'Qty'}</th>
                                <th class="text-right">${this.isArabic ? 'الإيراد' : 'Revenue'}</th>
                                <th class="text-right">${this.isArabic ? 'التكلفة' : 'Cost'}</th>
                                <th class="text-right">${this.isArabic ? 'مجمل الربح' : 'Gross Profit'}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml || `<tr><td colspan="6" class="text-center">${this.isArabic ? 'لا توجد بيانات' : 'No data available'}</td></tr>`}
                        </tbody>
                    </table>
                `;
            } else if (reportType === 'cash_log') {
                reportTitle = this.isArabic ? 'سجل التدفق النقدي وحركة الخزينة' : 'Cash Drawer Transactions Log';
                let rowsHtml = '';
                (this.posStats.cash_transactions || []).forEach(t => {
                    rowsHtml += `
                        <tr>
                            <td>${t.created_at}</td>
                            <td>${t.type === 'IN' ? `<span class="badge badge-green">${this.isArabic ? 'إيداع نقدية' : 'Cash In'}</span>` : `<span class="badge badge-red">${this.isArabic ? 'صرف مصروفات' : 'Cash Out'}</span>`}</td>
                            <td class="text-right font-bold">${t.amount.toFixed(2)} ${currency}</td>
                            <td>${t.reason}</td>
                            <td>${t.cashier}</td>
                        </tr>
                    `;
                });

                contentHtml = `
                    <table>
                        <thead>
                            <tr>
                                <th>${this.isArabic ? 'التاريخ والوقت' : 'Date & Time'}</th>
                                <th>${this.isArabic ? 'نوع الحركة' : 'Type'}</th>
                                <th class="text-right">${this.isArabic ? 'المبلغ' : 'Amount'}</th>
                                <th>${this.isArabic ? 'السبب والبيان' : 'Reason / Description'}</th>
                                <th>${this.isArabic ? 'الكاشير' : 'Cashier'}</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml || `<tr><td colspan="5" class="text-center">${this.isArabic ? 'لا توجد بيانات' : 'No data available'}</td></tr>`}
                        </tbody>
                    </table>
                `;
            } else if (reportType === 'pl_summary') {
                reportTitle = this.isArabic ? 'قائمة الدخل وتلخيص الأرباح والخسائر' : 'Income Statement Summary';
                const stats = this.posStats;
                contentHtml = `
                    <div style="max-width: 500px; margin: 0 auto;">
                        <div class="pl-line">
                            <span>${this.isArabic ? 'إجمالي الإيرادات المبيعات (+)' : 'Total Sales Revenue (+)'}</span>
                            <span class="font-bold">${stats.total_revenue.toFixed(2)} ${currency}</span>
                        </div>
                        <div class="pl-line" style="border-bottom: 1px solid #ddd; padding-bottom: 8px;">
                            <span>${this.isArabic ? 'تكلفة البضاعة المباعة COGS (-)' : 'Cost of Goods Sold COGS (-)'}</span>
                            <span class="text-red font-bold">-${stats.total_cogs.toFixed(2)} ${currency}</span>
                        </div>
                        <div class="pl-line" style="font-size: 18px; font-weight: bold; margin: 10px 0;">
                            <span>${this.isArabic ? 'مجمل الربح (Gross Profit)' : 'Gross Profit'}</span>
                            <span class="text-green">${stats.gross_profit.toFixed(2)} ${currency}</span>
                        </div>
                        <div class="pl-line">
                            <span>${this.isArabic ? 'مشتريات مخزنية (-)' : 'Inventory Purchases (-)'}</span>
                            <span class="text-red">-${stats.total_purchases.toFixed(2)} ${currency}</span>
                        </div>
                        <div class="pl-line">
                            <span>${this.isArabic ? 'المصروفات التشغيلية والعمومية (-)' : 'Operational Expenses (-)'}</span>
                            <span class="text-red">-${stats.total_expenses.toFixed(2)} ${currency}</span>
                        </div>
                        <div class="pl-line" style="border-bottom: 2px double #333; padding-bottom: 12px; margin-bottom: 10px;">
                            <span>${this.isArabic ? 'التدفقات والمقبوضات النقدية (+)' : 'Cash Inflows (+)'}</span>
                            <span class="text-green">+${(stats.total_inflows || 0).toFixed(2)} ${currency}</span>
                        </div>
                        <div class="pl-line font-bold" style="font-size: 22px; color: #1e3a8a;">
                            <span>${this.isArabic ? 'صافي الربح النهائي (Net Profit)' : 'Final Net Profit'}</span>
                            <span class="${stats.net_profit >= 0 ? 'text-green' : 'text-red'}">${stats.net_profit.toFixed(2)} ${currency}</span>
                        </div>
                    </div>
                `;
            }

            const printWindow = window.open('', '_blank', 'width=800,height=700');
            const isRtl = this.isArabic;
            const html = `
                <html>
                <head>
                    <title>${reportTitle}</title>
                    <style>
                        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
                        body { 
                            font-family: 'Cairo', sans-serif; 
                            padding: 40px; 
                            color: #334155; 
                            direction: ${isRtl ? 'rtl' : 'ltr'}; 
                            text-align: ${isRtl ? 'right' : 'left'};
                        }
                        .header { text-align: center; border-bottom: 2px solid #cbd5e1; padding-bottom: 20px; margin-bottom: 30px; }
                        .company { font-size: 20px; font-weight: bold; color: #1e293b; }
                        .title { font-size: 24px; font-weight: 900; color: #dc2626; margin: 10px 0; }
                        .date { font-size: 12px; color: #64748b; }
                        
                        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                        th, td { padding: 12px 15px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
                        th { background-color: #f8fafc; font-weight: bold; color: #0f172a; text-align: ${isRtl ? 'right' : 'left'}; }
                        tr:hover { background-color: #f8fafc; }
                        
                        .text-right { text-align: right; }
                        .text-center { text-align: center; }
                        .font-bold { font-weight: bold; }
                        
                        .text-green { color: #10b981; }
                        .text-red { color: #ef4444; }
                        
                        .badge { padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: bold; }
                        .badge-green { background-color: #d1fae5; color: #065f46; }
                        .badge-red { background-color: #fee2e2; color: #991b1b; }
                        
                        .pl-line { display: flex; justify-content: space-between; margin: 12px 0; font-size: 14px; }
                        
                        .footer { margin-top: 50px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #cbd5e1; padding-top: 20px; }
                        @media print {
                            body { padding: 0; }
                            button { display: none; }
                        }
                    </style>
                </head>
                <body onload="window.print();">
                    <div class="header">
                        <div class="company">${companyName}</div>
                        <div class="title">${reportTitle}</div>
                        <div class="date">${this.isArabic ? 'تاريخ استخراج التقرير' : 'Generated on'}: ${dateStr}</div>
                    </div>
                    
                    <div class="content">
                        ${contentHtml}
                    </div>
                    
                    <div class="footer">
                        REDIVIO ERP • Restaurant Management & Intelligence System
                    </div>
                </body>
                </html>
            `;
            printWindow.document.write(html);
            printWindow.document.close();
        },

        async fetchPOSDashboard() {
            try {
                this.loading = true;
                let url = `/api/pos/orders/dashboard_stats/?opco=${this.activeOpcoId}`;
                if (this.posDashboardFilters.from) url += `&from=${this.posDashboardFilters.from}`;
                if (this.posDashboardFilters.to) url += `&to=${this.posDashboardFilters.to}`;
                
                const res = await fetch(url);
                if (res.ok) {
                    this.posStats = await res.json();
                }
            } catch (e) {
                this.showToast("Error fetching stats", "error");
            } finally {
                this.loading = false;
            }
        },

        async selectPOSDateRange() {
            const { value: formValues } = await Swal.fire({
                title: this.isArabic ? 'اختر الفترة الزمنية' : 'Select Date Range',
                html: `
                    <div style="text-align:right" dir="rtl">
                        <label>من تاريخ:</label>
                        <input id="swal-from" class="swal2-input" type="date" value="${this.posDashboardFilters.from}">
                        <label>إلى تاريخ:</label>
                        <input id="swal-to" class="swal2-input" type="date" value="${this.posDashboardFilters.to}">
                    </div>
                `,
                focusConfirm: false,
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'تطبيق الفلتر' : 'Apply Filter',
                cancelButtonText: this.isArabic ? 'إلغاء' : 'Cancel',
                preConfirm: () => {
                    return {
                        from: document.getElementById('swal-from').value,
                        to: document.getElementById('swal-to').value
                    }
                }
            });

            if (formValues) {
                this.posDashboardFilters.from = formValues.from;
                this.posDashboardFilters.to = formValues.to;
                this.fetchPOSDashboard();
            }
        },

        async fetchSessionsHistory() {
            try {
                this.loading = true;
                const res = await fetch('/api/pos/orders/session_history/?opco=' + this.activeOpcoId);
                if (res.ok) {
                    this.posSessionsHistory = await res.json();
                }
            } catch (e) {
                console.error("Fetch Sessions Error:", e);
            } finally {
                this.loading = false;
            }
        },

        async viewSessionDetails(session) {
            this.selectedSession = session;
            try {
                this.loading = true;
                // جلب الطلبات والمصروفات لنفس الجلسة
                const [ordersRes, transRes] = await Promise.all([
                    fetch(`/api/pos/orders/?opco=${this.activeOpcoId}&session=${session.id}`),
                    fetch(`/api/pos/orders/cash_transactions/?opco=${this.activeOpcoId}&session=${session.id}`)
                ]);

                let orders = [];
                let trans = [];

                if (ordersRes.ok) orders = await ordersRes.json();
                if (transRes.ok) trans = await transRes.json();

                // دمج القائمتين مع تمييز النوع
                this.posOrdersHistory = [
                    ...orders.map(o => ({ ...o, is_order: true })),
                    ...trans.map(t => ({ ...t, is_transaction: true, order_ref: 'CASH-OUT', total_amount: t.amount, status: 'paid', customer_name: t.reason }))
                ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

            } catch (e) {
                console.error("Fetch Session Details Error:", e);
            } finally {
                this.loading = false;
            }
        },

        async refundOrder(order) {
            const { isConfirmed } = await Swal.fire({
                title: this.isArabic ? 'هل أنت متأكد؟' : 'Are you sure?',
                text: this.isArabic ? `سيتم إرجاع مبلغ ${order.total_amount} وخصمه من الدرج` : `Amount of ${order.total_amount} will be refunded and deducted from drawer`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'تأكيد الإرجاع' : 'Confirm Refund'
            });

            if (!isConfirmed) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/pos/orders/${order.id}/refund_order/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });
                if (res.ok) {
                    this.showToast(this.isArabic ? "تم إرجاع الطلب بنجاح" : "Order refunded successfully", "success");
                    this.fetchOrdersHistory();
                }
            } catch (e) {
                this.showToast("Error refunding order", "error");
            } finally {
                this.loading = false;
            }
        },

        async fetchOrdersHistory() {
            try {
                this.loading = true;
                const [ordersRes, transRes] = await Promise.all([
                    fetch('/api/pos/orders/?opco=' + this.activeOpcoId),
                    fetch('/api/pos/orders/cash_transactions/?opco=' + this.activeOpcoId)
                ]);

                let orders = [];
                let trans = [];

                if (ordersRes.ok) orders = await ordersRes.json();
                if (transRes.ok) trans = await transRes.json();

                this.posOrdersHistory = [
                    ...orders.map(o => ({ ...o, is_order: true })),
                    ...trans.map(t => ({ ...t, is_transaction: true, order_ref: 'CASH-OUT', total_amount: t.amount, status: 'paid', customer_name: t.reason }))
                ].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

            } catch (e) {
                console.error("Fetch Orders Error:", e);
            } finally {
                this.loading = false;
            }
        },

        async checkActivePOSSession() {
            try {
                let url = '/api/pos/orders/active_session/?opco=' + this.activeOpcoId;
                if (this.selectedTerminalId) {
                    url += '&terminal=' + this.selectedTerminalId;
                }
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.id) {
                        this.activePOSSession = data;
                        this.posMode = data.terminal_type === 'DIRECT' ? 'direct' : 'restaurant';
                    } else {
                        this.activePOSSession = null;
                    }
                }
            } catch (e) { console.error("Session Check Error", e); }
        },

        async startPOSSession() {
            if (!this.selectedTerminalId) {
                this.showToast(this.isArabic ? "برجاء اختيار جهاز نقطة البيع" : "Please select a POS Terminal", "warning");
                return;
            }
            if (!this.posActiveCashierId) {
                this.showToast(this.isArabic ? "برجاء اختيار الكاشير" : "Please select a cashier", "warning");
                return;
            }

            // --- Password Verification Logic ---
            const selectedUser = this.companyUsers.find(u => u.id === this.posActiveCashierId) || (this.posActiveCashierId === 'OWNER' ? { user_details: { email: this.user.email } } : null);
            
            const { value: password } = await Swal.fire({
                title: this.isArabic ? 'التحقق من الهوية' : 'Security Check',
                input: 'password',
                inputLabel: (this.isArabic ? 'كلمة المرور لـ ' : 'Password for ') + (selectedUser?.user_details.email || selectedUser?.user_details.username || 'Admin'),
                inputPlaceholder: '********',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'تأكيد' : 'Verify'
            });

            if (!password) return;

            try {
                this.loading = true;
                const verifyRes = await fetch('/api/company-users/verify_password/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        user_id: this.posActiveCashierId,
                        password: password
                    })
                });

                if (!verifyRes.ok) {
                    this.showToast(this.isArabic ? "كلمة المرور غير صحيحة" : "Invalid Password", "error");
                    return;
                }
            } catch (e) {
                this.showToast("Connection Error", "error");
                return;
            } finally {
                this.loading = false;
            }
            // --- End Password Verification ---

            const openingBalance = parseFloat(this.posOpeningBalance) || 0;

            try {
                this.loading = true;
                const res = await fetch('/api/pos/orders/start_session/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        cashier_name: this.companyUsers.find(u => u.id === this.posActiveCashierId)?.user_details.email || this.user.email || 'Admin',
                        cashier_id: this.posActiveCashierId,
                        opening_balance: openingBalance,
                        terminal: this.selectedTerminalId
                    })
                });
                
                if (res.ok) {
                    const session = await res.json();
                    this.activePOSSession = session;
                    this.posMode = session.terminal_type === 'DIRECT' ? 'direct' : 'restaurant';
                    this.showToast(this.isArabic ? "تم فتح الوردية بنجاح" : "Session started successfully", "success");
                } else {
                    const err = await res.json();
                    this.showToast(err.error || (this.isArabic ? "خطأ في بدء الوردية" : "Error starting session"), "error");
                }
            } catch (e) {
                this.showToast("Error starting session", "error");
            } finally {
                this.loading = false;
            }
        },

        async fetchPOSTerminals() {
            try {
                this.loading = true;
                // Fetch company users in parallel to ensure lock screen lists load correctly
                this.fetchCompanyUsers();
                const res = await fetch(`/api/pos/terminals/?opco=${this.activeOpcoId}`);
                if (res.ok) {
                    this.posTerminals = await res.json();
                    
                    if (!this.selectedTerminalId && this.posTerminals.length > 0) {
                        this.selectedTerminalId = this.posTerminals[0].id;
                        localStorage.setItem('selected_terminal_id', this.selectedTerminalId);
                    }
                    
                    if (this.selectedTerminalId) {
                        this.onTerminalSelectionChange();
                    }
                }
            } catch (e) {
                console.error("Error fetching terminals:", e);
            } finally {
                this.loading = false;
            }
        },

        async onTerminalSelectionChange() {
            if (!this.selectedTerminalId) return;
            localStorage.setItem('selected_terminal_id', this.selectedTerminalId);
            
            try {
                this.loading = true;
                const res = await fetch(`/api/pos/orders/active_session/?opco=${this.activeOpcoId}&terminal=${this.selectedTerminalId}`);
                if (res.ok) {
                    const session = await res.json();
                    if (session && session.id) {
                        this.activePOSSession = session;
                        this.posMode = session.terminal_type === 'DIRECT' ? 'direct' : 'restaurant';
                    } else {
                        this.activePOSSession = null;
                        const term = this.posTerminals.find(t => t.id === parseInt(this.selectedTerminalId));
                        if (term) {
                            this.posMode = term.terminal_type === 'DIRECT' ? 'direct' : 'restaurant';
                        }
                    }
                }
            } catch (e) {
                console.error("Error checking terminal session:", e);
            } finally {
                this.loading = false;
            }
        },

        getAllowedCashiers() {
            const cashiers = this.companyUsers.filter(u => ['cashier', 'administrator', 'admin', 'manager'].includes(u.role.toLowerCase()));
            if (!this.selectedTerminalId) return cashiers;
            const term = this.posTerminals.find(t => t.id === parseInt(this.selectedTerminalId));
            if (!term || !term.allowed_users || term.allowed_users.length === 0) {
                return cashiers;
            }
            return cashiers.filter(c => term.allowed_users.includes(c.user));
        },

        openTerminalModal(term = null) {
            this.fetchCompanyUsers();
            if (term) {
                this.terminalForm = {
                    id: term.id,
                    code: term.code,
                    name: term.name,
                    terminal_type: term.terminal_type,
                    is_active: term.is_active,
                    allowed_users: term.allowed_users ? [...term.allowed_users] : []
                };
            } else {
                this.terminalForm = {
                    id: null,
                    code: 'POS-' + String(this.posTerminals.length + 1).padStart(2, '0'),
                    name: '',
                    terminal_type: 'DIRECT',
                    is_active: true,
                    allowed_users: []
                };
            }
            this.showTerminalFormModal = true;
        },

        async savePOSTerminal() {
            if (!this.terminalForm.code || !this.terminalForm.name) {
                this.showToast(this.isArabic ? "الكود والاسم مطلوبان" : "Code and Name are required", "error");
                return;
            }
            try {
                this.loading = true;
                const method = this.terminalForm.id ? 'PUT' : 'POST';
                const url = this.terminalForm.id ? `/api/pos/terminals/${this.terminalForm.id}/` : '/api/pos/terminals/';
                const res = await fetch(url, {
                    method,
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        opco: this.activeOpcoId,
                        code: this.terminalForm.code,
                        name: this.terminalForm.name,
                        terminal_type: this.terminalForm.terminal_type,
                        is_active: this.terminalForm.is_active,
                        allowed_users: this.terminalForm.allowed_users || []
                    })
                });
                if (res.ok) {
                    this.showToast(this.isArabic ? "تم حفظ جهاز نقطة البيع" : "POS terminal saved successfully", "success");
                    this.showTerminalFormModal = false;
                    await this.fetchPOSTerminals();
                } else {
                    const err = await res.json();
                    this.showToast(JSON.stringify(err), "error");
                }
            } catch (e) {
                console.error("Error saving terminal:", e);
            } finally {
                this.loading = false;
            }
        },

        async toggleTerminalActive(term) {
            try {
                this.loading = true;
                const res = await fetch(`/api/pos/terminals/${term.id}/`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({ is_active: !term.is_active })
                });
                if (res.ok) {
                    this.showToast(this.isArabic ? "تم تحديث حالة جهاز نقطة البيع" : "Terminal status updated", "success");
                    await this.fetchPOSTerminals();
                }
            } catch (e) {
                console.error("Error toggling terminal:", e);
            } finally {
                this.loading = false;
            }
        },

        async fetchInventoryMoves() {
            this.loading = true;
            try {
                let url = `/api/wms/moves/?opco=${this.activeOpcoId || ''}`;
                if (this.reportFilters) {
                    if (this.reportFilters.material_id) url += `&material_id=${this.reportFilters.material_id}`;
                    if (this.reportFilters.location_id) url += `&location_id=${this.reportFilters.location_id}`;
                    if (this.reportFilters.date_from) url += `&date_from=${this.reportFilters.date_from}`;
                    if (this.reportFilters.date_to) url += `&date_to=${this.reportFilters.date_to}`;
                }
                const res = await fetch(url);
                if (res.ok) {
                    const data = await res.json();
                    this.inventoryMoves = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) { console.error("Moves Fetch Error", e); }
            finally { this.loading = false; }
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

        viewContactLedger() {
            if (this.forms.stock_entry.receipt_type === 'PURCHASE' && this.forms.stock_entry.contact_id) {
                const vendor = this.vendors.find(v => v.id === this.forms.stock_entry.contact_id);
                if (vendor) {
                    this.showModal = false;
                    this.fetchVendorLedger(vendor);
                }
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
            const vendorCode = "V-" + Math.floor(Math.random() * 3000);

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
            return date.toLocaleDateString(this.isArabic ? 'ar-EG' : 'en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        formatTime(dateStr) {
            if (!dateStr) return '---';
            const date = new Date(dateStr);
            return date.toLocaleTimeString(this.isArabic ? 'ar-EG' : 'en-US', {
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
            
            // If it's already a full URL or data URI, return as is
            if (path.startsWith('http') || path.startsWith('data:')) {
                return path;
            }

            // Clean up localhost paths from dev environments
            if (path.includes('localhost') || path.includes('127.0.0.1')) {
                const parts = path.split('/media/');
                if (parts.length > 1) path = parts[1];
            }

            // Ensure it starts with /media/
            let cleanPath = path;
            if (cleanPath.startsWith('/')) cleanPath = cleanPath.substring(1);
            if (!cleanPath.startsWith('media/')) {
                cleanPath = 'media/' + cleanPath;
            }
            
            return '/' + cleanPath;
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
                    logo: finalLogo,
                    system_mode: active.system_mode || 'modular',
                    purchased_modules: active.purchased_modules || []
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

        addRecipeLine() {
            itemMasterModule.methods.addRecipeLine(this);
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
                    sales_price: itemData.sales_price || 0,
                    tax_rate: itemData.tax_rate || 15,
                    is_pos_item: itemData.is_pos_item || false,
                    recipe_lines: itemData.recipe_lines || [],
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
                        const errorText = await res.text();
                        console.error("Delete Error:", errorText);
                        let errorMessage = "";
                        try {
                            const errJson = JSON.parse(errorText);
                            errorMessage = errJson.error || errJson.detail || "";
                        } catch (e) {}
                        
                        if (errorMessage) {
                            this.showToast(this.isArabic ? `فشل الحذف: ${errorMessage}` : `Delete failed: ${errorMessage}`, 'error');
                        } else {
                            this.showToast(this.isArabic ? "فشل الحذف: قد يكون العنصر مرتبطاً ببيانات أخرى" : "Delete failed: Item may be linked to other data", 'error');
                        }
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
                        else if (type === 'material' && key === 'recipe_lines') {
                            payload.append('recipe_lines', JSON.stringify(data[key]));
                        }
                        else if (type === 'material' && key === 'combo_lines') {
                            payload.append('combo_lines', JSON.stringify(data[key]));
                        }
                        else if (type === 'material' && key === 'allowed_terminals') {
                            payload.append('allowed_terminals', JSON.stringify(data[key]));
                        }
                        else if (data[key] !== null && !['logo', 'image', 'assigned_bins', 'primary_bin', 'company_assignments', 'recipe_lines', 'combo_lines', 'allowed_terminals'].includes(key)) {
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
                    const errorText = await response.text();
                    let errorMessage = errorText;
                    try {
                        const errJson = JSON.parse(errorText);
                        const firstKey = Object.keys(errJson)[0];
                        if (firstKey) {
                            const val = errJson[firstKey];
                            errorMessage = Array.isArray(val) ? val[0] : (typeof val === 'object' ? JSON.stringify(val) : val);
                        }
                    } catch (e) {
                        // Keep text as is
                    }
                    this.showToast(this.isArabic ? "فشل الحفظ: " + errorMessage : "Save failed: " + errorMessage, 'error');
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
                formData.append('system_mode', this.config.system_mode || 'modular');
                formData.append('purchased_modules', JSON.stringify(this.config.purchased_modules || []));

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
                    logo: logoUrl,
                    system_mode: updatedData.system_mode || 'modular',
                    purchased_modules: updatedData.purchased_modules || []
                };
                
                // Update active state in Vue memory
                this.systemMode = updatedData.system_mode || 'modular';
                this.purchasedModules = updatedData.purchased_modules || [];
                
                // If Stand Alone, jump directly to the single module and skip ECC
                if (this.systemMode === 'standalone') {
                    const defaultModule = this.sidebarGroups.operations.find(m => m.id !== 'org_builder' && this.isModulePurchased(m.id));
                    if (defaultModule) {
                        this.view = defaultModule.id;
                    }
                }
            }

            this.newLogoFile = null;
            // ✅ رسالة نجاح احترافية
            this.showToast(this.isArabic ? 'تم حفظ البيانات بنجاح' : 'Data saved successfully', 'success');
        },

        downloadPlantTemplate() {
            const isAr = this.isArabic;
            const headers = isAr ? 'الكود,الاسم' : 'Plant Code,Plant Name';
            const sample1 = isAr ? 'PL01,المنشأة الأولى' : 'PL01,First Plant';
            const sample2 = isAr ? 'PL02,المنشأة الثانية' : 'PL02,Second Plant';
            
            const csvContent = "data:text/csv;charset=utf-8,\uFEFF" + headers + "\n" + sample1 + "\n" + sample2;
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", isAr ? "نموذج_المنشآت.csv" : "plant_template.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        triggerPlantImport() {
            if (this.$refs.plantExcelFile) {
                this.$refs.plantExcelFile.click();
            } else {
                const el = document.querySelector('input[type="file"][ref="plantExcelFile"]');
                if (el) el.click();
            }
        },

        async uploadPlantExcel(event) {
            const file = event.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('file', file);
            
            this.loading = true;
            try {
                const response = await fetch('/api/plants/import/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: formData
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    this.showToast(this.isArabic 
                        ? `تم استيراد ${result.success_count} بنجاح، وتم تخطي ${result.skipped_count} مكررين.` 
                        : `Successfully imported ${result.success_count}, skipped ${result.skipped_count} duplicates.`, 
                        'success');
                    await this.refreshAllData();
                } else {
                    this.showToast(this.isArabic ? "فشل الاستيراد: " + (result.error || '') : "Import Failed: " + (result.error || ''), 'error');
                }
            } catch (e) {
                this.showToast(this.isArabic ? "حدث خطأ في الاتصال بالسيرفر" : "Server connection error", 'error');
            } finally {
                this.loading = false;
                event.target.value = ''; // Reset input
            }
        },

        downloadLocationTemplate() {
            const isAr = this.isArabic;
            const headers = isAr ? 'كود المنشأة,كود الموقع,اسم الموقع' : 'Plant Code,Location Code,Location Name';
            const sample1 = isAr ? 'PL01,LOC01,الموقع الأول' : 'PL01,LOC01,First Location';
            
            const csvContent = "data:text/csv;charset=utf-8,\uFEFF" + headers + "\n" + sample1;
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", isAr ? "نموذج_المواقع.csv" : "location_template.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        triggerLocationImport() {
            if (this.$refs.locationExcelFile) this.$refs.locationExcelFile.click();
            else {
                const el = document.querySelector('input[type="file"][ref="locationExcelFile"]');
                if (el) el.click();
            }
        },

        async uploadLocationExcel(event) {
            const file = event.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            this.loading = true;
            try {
                const response = await fetch('/api/locations/import/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    this.showToast(this.isArabic 
                        ? `تم استيراد ${result.success_count} بنجاح، وتم تخطي ${result.skipped_count} مكررين.` 
                        : `Successfully imported ${result.success_count}, skipped ${result.skipped_count} duplicates.`, 'success');
                    await this.refreshAllData();
                } else {
                    this.showToast(this.isArabic ? "فشل الاستيراد: " + (result.error || '') : "Import Failed: " + (result.error || ''), 'error');
                }
            } catch (e) {
                this.showToast(this.isArabic ? "حدث خطأ في الاتصال بالسيرفر" : "Server connection error", 'error');
            } finally {
                this.loading = false;
                event.target.value = '';
            }
        },

        downloadBinTemplate() {
            const isAr = this.isArabic;
            const headers = isAr ? 'كود الموقع,كود الرف' : 'Location Code,Bin Code';
            const sample1 = isAr ? 'LOC01,BIN01' : 'LOC01,BIN01';
            
            const csvContent = "data:text/csv;charset=utf-8,\uFEFF" + headers + "\n" + sample1;
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", isAr ? "نموذج_الأرفف.csv" : "bin_template.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        },

        triggerBinImport() {
            if (this.$refs.binExcelFile) this.$refs.binExcelFile.click();
            else {
                const el = document.querySelector('input[type="file"][ref="binExcelFile"]');
                if (el) el.click();
            }
        },

        async uploadBinExcel(event) {
            const file = event.target.files[0];
            if (!file) return;
            const formData = new FormData();
            formData.append('file', file);
            this.loading = true;
            try {
                const response = await fetch('/api/bins/import/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: formData
                });
                const result = await response.json();
                if (response.ok) {
                    this.showToast(this.isArabic 
                        ? `تم استيراد ${result.success_count} بنجاح، وتم تخطي ${result.skipped_count} مكررين.` 
                        : `Successfully imported ${result.success_count}, skipped ${result.skipped_count} duplicates.`, 'success');
                    await this.refreshAllData();
                } else {
                    this.showToast(this.isArabic ? "فشل الاستيراد: " + (result.error || '') : "Import Failed: " + (result.error || ''), 'error');
                }
            } catch (e) {
                this.showToast(this.isArabic ? "حدث خطأ في الاتصال بالسيرفر" : "Server connection error", 'error');
            } finally {
                this.loading = false;
                event.target.value = '';
            }
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
                    this.fetchVendors(),
                    this.fetchCompanyUsers(),
                    this.fetchFloorsAndTables(),
                    this.fetchPOSDashboard()
                ]);
                if (this.activeOpcoId) this.syncGlobalConfig(this.activeOpcoId);
            } catch (e) {
                console.error("Error in refreshAllData:", e);
            } finally {
                this.loading = false;
            }
        },

        isModulePurchased(modId) {
            if (this.systemMode === 'standalone') {
                if (!this.purchasedModules || this.purchasedModules.length === 0) {
                    return modId === 'restaurant_pos_module';
                }
            } else {
                if (!this.purchasedModules || this.purchasedModules.length === 0) return true;
            }
            
            const idMap = {
                'inventory_module': 'wms',
                'procurement_module': 'procurement',
                'sales_module': 'sales',
                'accounting_module': 'sales',
                'restaurant_pos_module': 'restaurant_pos'
            };
            
            const mappedId = idMap[modId] || modId;
            return this.purchasedModules.includes(mappedId);
        },

        isConfigModuleSelected(modId) {
            if (!this.config || !this.config.purchased_modules) return false;
            
            const idMap = {
                'inventory_module': 'wms',
                'procurement_module': 'procurement',
                'sales_module': 'sales',
                'accounting_module': 'sales',
                'restaurant_pos_module': 'restaurant_pos'
            };
            const mappedId = idMap[modId] || modId;
            return this.config.purchased_modules.includes(mappedId);
        },

        setConfigMode(mode) {
            this.config.system_mode = mode;
            if (mode === 'standalone' && this.config.purchased_modules && this.config.purchased_modules.length > 1) {
                this.config.purchased_modules = [this.config.purchased_modules[0]];
            }
        },

        toggleConfigModule(modId) {
            if (!this.config.purchased_modules) {
                this.config.purchased_modules = [];
            }
            
            const idMap = {
                'inventory_module': 'wms',
                'procurement_module': 'procurement',
                'sales_module': 'sales',
                'accounting_module': 'sales',
                'restaurant_pos_module': 'restaurant_pos'
            };
            const mappedId = idMap[modId] || modId;

            if (this.config.purchased_modules.includes(mappedId)) {
                if (this.config.purchased_modules.length > 1) {
                    this.config.purchased_modules = this.config.purchased_modules.filter(m => m !== mappedId);
                }
            } else {
                if (this.config.system_mode === 'standalone') {
                    this.config.purchased_modules = [mappedId];
                } else {
                    this.config.purchased_modules.push(mappedId);
                }
            }
        },

        async checkAuth() {
            try {
                const res = await fetch('/api/check-auth/');
                const data = await res.json();
                if (data.authenticated) {
                    this.user = {
                        id: data.user_id,
                        name: data.user,
                        is_superuser: data.is_superuser,
                        role: data.role
                    };

                    this.license = {
                        daysRemaining: data.days_remaining,
                        companyName: data.holding_name,
                        isExpired: data.days_remaining <= 0,
                        plan: data.plan || 'free',
                        skuLimit: data.sku_limit || 50,
                        daysLimit: data.days_limit || 15,
                        skuCount: data.sku_count || 0
                    };
                    
                    this.systemMode = data.system_mode || 'modular';
                    this.purchasedModules = data.purchased_modules || [];
                    
                    // If Stand Alone, jump directly to the single module and skip Executive Command Center
                    if (this.systemMode === 'standalone') {
                        const defaultModule = this.sidebarGroups.operations.find(m => m.id !== 'org_builder' && this.isModulePurchased(m.id));
                        if (defaultModule) {
                            this.view = defaultModule.id;
                        }
                    }

                    await this.fetchAll();
                    this.activeOpcoId = data.company_id || (this.allOpcos[0] ? this.allOpcos[0].id : null);
                    this.syncGlobalConfig(this.activeOpcoId);
                    await this.refreshAllData();
                }
            } catch (e) { console.error("Auth Error", e); }
        },

        async changePlan(planType) {
            try {
                this.loading = true;
                const response = await fetch('/api/change-plan/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ plan: planType })
                });
                
                const data = await response.json();
                if (data.success) {
                    this.showSubscriptionModal = false;
                    Swal.fire({
                        title: this.isArabic ? 'تم تحديث الخطة بنجاح!' : 'Plan Updated Successfully!',
                        text: this.isArabic 
                            ? `تم تغيير خطتك الحالية إلى ${planType.toUpperCase()}`
                            : `Your plan has been updated to ${planType.toUpperCase()}`,
                        icon: 'success',
                        background: '#0f172a',
                        color: '#fff',
                        confirmButtonColor: '#3b82f6'
                    });
                    await this.checkAuth();
                } else {
                    Swal.fire({
                        title: this.isArabic ? 'حدث خطأ' : 'Error',
                        text: data.error || (this.isArabic ? 'فشل تحديث الخطة.' : 'Failed to update plan.'),
                        icon: 'error',
                        background: '#0f172a',
                        color: '#fff',
                        confirmButtonColor: '#3b82f6'
                    });
                }
            } catch (e) {
                console.error("Error changing plan:", e);
                Swal.fire({
                    title: this.isArabic ? 'خطأ في الاتصال' : 'Connection Error',
                    text: this.isArabic ? 'يرجى التحقق من اتصالك بالشبكة.' : 'Please check your network connection.',
                    icon: 'error',
                    background: '#0f172a',
                    color: '#fff',
                    confirmButtonColor: '#3b82f6'
                });
            } finally {
                this.loading = false;
            }
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
                
                this.fetchSaleGroups();
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
            window.open('/api/wms/inventory/print_audit/?pdf=1', '_blank');
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
                    id: null, sku: '', name: '', category: '', sale_group: '', base_uom: 'PCS', barcode: '',
                    standard_price: 0, sales_price: 0, tax_rate: 15, is_pos_item: false, is_combo: false,
                    company_assignments: [{ opco_id: this.activeOpcoId, bins: [], primary_bin: null }],
                    tracking: 'none', reorder_level: 0, max_level: 0, recipe_lines: [], combo_lines: []
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
            this.activeOperation = 'so_delivery';
            this.modalType = 'delivery';
            this.showModal = true;
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
                    await this.fetchSalesOrders();
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

        async fetchSaleGroups() {
            try {
                const url = this.activeOpcoId ? `/api/sale-groups/?opco=${this.activeOpcoId}` : '/api/sale-groups/';
                const res = await fetch(url);
                if (res.ok) {
                    this.sale_groups = await res.json();
                }
            } catch (e) { console.error("Error fetching sale groups:", e); }
        },

        async addSaleGroup() {
            const { value: name } = await Swal.fire({
                title: this.isArabic ? 'إضافة مجموعة بيعية جديدة' : 'Add New Sale Group',
                input: 'text',
                inputPlaceholder: this.isArabic ? 'اسم المجموعة (مثلاً: مشروبات، بيتزا...)' : 'Group Name (e.g. Drinks, Pizza...)',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? 'حفظ' : 'Save'
            });

            if (name) {
                try {
                    const res = await fetch('/api/sale-groups/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': this.getCookie('csrftoken')
                        },
                        body: JSON.stringify({ 
                            name: name,
                            opco: this.activeOpcoId
                        })
                    });
                    if (res.ok) {
                        this.showToast(this.isArabic ? "تمت الإضافة بنجاح" : "Group added successfully", 'success');
                        this.fetchSaleGroups();
                    }
                } catch (e) { this.showToast("Error", 'error'); }
            }
        },

        // --- Kitchen Display System (KDS) Methods ---
        async fetchKDSOrders() {
            try {
                const res = await fetch(`/api/pos/orders/kds_orders/?opco=${this.activeOpcoId}`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.length > this.kdsOrders.length) {
                        // Notify kitchen of new orders
                        const newOrdersCount = data.length - this.kdsOrders.length;
                        this.showToast(this.isArabic ? `وصل ${newOrdersCount} طلب جديد للمطبخ!` : `${newOrdersCount} New Orders Received!`, "success");
                        
                        const sound = this.$refs.notificationSound;
                        if (sound) {
                            sound.currentTime = 0;
                            sound.play().catch(e => console.log("Sound blocked"));
                        }
                    }
                    this.kdsOrders = data;
                }
            } catch (e) { console.error("KDS Fetch Error", e); }
        },

        onKDSDragStart(event, order) {
            this.draggedOrder = order;
            event.dataTransfer.effectAllowed = 'move';
            event.target.classList.add('opacity-50');
        },

        async onKDSDrop(event, targetStatus) {
            if (!this.draggedOrder) return;
            const order = this.draggedOrder;
            if (order.status === targetStatus) return;
            try {
                const res = await fetch(`/api/pos/orders/${order.id}/update_kitchen_status/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ status: targetStatus })
                });
                if (res.ok) {
                    order.status = targetStatus;
                    if (targetStatus === 'inprogress') order.started_at = new Date().toISOString();
                    this.showToast(this.isArabic ? "تم تحديث حالة الطلب" : "Order status updated", "success");
                    await this.fetchKDSOrders();
                }
            } catch (e) {
                this.showToast("KDS Update Error", "error");
            } finally {
                this.draggedOrder = null;
            }
        },

        async updateOrderStatus(orderId, targetStatus) {
            try {
                this.loading = true;
                const res = await fetch(`/api/pos/orders/${orderId}/update_kitchen_status/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken')
                    },
                    body: JSON.stringify({ status: targetStatus })
                });
                if (res.ok) {
                    this.showToast(this.isArabic ? "تم تحديث حالة الطلب" : "Order status updated", "success");
                    await this.fetchKDSOrders();
                }
            } catch (e) {
                this.showToast("KDS Update Error", "error");
            } finally {
                this.loading = false;
            }
        },

        getWaitTime(timestamp) {
            if (!timestamp) return '0m';
            const start = new Date(timestamp);
            const now = this.kdsCurrentTime;
            const diff = Math.floor((now - start) / 1000);
            if (diff < 60) return `${diff}s`;
            const mins = Math.floor(diff / 60);
            const secs = diff % 60;
            return `${mins}m ${secs}s`;
        },

        canAccess(module) {
            const role = (this.user.role || '').toLowerCase();
            if (role === 'admin' || this.user.is_superuser) return true;
            
            // Mapping roles to permissions
            const permissions = {
                'dashboard': ['manager', 'admin'],
                'inventory_module': ['warehouse', 'manager', 'admin'],
                'procurement_module': ['warehouse', 'manager', 'admin'],
                'sales_module': ['manager', 'admin'],
                'accounting_module': ['manager', 'admin'],
                'users': ['manager', 'admin'],
                'global_config': ['manager', 'admin'],
                'org_builder': ['manager', 'admin'],
                
                // Restaurant POS Internal Tabs
                'pos_cashier': ['cashier', 'manager', 'admin'],
                'pos_kitchen': ['kitchen', 'manager', 'admin'],
                'pos_dashboard': ['manager', 'admin'],
                'pos_recipes': ['warehouse', 'manager', 'admin'],
                'pos_history': ['manager', 'admin']
            };

            if (permissions[module]) {
                return permissions[module].includes(role);
            }
            return true; // Default Allow
        },

        async fetchCompanyUsers() {
            try {
                const res = await fetch(`/api/company-users/?opco=${this.activeOpcoId}`);
                if (res.ok) {
                    this.companyUsers = await res.json();
                }
            } catch (e) { console.error("Fetch Users Error", e); }
        },

        async saveCompanyUser() {
            try {
                const isNew = !this.forms.user.id;
                const url = isNew ? '/api/company-users/' : `/api/company-users/${this.forms.user.id}/`;
                const method = isNew ? 'POST' : 'PUT';
                
                const res = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: JSON.stringify({
                        email: this.forms.user.email,
                        role: this.forms.user.role,
                        company: this.forms.user.company || this.activeOpcoId,
                        password: this.forms.user.password
                    })
                });

                if (res.ok) {
                    this.showToast(this.isArabic ? "تم حفظ المستخدم" : "User saved successfully", "success");
                    this.showModal = false;
                    this.forms.user.password = '';
                    await this.fetchCompanyUsers();
                } else {
                    const err = await res.json();
                    this.showToast(err.error || "Error saving user", "error");
                }
            } catch (e) { console.error("Save User Error", e); }
        },

        async deleteCompanyUser(id) {
            if (!confirm(this.isArabic ? "هل أنت متأكد من حذف هذا المستخدم؟" : "Are you sure you want to delete this user?")) return;
            try {
                const res = await fetch(`/api/company-users/${id}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });
                if (res.ok) {
                    this.showToast(this.isArabic ? "تم الحذف" : "Deleted successfully", "success");
                    await this.fetchCompanyUsers();
                }
            } catch (e) { console.error("Delete User Error", e); }
        },

        formatTime(isoString) {
            if (!isoString) return '--:--';
            const date = new Date(isoString);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        },

        handleNotificationAction(action, idx) {
            if (action === 'delete' || action === 'done') {
                this.notifications.splice(idx, 1);
            } else if (action === 'postpone') {
                const notif = this.notifications[idx];
                this.notifications.splice(idx, 1);
                // Re-add after 1 minute (simplified postpone)
                setTimeout(() => {
                    this.notifications.push(notif);
                    this.showToast(this.isArabic ? "تذكير: " + notif.title : "Reminder: " + notif.title, "info");
                }, 60000);
            }
        },

        async checkPOSStatusUpdates() {
            try {
                const res = await fetch(`/api/pos/orders/?opco=${this.activeOpcoId}`);
                if (res.ok) {
                    const data = await res.json();
                    data.forEach(order => {
                        const oldStatus = this.posOrdersState[order.id];
                        if (oldStatus && oldStatus !== order.status) {
                            // Status changed! Notify cashier
                            let msg = this.isArabic ? 
                                `تغيرت حالة الطلب ${order.order_ref} إلى ${order.status}` : 
                                `Order ${order.order_ref} status changed to ${order.status}`;
                            
                            this.notifications.unshift({
                                type: 'pos_ready',
                                title: this.isArabic ? 'تحديث طلب' : 'Order Update',
                                message: msg,
                                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                            });

                            if (order.status === 'done' || order.status === 'paid') {
                                this.showToast(msg, "success");
                            }
                        }
                        this.posOrdersState[order.id] = order.status;
                    });
                }
            } catch (e) { console.error("POS Update Check Error", e); }
        }
    }
}).mount('#app');
