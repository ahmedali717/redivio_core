import { utils } from './modules/utils.js';
import { inventoryModule } from './modules/inventory.js';
import { orgModule } from './modules/org_builder.js';
import { itemMasterModule } from './modules/itemMaster.js';

console.log("≡ƒÜÇ REDIVIO Core v1.0.5 Loaded");
console.log("≡ƒîì Current Language Mode (isArabic):", window.is_arabic);

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            searchQuery: '',
            scannerInstance: null,
            isScanning: false, // ┘ä╪º╪▓┘à ┘è╪¬╪╣╪▒┘ü ┘ç┘å╪º ╪╣╪┤╪º┘å ╪º┘ä┘Ç HTML ┘è╪┤┘ê┘ü┘ç
            barcodeQuery: '',
            // ≡ƒÜÇ ╪╢┘è┘ü ╪º┘ä┘à╪¬╪║┘è╪▒ ╪»┘ç ┘ç┘å╪º ┘ü┘è ╪ú┘ê┘ä ╪│╪╖╪▒
            activeOperation: null,
            showBrandDropdown: false,
            showActivityLog: false,
            showNotificationsDropdown: false,
            
            // SaaS Configurations
            systemMode: 'modular',
            purchasedModules: [],

            // ≡ƒÜÇ ╪º┘ä╪¬╪╣╪»┘è┘ä ╪º┘ä╪ú┘ê┘ä: ╪╢┘è┘ü ╪º┘ä╪│╪╖╪▒┘è┘å ╪»┘ê┘ä ┘ç┘å╪º ╪¿╪º┘ä╪╕╪¿╪╖
            showQtyModal: false,
            scannedItemData: {
                material_id: null,
                material_name: '',
                sku: '',
                ordered_qty: 0,
                scan_qty: 1
            },

            // 1. ╪¼╪╣┘ä ╪º┘ä┘à┘ê╪»┘è┘ê┘ä ╪º┘ä┘à┘ê╪¡╪» ┘ç┘ê ╪º┘ä╪┤╪º╪┤╪⌐ ╪º┘ä╪º┘ü╪¬╪▒╪º╪╢┘è╪⌐ (╪º╪«╪¬┘è╪º╪▒┘è)
            view: 'dashboard',
            inventoryMoves: [],
            // ≡ƒÜÇ ╪Ñ╪╢╪º┘ü╪⌐ ╪º┘ä┘à╪¬╪║┘è╪▒ ╪º┘ä╪¼╪»┘è╪» ┘ä┘ä╪¬╪¿╪»┘è┘ä ╪¿┘è┘å ╪º┘ä╪ú╪╡┘å╪º┘ü ┘ê╪º┘ä╪ú╪▒╪╡╪»╪⌐
            inventoryTab: 'levels',
            posTab: 'cashier',
            activePOSSession: null,
            posCart: [],
            posSearch: '',
            posCategory: 'all',
            posPaymentMethod: 'cash',
            posStats: { total_revenue: 0, cash_total: 0, instapay_total: 0, credit_total: 0, top_items: [], ingredients: [] },
            posSelectedCartIndex: null,
            posShowNumpad: false,
            // ≡ƒôà ┘ü┘ä╪º╪¬╪▒ ┘ä┘ê╪¡╪⌐ ╪¬╪¡┘â┘à ╪º┘ä┘à╪╖╪╣┘à
            posDashboardFilters: {
                from: '',
                to: ''
            },
            posNumpadBuffer: '',
            posOrderType: 'DINE_IN',
            posTableNumber: '',
            posGuestCount: 1,
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

            confirmModal: {
                show: false,
                onConfirm: null,
                onCancel: null
            },

            // 2. ╪¬╪¡╪»┘è╪½ ╪º┘ä┘é╪º╪ª┘à╪⌐ ╪º┘ä╪¼╪º┘å╪¿┘è╪⌐ ┘ä╪¬┘â┘ê┘å "┘à┘ê╪»┘è┘ê┘ä╪º╪¬" ╪¿╪»┘ä╪º┘ï ┘à┘å ╪┤╪º╪┤╪º╪¬
            sidebarGroups: {
                settings: [
                    { id: 'global_config', name: { ar: '╪º┘ä╪Ñ╪╣╪»╪º╪»╪º╪¬ ╪º┘ä╪╣╪º┘à╪⌐', en: 'Global Config' }, icon: 'fas fa-cogs' },
                    { id: 'users', name: { ar: '╪º┘ä┘à╪│╪¬╪«╪»┘à┘è┘å', en: 'Users' }, icon: 'fas fa-users' }
                ],
                operations: [
                    { id: 'org_builder', name: { ar: '╪¿┘å╪º╪í ╪º┘ä┘ç┘è┘â┘ä', en: 'Org Builder' }, icon: 'fas fa-sitemap' },
                    // ┘à┘ê╪»┘è┘ê┘ä ┘ê╪º╪¡╪» ╪┤╪º┘à┘ä ┘ä┘ä┘à╪«╪▓┘ê┘å
                    { id: 'inventory_module', name: { ar: 'RIMS (╪º┘ä┘à╪«╪▓┘ê┘å)', en: 'RIMS (Inventory)' }, icon: 'fas fa-archive' },
                    { id: 'procurement_module', name: { ar: 'RPMS (╪º┘ä┘à╪┤╪¬╪▒┘è╪º╪¬)', en: 'RPMS (Procurement)' }, icon: 'fas fa-shopping-cart' },
                    { id: 'sales_module', name: { ar: '╪Ñ╪»╪º╪▒╪⌐ ╪º┘ä┘à╪¿┘è╪╣╪º╪¬', en: 'Sales & CRM' }, icon: 'fas fa-cart-shopping' },
                    { id: 'accounting_module', name: { ar: '╪º┘ä┘à╪¡╪º╪│╪¿╪⌐ ┘ê╪º┘ä┘à╪º┘ä┘è╪⌐', en: 'Accounting' }, icon: 'fas fa-file-invoice-dollar' },
                    { id: 'restaurant_pos_module', name: { ar: '┘å┘é╪╖╪⌐ ╪º┘ä╪¿┘è╪╣ (POS)', en: 'Restaurant POS' }, icon: 'fas fa-utensils' }
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
                plant: { ar: '╪Ñ╪╢╪º┘ü╪⌐ ┘à┘å╪┤╪ú╪⌐ ╪¼╪»┘è╪»╪⌐', en: 'Add New Facility' },
                location: { ar: '╪Ñ╪╢╪º┘ü╪⌐ ┘à┘ê┘é╪╣ ╪¬╪«╪▓┘è┘å', en: 'Add Storage Location' },
                bin: { ar: '╪Ñ╪╢╪º┘ü╪⌐ ╪▒┘ü/╪¡╪º┘ê┘è╪⌐', en: 'Add New Bin' },
                material: { ar: '╪¬╪╣╪▒┘è┘ü ╪╡┘å┘ü ╪¼╪»┘è╪»', en: 'Define New Material' },
                stock_entry: { ar: '╪Ñ╪░┘å ╪º╪│╪¬┘ä╪º┘à / ╪¬╪¡┘ê┘è┘ä ┘à╪«╪▓┘å┘è', en: 'Stock Inbound / Transfer' },
                po: { ar: '╪ú┘à╪▒ ╪¬┘ê╪▒┘è╪» ╪¼╪»┘è╪»', en: 'New Purchase Order' },
                opco: { ar: '╪Ñ╪╢╪º┘ü╪⌐ ╪┤╪▒┘â╪⌐ ╪¬╪º╪¿╪╣╪⌐ / ┘à╪┤╪║┘ä╪⌐', en: 'Add Subsidiary / OpCo' },
                salesorder: { ar: '╪ú┘à╪▒ ╪¿┘è╪╣ ╪¼╪»┘è╪»', en: 'New Sales Order' },
                customer: { ar: '╪¿┘è╪º┘å╪º╪¬ ╪╣┘à┘è┘ä ╪¼╪»┘è╪»', en: 'Customer Information' },

                // ≡ƒÜÇ ╪º┘ä╪│╪╖┘ê╪▒ ╪º┘ä┘ä┘è ┘â╪º┘å╪¬ ┘å╪º┘é╪╡╪⌐ ┘ê╪╣╪º┘à┘ä╪⌐ ╪º┘ä┘à╪┤┘â┘ä╪⌐ ╪¬┘à ╪Ñ╪╢╪º┘ü╪¬┘ç╪º ┘ç┘å╪º:
                view_po: { ar: '╪¬┘ü╪º╪╡┘è┘ä ╪ú┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪»', en: 'Purchase Order Details' },
                payment: { ar: '╪¬╪¡╪╡┘è┘ä ╪»┘ü╪╣╪⌐ ┘à╪º┘ä┘è╪⌐', en: 'Record Payment' },
                delivery: { ar: '╪╡╪▒┘ü ╪¿╪╢╪º╪╣╪⌐', en: 'Order Delivery' },
                so_delivery: { ar: '╪╡╪▒┘ü ╪¿╪╢╪º╪╣╪⌐ ┘à┘å ╪ú┘à╪▒ ╪¿┘è╪╣', en: 'WMS Sales Delivery' }
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
                    // ≡ƒÜÇ ╪º┘ä┘ç┘è┘â┘ä ╪º┘ä╪¼╪»┘è╪» ┘ä╪»╪╣┘à ╪¬╪╣╪»╪» ╪º┘ä╪┤╪▒┘â╪º╪¬
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
                    is_tax_inclusive: false, // ╪┤╪º┘à┘ä ╪º┘ä╪╢╪▒┘è╪¿╪⌐╪ƒ
                    tax_rate: 15, // ┘å╪│╪¿╪⌐ ╪º┘ä╪╢╪▒┘è╪¿╪⌐ ╪º┘ä╪º┘ü╪¬╪▒╪º╪╢┘è╪⌐
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
        posCategories() {
            // ╪│┘å╪│╪¬╪«╪»┘à ╪º┘ä┘à╪¼┘à┘ê╪╣╪º╪¬ ╪º┘ä╪¿┘è╪╣┘è╪⌐ ╪¿╪»┘ä╪º┘ï ┘à┘å ╪º┘ä┘ü╪ª╪º╪¬ ╪º┘ä╪╣╪º┘à╪⌐ ┘ü┘è ╪º┘ä┘Ç POS
            return this.sale_groups || [];
        },
        filteredPosItems() {
            // ┘ü┘ä╪¬╪▒╪⌐ ╪º┘ä╪ú╪╡┘å╪º┘ü ╪º┘ä╪¬┘è ╪¬╪¡┘à┘ä ╪╣┘ä╪º┘à╪⌐ POS Item ┘ü┘é╪╖
            let items = (this.materials_list || []).filter(i => i.is_pos_item);
            
            if (this.posCategory !== 'all') {
                // ╪º┘ä┘ü┘ä╪¬╪▒╪⌐ ┘ç┘å╪º ╪¬╪¬┘à ╪¿┘å╪º╪í┘ï ╪╣┘ä┘ë ID ╪º┘ä┘à╪¼┘à┘ê╪╣╪⌐ ╪º┘ä╪¿┘è╪╣┘è╪⌐
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
            
            // ╪º┘ä╪¿╪¡╪½ ╪╣┘å ╪º┘ä╪┤╪▒┘â╪⌐ ╪º┘ä╪¡╪º┘ä┘è╪⌐
            const opco = this.allOpcos.find(o => parseInt(o.id) === parseInt(this.activeOpcoId));
            if (!opco) return null;

            // ≡ƒÜÇ ┘à┘å╪╖┘é ╪º┘ä┘ê╪▒╪º╪½╪⌐ (Inheritance Logic)
            // ╪Ñ╪░╪º ┘â╪º┘å╪¬ ╪º┘ä╪┤╪▒┘â╪⌐ ┘ü╪▒╪╣┘è╪⌐ ┘ê┘ä┘è╪│ ┘ä┘ç╪º ┘ä┘ê╪¼┘ê╪î ┘å╪¿╪¡╪½ ┘ü┘è ╪º┘ä╪┤╪▒┘â╪⌐ ╪º┘ä╪ú┘à ┘ê┘ç┘â╪░╪º
            let current = opco;
            let finalLogo = current.logo;
            let finalColor = current.brand_color;

            // ┘à╪¡╪º┘ê┘ä╪⌐ ╪¼┘ä╪¿ ╪º┘ä┘ä┘ê╪¼┘ê ┘ê╪º┘ä┘ä┘ê┘å ┘à┘å ╪º┘ä┘ç┘è┘â┘ä ╪º┘ä┘ç╪▒┘à┘è
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

            // 1. ┘ü┘ä╪¬╪▒╪⌐ ╪¿╪º┘ä╪┤╪▒┘â╪⌐ ╪º┘ä╪¡╪º┘ä┘è╪⌐
            if (this.activeOpcoId) {
                list = list.filter(item => {
                    if (!item.company_assignments) return true;
                    return item.company_assignments.some(a => parseInt(a.opco_id) === parseInt(this.activeOpcoId));
                });
            }

            // 2. ╪¬╪╡┘ü┘è╪⌐ ╪Ñ╪╢╪º┘ü┘è╪⌐ ┘ä┘à┘ê╪»┘è┘ê┘ä ╪º┘ä┘à╪╖╪º╪╣┘à (╪º╪«╪¬┘è╪º╪▒┘è: ┘è┘à┘â┘å┘â ┘ü┘ä╪¬╪▒╪⌐ ╪º┘ä╪ú╪╡┘å╪º┘ü ┘ç┘å╪º ╪Ñ╪░╪º ╪▒╪║╪¿╪¬)
            if (this.view === 'restaurant_pos_module' && this.posTab === 'recipes') {
                // ╪│┘å╪╣╪▒╪╢ ┘â┘ä ╪º┘ä╪ú╪╡┘å╪º┘ü ╪¡╪º┘ä┘è╪º┘ï ┘ä╪¬┘à┘â┘è┘å ╪Ñ╪»╪º╪▒╪⌐ ╪º┘ä┘à┘â┘ê┘å╪º╪¬ ╪ú┘è╪╢╪º┘ï
            }

            // 2. ┘ü┘ä╪¬╪▒╪⌐ ╪¿┘å╪╡ ╪º┘ä╪¿╪¡╪½ (┘ä┘ê ╪º┘ä┘à╪│╪¬╪«╪»┘à ┘â╪¬╪¿ ╪¡╪º╪¼╪⌐)
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

        // ≡ƒÜÇ ╪¡╪│╪º╪¿╪º╪¬ ╪ú┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪» (╪º┘ä╪╢╪▒╪º╪ª╪¿ ┘ê╪º┘ä╪Ñ╪¼┘à╪º┘ä┘è╪º╪¬)
        poLineTotal() {
            if (!this.forms.po || !this.forms.po.lines) return 0;
            return this.forms.po.lines.reduce((sum, line) => sum + ((line.quantity || 0) * (line.unit_price || 0)), 0);
        },
        poTaxAmount() {
            if (!this.forms.po) return 0;
            const rate = (this.forms.po.tax_rate || 0) / 100;
            if (this.forms.po.is_tax_inclusive) {
                // ┘ä┘ê ╪º┘ä╪│╪╣╪▒ ╪┤╪º┘à┘ä ╪º┘ä╪╢╪▒┘è╪¿╪⌐╪î ╪¿┘å╪│╪¬╪«╪▒╪¼ ╪º┘ä╪╢╪▒┘è╪¿╪⌐ ┘à┘å ╪º┘ä╪Ñ╪¼┘à╪º┘ä┘è
                return this.poLineTotal - (this.poLineTotal / (1 + rate));
            } else {
                // ┘ä┘ê ╪║┘è╪▒ ╪┤╪º┘à┘ä╪î ╪¿┘å╪╢╪▒╪¿ ╪º┘ä╪Ñ╪¼┘à╪º┘ä┘è ┘ü┘è ╪º┘ä┘å╪│╪¿╪⌐
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
                return this.poLineTotal; // ╪º┘ä╪Ñ╪¼┘à╪º┘ä┘è ┘ç┘ê ┘å┘ü╪│ ╪º┘ä╪│╪╣╪▒ ╪º┘ä┘à┘â╪¬┘ê╪¿
            } else {
                return this.poLineTotal + this.poTaxAmount; // ╪º┘ä╪Ñ╪¼┘à╪º┘ä┘è + ╪º┘ä╪╢╪▒┘è╪¿╪⌐
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
                'dashboard': { ar: '┘ä┘ê╪¡╪⌐ ╪º┘ä╪¬╪¡┘â┘à', en: 'Dashboard' },
                'org_builder': { ar: '┘ç┘è┘â┘ä╪⌐ ╪º┘ä┘à┘å╪╕┘à╪⌐', en: 'Org Builder' },
                'inventory_module': { ar: 'RIMS (╪º┘ä┘à╪«╪▓┘ê┘å)', en: 'RIMS (Inventory)' },
                'procurement_module': { ar: 'RPMS (╪º┘ä┘à╪┤╪¬╪▒┘è╪º╪¬)', en: 'RPMS (Procurement)' },
                'sales_module': { ar: '╪Ñ╪»╪º╪▒╪⌐ ╪º┘ä┘à╪¿┘è╪╣╪º╪¬', en: 'Sales & CRM' },
                'accounting_module': { ar: '╪º┘ä┘à╪¡╪º╪│╪¿╪⌐ ┘ê╪º┘ä┘à╪º┘ä┘è╪⌐', en: 'Accounting' },
                'global_config': { ar: '╪Ñ╪╣╪»╪º╪»╪º╪¬ ╪º┘ä┘å╪╕╪º┘à', en: 'Global Settings' },
                'users': { ar: '╪Ñ╪»╪º╪▒╪⌐ ╪º┘ä┘à╪│╪¬╪«╪»┘à┘è┘å', en: 'User Management' },
                'item_master': { ar: '╪│╪¼┘ä ╪º┘ä╪ú╪╡┘å╪º┘ü', en: 'Item Master' },
                'vendors_list': { ar: '╪│╪¼┘ä ╪º┘ä┘à┘ê╪▒╪»┘è┘å', en: 'Vendors' },
                'vendor_ledger': { ar: '┘â╪┤┘ü ╪¡╪│╪º╪¿ ┘à┘ê╪▒╪»', en: 'Vendor Ledger' }
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
            // Γ£à Fix: Use displayMoves instead of inventoryMoves so top filters work on aggregation too
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
        // ╪Ñ╪╢╪º┘ü╪⌐ ┘à╪│╪¬┘à╪╣ ┘ä┘ä┘å┘é╪▒╪º╪¬ ╪º┘ä╪«╪º╪▒╪¼┘è╪⌐ ┘ä╪Ñ╪║┘ä╪º┘é ╪º┘ä┘é┘ê╪º╪ª┘à ╪º┘ä┘à┘å╪│╪»┘ä╪⌐
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
        this.checkActivePOSSession();
        
        // ≡ƒÜÇ KDS Timer & Polling
        setInterval(() => { this.kdsCurrentTime = new Date(); }, 1000);
        this.kdsInterval = setInterval(() => {
            if (this.view === 'restaurant_pos_module' && this.posTab === 'kitchen') {
                this.fetchKDSOrders();
            }
        }, 10000); // ┘â┘ä 10 ╪½┘ê╪º┘å┘è

        // Core Init
        this.checkAuth();
        this.startClock();
        this.fetchAll();
        this.fetchMaterialsList();
        this.fetchWMSStats();
    },

    methods: {
        addToCart(item) {
            const price = parseFloat(item.sales_price || item.standard_price || 0);
            const onHand = parseFloat(item.on_hand || 0);
            const hasNoBOM = !item.recipe_lines || item.recipe_lines.length === 0;

            const existing = this.posCart.find(i => i.id === item.id);
            if (existing) {
                if (hasNoBOM && existing.qty + 1 > onHand) {
                    this.showToast(this.isArabic ? `╪╣┘ü┘ê╪º┘ï╪î ╪º┘ä╪▒╪╡┘è╪» ╪º┘ä┘à╪¬╪º╪¡ ${onHand} ┘ü┘é╪╖` : `Sorry, only ${onHand} available in stock`, "error");
                    return;
                }
                existing.qty++;
            } else {
                if (hasNoBOM && onHand <= 0) {
                    this.showToast(this.isArabic ? "╪╣┘ü┘ê╪º┘ï╪î ╪º┘ä╪╡┘å┘ü ╪║┘è╪▒ ┘à╪¬┘ê┘ü╪▒ ┘ü┘è ╪º┘ä┘à╪«╪▓┘å" : "Sorry, item is out of stock", "error");
                    return;
                }
                this.posCart.push({
                    id: item.id,
                    name: item.name,
                    price: price,
                    tax_rate: item.tax_rate || 15,
                    qty: 1,
                    on_hand: onHand,
                    has_no_bom: hasNoBOM
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
            
            // ≡ƒÜÇ Stock Validation
            if (item.has_no_bom && newQty > item.on_hand) {
                this.showToast(this.isArabic ? `╪╣┘ü┘ê╪º┘ï╪î ╪ú┘é╪╡┘ë ┘â┘à┘è╪⌐ ┘à╪¬╪º╪¡╪⌐ ┘ç┘è ${item.on_hand}` : `Max available stock is ${item.on_hand}`, "error");
                return;
            }

            this.posNumpadBuffer = currentBuffer;
            if (newQty > 0) {
                item.qty = newQty;
            } else if (this.posNumpadBuffer === '') {
                item.qty = 1;
            }
        },

        selectCartItem(index) {
            this.posSelectedCartIndex = index;
            this.posNumpadBuffer = '';
            this.posShowNumpad = true;
        },
        updateCartQty(idx, delta) {
            const item = this.posCart[idx];
            
            // ≡ƒÜÇ Stock Validation for increment
            if (delta > 0 && item.has_no_bom && item.qty + delta > item.on_hand) {
                this.showToast(this.isArabic ? `╪╣┘ü┘ê╪º┘ï╪î ╪º┘ä╪▒╪╡┘è╪» ╪º┘ä┘à╪¬╪º╪¡ ${item.on_hand} ┘ü┘é╪╖` : `Sorry, only ${item.on_hand} available in stock`, "error");
                return;
            }

            item.qty += delta;
            if (item.qty <= 0) {
                this.posCart.splice(idx, 1);
                if (this.posSelectedCartIndex === idx) this.posSelectedCartIndex = null;
            }
        },
        async checkoutOrder() {
            if (!this.activePOSSession) {
                this.showToast(this.isArabic ? "╪¿╪▒╪¼╪º╪í ┘ü╪¬╪¡ ┘ê╪▒╪»┘è╪⌐ ╪ú┘ê┘ä╪º┘ï!" : "Please start a session first!", "error");
                return;
            }
            if (this.posCart.length === 0) {
                this.showToast(this.isArabic ? "╪º┘ä╪╣╪▒╪¿╪⌐ ┘ü╪º╪▒╪║╪⌐!" : "Cart is empty!", "error");
                return;
            }
            
            // ≡ƒÜÇ Prompt for Payment Method during Checkout
            const { value: method } = await Swal.fire({
                title: this.isArabic ? '╪º╪«╪¬╪▒ ╪╖╪▒┘è┘é╪⌐ ╪º┘ä╪»┘ü╪╣' : 'Select Payment Method',
                input: 'radio',
                inputOptions: {
                    'cash': this.isArabic ? '┘å┘é╪»╪º┘ï (Cash)' : 'Cash',
                    'instapay': this.isArabic ? '╪Ñ┘ä┘â╪¬╪▒┘ê┘å┘è (InstaPay)' : 'InstaPay',
                    'credit': this.isArabic ? '╪ó╪¼┘ä (Credit)' : 'Credit'
                },
                inputValue: this.posPaymentMethod,
                showCancelButton: true,
                confirmButtonText: this.isArabic ? '╪¬╪ú┘â┘è╪» ┘ê╪»┘ü╪╣' : 'Confirm & Pay'
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
                            subtotal: parseFloat((i.price * i.qty).toFixed(2))
                        }))
                    })
                });

                if (res.ok) {
                    const order = await res.json();
                    
                    // 2. Process Payment & Deduct Inventory (BOM Deduction)
                    const payRes = await fetch(`/api/pos/orders/${order.id}/process_payment/`, {
                        method: 'POST',
                        headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                    });

                    if (payRes.ok) {
                        const payData = await payRes.json();
                        this.showToast(this.isArabic ? "╪¬┘à ╪¬╪ú┘â┘è╪» ╪º┘ä╪╖┘ä╪¿ ┘ê╪«╪╡┘à ╪º┘ä┘à┘â┘ê┘å╪º╪¬ ╪¿┘å╪¼╪º╪¡!" : "Order Confirmed & Ingredients Deducted!", "success");
                        
                        // ≡ƒû¿∩╕Å ╪╖╪¿╪º╪╣╪⌐ ╪º┘ä╪Ñ┘è╪╡╪º┘ä ╪¬┘ä┘é╪º╪ª┘è╪º┘ï
                        this.printReceipt(order, this.posCart);
                        
                        this.posCart = [];
                        this.refreshAllData(); // ≡ƒÜÇ ╪¬╪¡╪»┘è╪½ ╪┤╪º┘à┘ä ┘ä┘â┘ä ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ┘ê╪º┘ä╪¬┘é╪º╪▒┘è╪▒ ┘ê╪¡╪▒┘â╪º╪¬ ╪º┘ä┘à╪«╪▓┘å ┘ü┘ê╪▒╪º┘ï
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
                <div style="display:flex; justify-content:space-between; margin-bottom:8px; border-bottom: 1px dotted #eee; padding-bottom: 4px;">
                    <div style="flex:1">
                        <div style="font-weight:bold">${i.name || i.material_name}</div>
                        <div style="font-size:10px; color:#666">Qty: ${i.qty} x ${Number(i.price || i.unit_price).toFixed(2)}</div>
                    </div>
                    <div style="font-weight:bold">${((i.price || i.unit_price) * i.qty).toFixed(2)}</div>
                </div>
            `).join('');

            const total = Number(order.total_amount || this.cartTotal);
            const vat = Number(this.cartTax);
            const subtotal = total - vat;
            const brandColor = this.activeOpco && this.activeOpco.brand_color ? this.activeOpco.brand_color : '#1e293b';
            const currency = this.activeOpco ? this.activeOpco.currency : 'EGP';
            const orderRef = order.order_ref || 'DRAFT-POS';
            
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
                            ${this.isArabic ? '╪º┘ä┘å┘ê╪╣' : 'Type'}: ${order.order_type} | 
                            ${this.isArabic ? '╪º┘ä╪»┘ü╪╣' : 'Pay'}: ${order.payment_method}
                        </div>
                    </div>

                    <div class="items">
                        ${cart.map(i => `
                            <div class="item-row">
                                <div class="item-info">
                                    <div class="item-name">${i.name || i.material_name}</div>
                                    <div class="item-details">${i.qty} x ${Number(i.price || i.unit_price).toFixed(2)}</div>
                                </div>
                                <div class="item-price">${((i.price || i.unit_price) * i.qty).toFixed(2)}</div>
                            </div>
                        `).join('')}
                    </div>

                    <div class="summary">
                        <div class="summary-line">
                            <span>${this.isArabic ? '╪º┘ä┘à╪¼┘à┘ê╪╣ ╪º┘ä┘ü╪▒╪╣┘è' : 'Subtotal'}</span>
                            <span>${subtotal.toFixed(2)}</span>
                        </div>
                        <div class="summary-line">
                            <span>${this.isArabic ? '╪º┘ä╪╢╪▒┘è╪¿╪⌐ (15%)' : 'Tax (15%)'}</span>
                            <span>${vat.toFixed(2)}</span>
                        </div>
                        <div class="total-line">
                            <span>${this.isArabic ? '╪º┘ä╪Ñ╪¼┘à╪º┘ä┘è' : 'TOTAL'}</span>
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
                        <p>${this.isArabic ? '╪┤┘â╪▒╪º┘ï ┘ä╪▓┘è╪º╪▒╪¬┘â┘à ┘ê┘å╪¬┘à┘å┘ë ╪▒╪ñ┘è╪¬┘â┘à ┘é╪▒┘è╪¿╪º┘ï' : 'THANK YOU FOR YOUR VISIT! SEE YOU AGAIN.'}</p>
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
                        title: this.isArabic ? '╪Ñ╪║┘ä╪º┘é ╪º┘ä┘ê╪▒╪»┘è╪⌐ ┘ê╪¬╪╡┘ü┘è╪⌐ ╪º┘ä╪¡╪│╪º╪¿' : 'Close Shift & Settlement',
                        html: `
                            <div style="text-align:right; font-size: 14px;" dir="rtl">
                                <p>╪▒╪╡┘è╪» ╪º┘ä╪¿╪»╪º┘è╪⌐: <b>${Number(summary.opening_balance).toFixed(2)}</b></p>
                                <div style="margin: 10px 0; padding: 10px; bg-slate-50; border-radius: 10px; border: 1px solid #eee;">
                                    <p style="color:#059669">┘à╪¿┘è╪╣╪º╪¬ ┘â╪º╪┤ (+): <b>${Number(summary.cash_sales).toFixed(2)}</b></p>
                                    <p style="color:#6366f1">┘à╪¿┘è╪╣╪º╪¬ ╪Ñ┘ä┘â╪¬╪▒┘ê┘å┘è╪⌐ (InstaPay): <b>${Number(summary.instapay_sales).toFixed(2)}</b></p>
                                    <p style="color:#f43f5e">┘à╪¿┘è╪╣╪º╪¬ ╪ó╪¼┘ä╪⌐ (Credit): <b>${Number(summary.credit_sales).toFixed(2)}</b></p>
                                </div>
                                <p>╪Ñ╪¼┘à╪º┘ä┘è ╪º┘ä┘à╪╡╪º╪▒┘è┘ü (-): <b style="color:red">${Number(summary.total_expenses).toFixed(2)}</b></p>
                                <hr>
                                <p style="font-size:18px">╪º┘ä╪▒╪╡┘è╪» ╪º┘ä┘â╪º╪┤ ╪º┘ä┘à╪¬┘ê┘é╪╣: <b style="color:#0f172a">${Number(summary.expected_cash).toFixed(2)}</b></p>
                                <p style="font-size:10px; color:#666">*(┘ä╪º ┘è╪┤┘à┘ä ╪º┘ä┘ü┘è╪▓╪º ╪ú┘ê ╪º┘ä╪ú┘ê┘å┘ä╪º┘è┘å)*</p>
                                <br>
                                <label>╪ú╪»╪«┘ä ╪º┘ä┘à╪¿┘ä╪║ ╪º┘ä┘ü╪╣┘ä┘è ╪º┘ä┘à┘ê╪¼┘ê╪» ┘ü┘è ╪º┘ä╪»╪▒╪¼ ╪º┘ä╪ó┘å:</label>
                            </div>
                        `,
                        input: 'number',
                        inputAttributes: { step: '0.01' },
                        inputValue: summary.expected_cash,
                        showCancelButton: true,
                        confirmButtonText: this.isArabic ? '╪¬╪ú┘â┘è╪» ╪º┘ä╪Ñ╪║┘ä╪º┘é' : 'Confirm Close'
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
                        this.showToast(this.isArabic ? "╪¬┘à ╪Ñ╪║┘ä╪º┘é ╪º┘ä┘ê╪▒╪»┘è╪⌐" : "Shift closed");
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
                this.showToast(this.isArabic ? "╪¿╪▒╪¼╪º╪í ┘ü╪¬╪¡ ┘ê╪▒╪»┘è╪⌐ ╪ú┘ê┘ä╪º┘ï!" : "Please start a session first!", "error");
                return;
            }

            const { value: formValues } = await Swal.fire({
                title: this.isArabic ? '╪╡╪▒┘ü ┘å┘é╪»┘è╪⌐ / ┘à╪╡╪▒┘ê┘ü╪º╪¬' : 'Cash Out / Expense',
                html: `
                    <div style="text-align:right" dir="rtl">
                        <label style="font-weight:bold; font-size:12px; color:#666">╪º┘ä┘à╪¿┘ä╪║ ╪º┘ä┘à╪╖┘ä┘ê╪¿ ╪╡╪▒┘ü┘ç</label>
                        <input id="swal-amount" class="swal2-input" type="number" step="0.01" placeholder="0.00">
                        <label style="font-weight:bold; font-size:12px; color:#666; margin-top:10px; display:block">╪º┘ä╪│╪¿╪¿ / ╪º┘ä╪¿┘è╪º┘å</label>
                        <input id="swal-reason" class="swal2-input" type="text" placeholder="┘à╪½┘ä╪º┘ï: ╪┤╪▒╪º╪í ╪«╪╢╪▒┘ê╪º╪¬╪î ╪╣╪¼╪▓ ╪╣┘ç╪»┘ç...">
                    </div>
                `,
                focusConfirm: false,
                showCancelButton: true,
                confirmButtonText: this.isArabic ? '╪¬╪ú┘â┘è╪» ┘ê╪╡╪▒┘ü' : 'Confirm & Cash Out',
                cancelButtonText: this.isArabic ? '╪Ñ┘ä╪║╪º╪í' : 'Cancel',
                preConfirm: () => {
                    const amount = document.getElementById('swal-amount').value;
                    const reason = document.getElementById('swal-reason').value;
                    if (!amount || amount <= 0) {
                        Swal.showValidationMessage(this.isArabic ? '╪¿╪▒╪¼╪º╪í ╪Ñ╪»╪«╪º┘ä ┘à╪¿┘ä╪║ ╪╡╪¡┘è╪¡' : 'Please enter a valid amount');
                        return false;
                    }
                    if (!reason) {
                        Swal.showValidationMessage(this.isArabic ? '╪¿╪▒╪¼╪º╪í ╪Ñ╪»╪«╪º┘ä ╪│╪¿╪¿ ╪º┘ä╪╡╪▒┘ü' : 'Please enter a reason');
                        return false;
                    }
                    return { amount, reason };
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
                        type: 'OUT',
                        amount: formValues.amount,
                        reason: formValues.reason
                    })
                });
                
                if (res.ok) {
                    this.showToast(this.isArabic ? "╪¬┘à ╪¬╪│╪¼┘è┘ä ╪º┘ä╪╣┘à┘ä┘è╪⌐ ┘ê╪╖╪¿╪º╪╣╪⌐ ╪º┘ä╪Ñ┘è╪╡╪º┘ä" : "Transaction recorded & Receipt printed", "success");
                    
                    // ≡ƒÜÇ ╪╖╪¿╪º╪╣╪⌐ ╪Ñ┘è╪╡╪º┘ä ╪º┘ä┘à╪╡╪▒┘ê┘ü╪º╪¬
                    this.printExpenseReceipt({
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
                    <title>Expense Voucher</title>
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
                        <div class="title">${this.isArabic ? '╪Ñ┘è╪╡╪º┘ä ╪╡╪▒┘ü ┘å┘é╪»┘è╪⌐' : 'CASH OUT VOUCHER'}</div>
                        <div>${companyName}</div>
                    </div>
                    
                    <div class="detail-row">
                        <span>Date / ╪º┘ä┘ê┘é╪¬:</span>
                        <span>${date}</span>
                    </div>
                    <div class="detail-row">
                        <span>Session ID / ╪º┘ä┘ê╪▒╪»┘è╪⌐:</span>
                        <span>#${data.session_id}</span>
                    </div>
                    <div class="detail-row">
                        <span>Cashier / ╪º┘ä┘â╪º╪┤┘è╪▒:</span>
                        <span>${data.cashier}</span>
                    </div>
                    
                    <div class="divider" style="border-top:1px dashed #000; margin:15px 0;"></div>
                    
                    <div style="text-align:left; margin-bottom:10px; font-weight:bold;">Reason / ╪º┘ä╪¿┘è╪º┘å:</div>
                    <div style="text-align:left; font-size:16px; margin-bottom:20px; padding:10px; background:#f9f9f9;">${data.reason}</div>
                    
                    <div class="amount-box">
                        ${Number(data.amount).toFixed(2)} ${currency}
                    </div>
                    
                    <div class="signature">
                        <div>
                            <div class="sig-line">Cashier</div>
                        </div>
                        <div>
                            <div class="sig-line">Recipient</div>
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
                title: this.isArabic ? '╪º╪«╪¬╪▒ ╪º┘ä┘ü╪¬╪▒╪⌐ ╪º┘ä╪▓┘à┘å┘è╪⌐' : 'Select Date Range',
                html: `
                    <div style="text-align:right" dir="rtl">
                        <label>┘à┘å ╪¬╪º╪▒┘è╪«:</label>
                        <input id="swal-from" class="swal2-input" type="date" value="${this.posDashboardFilters.from}">
                        <label>╪Ñ┘ä┘ë ╪¬╪º╪▒┘è╪«:</label>
                        <input id="swal-to" class="swal2-input" type="date" value="${this.posDashboardFilters.to}">
                    </div>
                `,
                focusConfirm: false,
                showCancelButton: true,
                confirmButtonText: this.isArabic ? '╪¬╪╖╪¿┘è┘é ╪º┘ä┘ü┘ä╪¬╪▒' : 'Apply Filter',
                cancelButtonText: this.isArabic ? '╪Ñ┘ä╪║╪º╪í' : 'Cancel',
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
                // ╪¼┘ä╪¿ ╪º┘ä╪╖┘ä╪¿╪º╪¬ ┘ê╪º┘ä┘à╪╡╪▒┘ê┘ü╪º╪¬ ┘ä┘å┘ü╪│ ╪º┘ä╪¼┘ä╪│╪⌐
                const [ordersRes, transRes] = await Promise.all([
                    fetch(`/api/pos/orders/?opco=${this.activeOpcoId}&session=${session.id}`),
                    fetch(`/api/pos/orders/cash_transactions/?opco=${this.activeOpcoId}&session=${session.id}`)
                ]);

                let orders = [];
                let trans = [];

                if (ordersRes.ok) orders = await ordersRes.json();
                if (transRes.ok) trans = await transRes.json();

                // ╪»┘à╪¼ ╪º┘ä┘é╪º╪ª┘à╪¬┘è┘å ┘à╪╣ ╪¬┘à┘è┘è╪▓ ╪º┘ä┘å┘ê╪╣
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
                title: this.isArabic ? '┘ç┘ä ╪ú┘å╪¬ ┘à╪¬╪ú┘â╪»╪ƒ' : 'Are you sure?',
                text: this.isArabic ? `╪│┘è╪¬┘à ╪Ñ╪▒╪¼╪º╪╣ ┘à╪¿┘ä╪║ ${order.total_amount} ┘ê╪«╪╡┘à┘ç ┘à┘å ╪º┘ä╪»╪▒╪¼` : `Amount of ${order.total_amount} will be refunded and deducted from drawer`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? '╪¬╪ú┘â┘è╪» ╪º┘ä╪Ñ╪▒╪¼╪º╪╣' : 'Confirm Refund'
            });

            if (!isConfirmed) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/pos/orders/${order.id}/refund_order/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });
                if (res.ok) {
                    this.showToast(this.isArabic ? "╪¬┘à ╪Ñ╪▒╪¼╪º╪╣ ╪º┘ä╪╖┘ä╪¿ ╪¿┘å╪¼╪º╪¡" : "Order refunded successfully", "success");
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
                const res = await fetch('/api/pos/orders/?active_session=true&opco=' + this.activeOpcoId);
                // I'll need to update the ViewSet to handle this query param
                if (res.ok) {
                    const data = await res.json();
                    if (data.length > 0) {
                        this.activePOSSession = data[0];
                    }
                }
            } catch (e) { console.error("Session Check Error", e); }
        },

        async startPOSSession() {
            let lastBalance = 0;
            try {
                const res = await fetch(`/api/pos/orders/last_session_balance/?opco=${this.activeOpcoId}`);
                if (res.ok) {
                    const data = await res.json();
                    lastBalance = Number(data.last_balance || 0);
                }
            } catch (e) { console.error("Balance fetch error", e); }

            const { value: openingBalance } = await Swal.fire({
                title: this.isArabic ? '┘ü╪¬╪¡ ┘ê╪▒╪»┘è╪⌐ ╪¼╪»┘è╪»╪⌐' : 'Open New Shift',
                input: 'number',
                inputAttributes: { step: '0.01' },
                inputLabel: this.isArabic ? '╪▒╪╡┘è╪» ╪¿╪»╪º┘è╪⌐ ╪º┘ä╪»╪▒╪¼ (Cash Start)' : 'Opening Cash Balance',
                inputValue: lastBalance,
                showCancelButton: true,
                confirmButtonText: this.isArabic ? '╪¿╪»╪í ╪º┘ä┘ê╪▒╪»┘è╪⌐' : 'Start Shift',
                footer: `<div style="text-align:center">${this.isArabic ? '╪▒╪╡┘è╪» ╪Ñ╪║┘ä╪º┘é ╪ó╪«╪▒ ┘ê╪▒╪»┘è╪⌐: ' : 'Last shift closing balance: '} <b>${lastBalance}</b></div>`
            });

            if (openingBalance === undefined || openingBalance === null) return;

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
                        cashier_name: this.user.name || 'Admin',
                        opening_balance: openingBalance
                    })
                });
                
                if (res.ok) {
                    this.activePOSSession = await res.json();
                    this.showToast(this.isArabic ? "╪¬┘à ┘ü╪¬╪¡ ╪º┘ä┘ê╪▒╪»┘è╪⌐ ╪¿┘å╪¼╪º╪¡" : "Session started successfully", "success");
                }
            } catch (e) {
                this.showToast("Error starting session", "error");
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
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪¬╪¡╪╢┘è╪▒ ╪º┘ä╪╖╪¿╪º╪╣╪⌐..." : "Preparing Print...", "info");
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
            // ≡ƒôª 1. ╪¡╪│╪º╪¿╪º╪¬ ╪º┘ä┘à╪«╪▓┘ê┘å (Inventory)
            this.kpis.inventory.total_items = (this.materials_list || []).length;
            this.kpis.inventory.stock_qty = (this.inventoryList || []).reduce((acc, item) => acc + (item.quantity || 0), 0);
            
            this.kpis.inventory.critical_items = (this.inventoryList || []).filter(item => {
                const material = (this.materials_list || []).find(m => m.id === item.material_id);
                return material && (item.quantity < (material.reorder_level || 5));
            }).length;
            
            this.kpis.inventory.dead_stock = (this.inventoryList || []).filter(item => item.quantity > 500).length;

            // ≡ƒÆ░ 2. ╪¡╪│╪º╪¿╪º╪¬ ╪º┘ä┘à╪¿┘è╪╣╪º╪¬ (Sales)
            const soData = this.salesOrders || [];
            this.kpis.sales.total = soData.reduce((acc, so) => acc + (parseFloat(so.grand_total || so.total_amount) || 0), 0);
            this.kpis.sales.delivered = soData.filter(so => so.status === 'DELIVERED').reduce((acc, so) => acc + (parseFloat(so.grand_total) || 0), 0);
            this.kpis.sales.remaining_delivery = this.kpis.sales.total - this.kpis.sales.delivered;
            
            const invData = this.salesInvoices || [];
            this.kpis.sales.invoiced = invData.reduce((acc, inv) => acc + (parseFloat(inv.total_amount) || 0), 0);
            this.kpis.sales.remaining_invoice = this.kpis.sales.total - this.kpis.sales.invoiced;

            // ≡ƒ¢Æ 3. ╪¡╪│╪º╪¿╪º╪¬ ╪º┘ä┘à╪┤╪¬╪▒┘è╪º╪¬ (Procurement)
            const poData = this.purchase_orders || [];
            this.kpis.procurement.total = poData.reduce((acc, po) => acc + (parseFloat(po.total_amount) || 0), 0);
            this.kpis.procurement.received = poData.filter(po => po.status === 'RECEIVED').reduce((acc, po) => acc + (parseFloat(po.total_amount) || 0), 0);
            this.kpis.procurement.invoiced = this.kpis.procurement.received * 0.9; 
            this.kpis.procurement.paid = this.kpis.procurement.invoiced * 0.8;

            // ≡ƒÅª 4. ╪¡╪│╪º╪¿╪º╪¬ ╪º┘ä┘à╪º┘ä┘è╪⌐ (Finance)
            this.kpis.finance.invoices = this.kpis.sales.invoiced;
            this.kpis.finance.collected = invData.reduce((acc, inv) => acc + (parseFloat(inv.paid_amount || 0)), 0);
            this.kpis.finance.remaining = this.kpis.finance.invoices - this.kpis.finance.collected;

            // ≡ƒæÑ ╪╣╪»╪º╪»╪º╪¬ ╪Ñ╪╢╪º┘ü┘è╪⌐
            this.kpis.vendors = (this.vendors || []).length;
            this.kpis.customers_count = (this.customers || []).length;
        },
        ...utils.methods,
        ...itemMasterModule.methods,

        // ╪»╪º╪«┘ä methods ┘ü┘è main.js
        // ╪º╪¿╪¡╪½ ╪╣┘å generateItemReport ┘ê╪º╪│╪¬╪¿╪»┘ä┘ç╪º ╪¿┘ç╪░╪º ╪º┘ä┘â┘ê╪»
        // ╪»╪º╪«┘ä ┘é╪│┘à methods ┘ü┘è ┘à┘ä┘ü main.js
        startOperation(type) {
            // 1. ╪¬╪¡╪»┘è╪» ╪º┘ä╪¬╪º╪¿╪⌐ ╪º┘ä┘å╪┤╪╖╪⌐ ┘ü┘è ╪º┘ä┘à┘ê╪»╪º┘ä
            this.activeOperation = type;

            // 2. ┘à╪╡┘ü┘ê┘ü╪⌐ ╪º┘ä╪╣┘à┘ä┘è╪º╪¬ ╪º┘ä╪¬┘è ╪¬╪╣╪¬╪¿╪▒ "╪Ñ╪╢╪º┘ü╪⌐" (Incoming)
            const incomingOps = ['po_receipt', 'mrp_receipt', 'so_return', 'incoming_transfer'];

            // 3. ╪¬┘ç┘è╪ª╪⌐ ┘â╪º╪ª┘å ╪º┘ä┘Ç stock_entry ┘ê╪¬╪¡╪»┘è╪» ┘å┘ê╪╣ ╪º┘ä╪¡╪▒┘â╪⌐ ┘ü┘ê╪▒╪º┘ï
            if (!this.forms.stock_entry) {
                this.forms.stock_entry = { items: [], po_id: '' };
            }

            // ┘ç┘å╪º ╪º┘ä╪│╪▒: ┘ä┘ê ╪º┘ä╪╣┘à┘ä┘è╪⌐ ┘ü┘è ┘é╪º╪ª┘à╪⌐ ╪º┘ä╪Ñ╪╢╪º┘ü╪⌐╪î ╪º┘ä┘å┘ê╪╣ IN╪î ╪║┘è╪▒ ┘â╪»╪⌐ OUT
            this.forms.stock_entry.move_type = incomingOps.includes(type) ? 'IN' : 'OUT';

            // ╪¬╪╡┘ü┘è╪▒ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ┘ä┘ä╪¿╪»╪í ┘ü┘è ╪╣┘à┘ä┘è╪⌐ ╪¼╪»┘è╪»╪⌐
            this.forms.stock_entry.items = [{ material_id: '', quantity: 1, unit_cost: 0, sales_price: 0 }];
            this.forms.stock_entry.po_id = '';
            this.forms.stock_entry.payment_method = 'CASH';
            this.forms.stock_entry.tax_rate = 15;

            // ┘ä┘ê ╪º┘ä╪╣┘à┘ä┘è╪⌐ ╪┤╪▒╪º╪í╪î ┘å╪¼┘ç╪▓ ╪ú┘ê╪º┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪»
            if (type === 'po_receipt') {
                this.fetchPendingPOs();
            }

            // ┘ä┘ê ╪º┘ä╪╣┘à┘ä┘è╪⌐ ┘à╪¿┘è╪╣╪º╪¬╪î ┘å╪¼┘ç╪▓ ╪ú┘ê╪º┘à╪▒ ╪º┘ä╪¿┘è╪╣ ╪º┘ä┘é╪º╪¿┘ä╪⌐ ┘ä┘ä╪╡╪▒┘ü
            if (type === 'so_delivery') {
                this.fetchSalesOrders();
            }
            
            this.showModal = true;
            this.modalType = 'stock_entry';
        },

        async generateItemReport() {
            // 1. ╪º┘ä╪¬╪¡┘é┘é ┘à┘å ╪º╪«╪¬┘è╪º╪▒ ╪╡┘å┘ü ╪ú┘ê┘ä╪º┘ï
            if (!this.reportFilters.material_id) {
                alert(this.isArabic ? '╪¿╪▒╪¼╪º╪í ╪º╪«╪¬┘è╪º╪▒ ╪º┘ä╪╡┘å┘ü ╪ú┘ê┘ä╪º┘ï' : 'Please select a material first');
                return;
            }

            this.loading = true; // ╪¬╪┤╪║┘è┘ä ╪╣┘ä╪º┘à╪⌐ ╪º┘ä╪¬╪¡┘à┘è┘ä (Spinner)

            try {
                // 2. ╪¬╪¼┘ç┘è╪▓ ╪▒┘ê╪º╪¿╪╖ ╪º┘ä╪¿╪¡╪½ (Query Parameters)
                const params = new URLSearchParams({
                    material_id: this.reportFilters.material_id,
                    date_from: this.reportFilters.date_from || '',
                    date_to: this.reportFilters.date_to || '',
                    location_id: this.reportFilters.location_id || ''
                });

                // 3. ╪╖┘ä╪¿ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ┘à┘å ╪º┘ä╪│┘è╪▒┘ü╪▒ (╪¬╪ú┘â╪» ╪ú┘å ╪º┘ä╪▒╪º╪¿╪╖ ┘à╪╖╪º╪¿┘é ┘ä┘Ç urls.py)
                const response = await fetch(`/api/wms/moves/?${params.toString()}`);

                if (!response.ok) throw new Error('Network response was not ok');

                const data = await response.json();

                // 4. ┘ê╪╢╪╣ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ┘ü┘è ╪º┘ä┘à╪╡┘ü┘ê┘ü╪⌐ ┘ä╪╣╪▒╪╢┘ç╪º ┘ü┘è ╪º┘ä╪¼╪»┘ê┘ä
                this.inventoryMoves = data;

            } catch (error) {
                console.error("Error generating report:", error);
                alert(this.isArabic ? '╪¡╪»╪½ ╪«╪╖╪ú ╪ú╪½┘å╪º╪í ╪¼┘ä╪¿ ╪º┘ä╪¿┘è╪º┘å╪º╪¬' : 'Error fetching report data');
            } finally {
                this.loading = false; // ╪Ñ┘è┘é╪º┘ü ╪╣┘ä╪º┘à╪⌐ ╪º┘ä╪¬╪¡┘à┘è┘ä
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
                    // ≡ƒÜÇ ╪º┘ä╪¬╪╣╪»┘è┘ä ┘ç┘å╪º: ╪Ñ╪╢╪º┘ü╪⌐ showDetails ┘ä┘â┘ä ╪ú┘à╪▒ ╪¬┘ê╪▒┘è╪» ╪╣╪┤╪º┘å ╪º┘ä┘Ç Expand ┘è╪┤╪¬╪║┘ä
                    const list = Array.isArray(data) ? data : (data.results || []);
                    this.purchase_orders = list.map(po => ({
                        ...po,
                        showDetails: false // ╪º┘ä╪¡╪º┘ä╪⌐ ╪º┘ä╪º┘ü╪¬╪▒╪º╪╢┘è╪⌐ ┘ä┘ä╪¬┘ü╪º╪╡┘è┘ä ╪Ñ┘å┘ç╪º ┘à┘é┘ü┘ê┘ä╪⌐
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
                    // ≡ƒÜÇ ╪Ñ╪╢╪º┘ü╪⌐ ╪º┘ä╪«╪º╪╡┘è╪⌐ ┘ç┘å╪º ╪╢╪▒┘ê╪▒┘è ╪¼╪»╪º┘ï
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
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪Ñ╪╡╪»╪º╪▒ ╪º┘ä┘ü╪º╪¬┘ê╪▒╪⌐..." : "Generating invoice...", "success");
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
                    this.showToast(this.isArabic ? "╪¬┘à ╪Ñ╪╡╪»╪º╪▒ ╪º┘ä┘ü╪º╪¬┘ê╪▒╪⌐ ╪¿┘å╪¼╪º╪¡" : "Invoice generated successfully", "success");
                    await this.fetchSalesOrders();
                    await this.fetchSalesInvoices();
                    await this.fetchCustomers(); // ┘ä╪¬╪¡╪»┘è╪½ ╪ú╪▒╪╡╪»╪⌐ ╪º┘ä╪╣┘à┘ä╪º╪í ┘ü┘ê╪▒╪º┘ï
                } else {
                    this.showToast(data.error || (this.isArabic ? "┘ü╪┤┘ä ╪Ñ╪╡╪»╪º╪▒ ╪º┘ä┘ü╪º╪¬┘ê╪▒╪⌐" : "Failed to generate invoice"), "error");
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
                this.showToast(this.isArabic ? "╪«╪╖╪ú ┘ü┘è ╪¼┘ä╪¿ ┘â╪┤┘ü ╪º┘ä╪¡╪│╪º╪¿" : "Error fetching ledger", 'error');
            } finally {
                this.loading = false;
            }
        },

        calculatePOTotal(po) {
            if (!po.lines || po.lines.length === 0) return '0.00';
            const total = po.lines.reduce((sum, line) => sum + (line.quantity * line.unit_price), 0);
            return total.toFixed(2);
        },

        // ≡ƒÜÇ ╪Ñ╪╢╪º┘ü╪⌐ ╪»╪º┘ä╪⌐ ╪º┘ä╪╖╪¿╪º╪╣╪⌐ (Print)
        printPO(poId) {
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪¬╪¡╪╢┘è╪▒ ┘à┘ä┘ü ╪º┘ä╪╖╪¿╪º╪╣╪⌐..." : "Preparing document...", "success");
            // ╪º┘ä╪▒╪º╪¿╪╖ ╪»┘ç ╪º┘ä┘à┘ü╪▒┘ê╪╢ ┘è┘ü╪¬╪¡ ╪╡┘ü╪¡╪⌐ ╪º┘ä┘Ç PDF ╪º┘ä┘ä┘è ╪¼╪º┘å╪║┘ê ╪¿┘è╪╣┘à┘ä┘ç╪º
            window.open(`/print/po/${poId}/`, '_blank');
        },

        printSO(id) {
            window.open(`/print/so/${id}/`, '_blank');
        },

        printGRN(receiptId) {
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪¬╪¼┘ç┘è╪▓ ╪Ñ╪░┘å ╪º┘ä╪º╪│╪¬┘ä╪º┘à ┘ä┘ä╪╖╪¿╪º╪╣╪⌐..." : "Preparing GRN document...", "success");
            window.open(`/print/grn/${receiptId}/`, '_blank');
        },

        printDelivery(deliveryId) {
            if (!deliveryId || deliveryId === 'undefined') {
                this.showToast(this.isArabic ? "╪«╪╖╪ú: ╪▒┘é┘à ╪º┘ä╪Ñ╪░┘å ╪║┘è╪▒ ┘à┘ê╪¼┘ê╪»" : "Error: Delivery ID is missing", 'error');
                return;
            }
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪¬╪¼┘ç┘è╪▓ ╪Ñ╪░┘å ╪º┘ä╪╡╪▒┘ü ┘ä┘ä╪╖╪¿╪º╪╣╪⌐..." : "Preparing Delivery Note...", "success");
            window.open(`/print/delivery/${deliveryId}/`, '_blank');
        },

        // ≡ƒÜÇ 1. ╪º┘ä╪»╪º┘ä╪⌐ ╪º┘ä┘ä┘è ┘â╪º┘å╪¬ ┘à┘ü┘é┘ê╪»╪⌐ ┘ê╪╣╪º┘à┘ä╪⌐ ╪º┘ä╪Ñ┘è╪▒┘ê╪▒ (╪▒╪¿╪╖ ╪º┘ä╪º┘å╪¬╪▒)
        processBarcodeManual() {
            if (!this.barcodeQuery) return;
            this.processScannedBarcode(this.barcodeQuery.trim());
        },

        // ≡ƒÜÇ 2. ╪»╪º┘ä╪⌐ ╪¬╪┤╪║┘è┘ä ╪º┘ä┘â╪º┘à┘è╪▒╪º (╪º┘ä┘å╪│╪«╪⌐ ╪º┘ä╪░┘â┘è╪⌐ ┘ä┘Ç EAN-13)
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

        // ≡ƒÜÇ 3. ╪º┘ä╪»╪º┘ä╪⌐ ╪º┘ä╪░┘â┘è╪⌐ ┘ä┘ä╪¿╪¡╪½ ┘ü┘è ┘é╪º╪╣╪»╪⌐ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪½┘à ╪ú┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪»
        processScannedBarcode(barcode) {
            if (!this.forms.stock_entry.items || this.forms.stock_entry.items.length === 0) {
                this.showToast(this.isArabic ? "╪¿╪▒╪¼╪º╪í ╪º╪«╪¬┘è╪º╪▒ ╪ú┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪» ╪ú┘ê┘ä╪º┘ï" : "Select PO first", 'error');
                if (this.scannerInstance && this.isScanning) this.scannerInstance.resume();
                return;
            }

            const matchedMaterial = this.materials_list.find(
                m => (m.barcode && m.barcode.toString() === barcode.toString()) ||
                    (m.sku && m.sku.toLowerCase() === barcode.toLowerCase()) ||
                    (m.id && m.id.toString() === barcode.toString())
            );

            if (!matchedMaterial) {
                this.showToast(this.isArabic ? `╪º┘ä╪¿╪º╪▒┘â┘ê╪» (${barcode}) ╪║┘è╪▒ ┘à╪│╪¼┘ä ┘ü┘è ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪ú╪╡┘å╪º┘ü!` : `Barcode not registered!`, 'error');
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
                this.showToast(this.isArabic ? `╪º┘ä╪╡┘å┘ü (${matchedMaterial.name}) ╪║┘è╪▒ ┘à╪╖┘ä┘ê╪¿ ┘ü┘è ╪ú┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪» ╪º┘ä╪¡╪º┘ä┘è!` : `Item not in this PO!`, 'error');
                this.barcodeQuery = '';
                if (this.scannerInstance && this.isScanning) {
                    setTimeout(() => this.scannerInstance.resume(), 1500);
                }
            }
        },

        // ≡ƒÜÇ 4. ╪¬╪ú┘â┘è╪» ╪º┘ä┘â┘à┘è╪⌐
        confirmScannedQty() {
            const itemIndex = this.forms.stock_entry.items.findIndex(
                i => i.material_id === this.scannedItemData.material_id
            );

            if (itemIndex !== -1) {
                const item = this.forms.stock_entry.items[itemIndex];
                const balance = item.ordered_qty - (item.received_before || 0);
                const addedQty = parseFloat(this.scannedItemData.scan_qty) || 1;
                const currentInForm = parseFloat(item.received_qty) || 0;

                // ≡ƒ¢í∩╕Å ╪╡┘à╪º┘à ╪º┘ä╪ú┘à╪º┘å: ┘à┘å╪╣ ╪º╪│╪¬┘ä╪º┘à ┘â┘à┘è╪⌐ ╪ú┘â╪¿╪▒ ┘à┘å ╪º┘ä┘à╪¬╪¿┘é┘è
                if ((currentInForm + addedQty) > balance) {
                    this.showToast(
                        this.isArabic
                            ? `╪«╪╖╪ú: ╪º┘ä┘â┘à┘è╪⌐ ╪º┘ä┘à╪¬╪¿┘é┘è╪⌐ ┘ç┘è ${balance} ┘ü┘é╪╖!`
                            : `Error: Remaining balance is only ${balance}!`,
                        'error'
                    );
                    return; // ┘ê┘é┘ü ╪º┘ä╪╣┘à┘ä┘è╪⌐
                }

                item.received_qty = currentInForm + addedQty;
                this.showToast(this.isArabic ? `╪¬┘à ╪Ñ╪╢╪º┘ü╪⌐ ${addedQty}` : `Added ${addedQty}`, 'success');
            }

            this.closeQtyModal();
        },

        // ≡ƒÜÇ 5. ╪Ñ╪║┘ä╪º┘é ╪º┘ä┘å╪º┘ü╪░╪⌐
        closeQtyModal() {
            this.showQtyModal = false;
            if (this.scannerInstance && this.isScanning) {
                if (this.scannerInstance.getState() === Html5QrcodeScannerState.PAUSED) {
                    this.scannerInstance.resume();
                }
            }
        },

        // ≡ƒÜÇ 6. ╪Ñ┘è┘é╪º┘ü ╪º┘ä┘â╪º┘à┘è╪▒╪º
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

        // ≡ƒÜÇ ╪»╪º┘ä╪⌐ ╪¬╪¡┘à┘è┘ä ┘é╪º┘ä╪¿ ╪º┘ä╪º╪│╪¬┘è╪▒╪º╪» (Template)
        downloadTemplate() {
            // ╪ú╪│┘à╪º╪í ╪º┘ä╪ú╪╣┘à╪»╪⌐ (┘ä╪º╪▓┘à ╪º┘ä╪¿╪º┘â-╪Ñ┘å╪» ┘è┘â┘ê┘å ┘à╪¬╪¿╪▒┘à╪¼ ┘è┘é╪▒╪ú ╪º┘ä╪ú╪│┘à╪º╪í ╪»┘è ╪¿╪º┘ä╪╕╪¿╪╖)
            const headers = ['SKU*', 'Name*', 'Category', 'Base_UOM', 'Barcode', 'Tracking'];

            // ╪╡┘ü ╪¬╪¼╪▒┘è╪¿┘è ╪╣╪┤╪º┘å ╪º┘ä┘à╪│╪¬╪«╪»┘à ┘è┘ü┘ç┘à ╪º┘ä┘ü┘ê╪▒┘à╪º╪¬
            const exampleRow = ['ITEM-001', '┘à╪½╪º┘ä: ╪ú╪│┘à┘å╪¬ ╪¿┘ê╪▒╪¬┘ä╪º┘å╪»┘è', 'Raw Materials', 'BAG', '123456789012', 'none'];

            // ╪¬╪¼┘à┘è╪╣ ╪º┘ä┘à┘ä┘ü
            let csvContent = "data:text/csv;charset=utf-8,\uFEFF"
                + headers.join(",") + "\n"
                + exampleRow.join(",");

            // ╪Ñ┘å╪┤╪º╪í ╪º┘ä╪▒╪º╪¿╪╖ ┘ê╪¬┘å╪▓┘è┘ä ╪º┘ä┘à┘ä┘ü
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", `Item_Import_Template.csv`);
            document.body.appendChild(link);
            link.click();
            link.remove();

            this.showToast(this.isArabic ? "╪¬┘à ╪¬╪¡┘à┘è┘ä ┘é╪º┘ä╪¿ ╪º┘ä╪º╪│╪¬┘è╪▒╪º╪»" : "Template downloaded", "success");
        },

        // 1. ╪»┘ê╪º┘ä ╪º┘ä╪¬╪¡┘â┘à ┘ü┘è ╪│╪╖┘ê╪▒ ╪ú┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪»
        addPOLine() {
            this.forms.po.lines.push({ material: '', quantity: 1, unit_price: 0 });
        },
        removePOLine(index) {
            if (this.forms.po.lines.length > 1) {
                this.forms.po.lines.splice(index, 1);
            } else {
                this.showToast(this.isArabic ? "┘è╪¼╪¿ ╪ú┘å ┘è╪¡╪¬┘ê┘è ╪º┘ä╪ú┘à╪▒ ╪╣┘ä┘ë ╪╡┘å┘ü ┘ê╪º╪¡╪» ╪╣┘ä┘ë ╪º┘ä╪ú┘é┘ä" : "PO must have at least one line", 'error');
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
                this.showToast(this.isArabic ? "┘è╪¼╪¿ ╪ú┘å ┘è╪¡╪¬┘ê┘è ╪º┘ä╪ú┘à╪▒ ╪╣┘ä┘ë ╪╡┘å┘ü ┘ê╪º╪¡╪» ╪╣┘ä┘ë ╪º┘ä╪ú┘é┘ä" : "SO must have at least one line", 'error');
            }
        },


        exportToExcel() {
            const list = this.filteredMaterials || [];
            if (list.length === 0) {
                this.showToast(this.isArabic ? "┘ä╪º ╪¬┘ê╪¼╪» ╪¿┘è╪º┘å╪º╪¬ ┘ä╪¬╪╡╪»┘è╪▒┘ç╪º" : "No data to export", "error");
                return;
            }

            const headers = this.isArabic
                ? ['╪º┘ä┘à╪╣╪▒┘ü', '╪º┘ä┘â┘ê╪» (SKU)', '╪º╪│┘à ╪º┘ä╪╡┘å┘ü', '╪º┘ä╪¬╪╡┘å┘è┘ü', '┘ê╪¡╪»╪⌐ ╪º┘ä┘é┘è╪º╪│']
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

            this.showToast(this.isArabic ? "╪¬┘à ╪º┘ä╪¬╪╡╪»┘è╪▒ ╪¿┘å╪¼╪º╪¡" : "Exported successfully", "success");
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
                this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪º┘ä┘à╪╣╪º┘ä╪¼╪⌐..." : "Processing...", "success");

                const res = await fetch('/api/materials/import/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
                    body: formData
                });

                if (res.ok) {
                    await this.fetchMaterialsList(); // ╪¬╪¡╪»┘è╪½ ╪º┘ä╪»╪º╪¬╪º
                    this.showToast(this.isArabic ? "╪¬┘à ╪º┘ä╪º╪│╪¬┘è╪▒╪º╪» ╪¿┘å╪¼╪º╪¡" : "Imported successfully", "success");
                } else {
                    this.showToast(this.isArabic ? "┘ü╪┤┘ä ╪º┘ä╪º╪│╪¬┘è╪▒╪º╪»╪î ╪¬╪ú┘â╪» ┘à┘å ╪º┘ä┘à┘ä┘ü" : "Import failed", "error");
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
                'po_receipt': this.isArabic ? '╪Ñ╪╢╪º┘ü╪⌐ ┘à┘å ╪ú┘à╪▒ ╪¬┘ê╪▒┘è╪»' : 'Purchase Receipt',
                'mrp_receipt': this.isArabic ? '╪Ñ╪╢╪º┘ü╪⌐ ┘à┘å ╪ú┘à╪▒ ╪¬╪╡┘å┘è╪╣' : 'Production Receipt',
                'so_return': this.isArabic ? '┘à╪▒╪¬╪¼╪╣ ┘à┘å ╪ú┘à╪▒ ╪¿┘è╪╣' : 'Sales Return',
                'incoming_transfer': this.isArabic ? '╪º╪│╪¬┘ä╪º┘à ╪¬╪¡┘ê┘è┘ä ┘à╪«╪▓┘å┘è' : 'Incoming Transfer',
                'so_delivery': this.isArabic ? '╪╡╪▒┘ü ┘ä╪ú┘à╪▒ ╪¿┘è╪╣' : 'Sales Delivery',
                'internal_transfer': this.isArabic ? '╪¬╪¡┘ê┘è┘ä ┘à╪«╪▓┘å┘è ╪»╪º╪«┘ä┘è' : 'Internal Transfer',
                'mrp_issue': this.isArabic ? '╪╡╪▒┘ü ┘ä╪ú┘à╪▒ ╪¬╪╡┘å┘è╪╣' : 'Material Issue for Production',
                'scrap': this.isArabic ? '╪¬╪│╪¼┘è┘ä ┘ç╪º┘ä┘â' : 'Scrap Entry',
                'po_return': this.isArabic ? '┘à╪▒╪»┘ê╪»╪º╪¬ ┘à╪┤╪¬╪▒┘è╪º╪¬' : 'Purchase Return'
            };
            return titles[this.activeOperation] || (this.isArabic ? '╪╣┘à┘ä┘è╪⌐ ┘à╪«╪▓┘å┘è╪⌐' : 'Stock Operation');
        },

        startOperation(type) {
            this.activeOperation = type;
            // ≡ƒÜÇ ┘ä┘ê ╪º┘ä╪╣┘à┘ä┘è╪⌐ ┘ç┘è ╪º╪│╪¬┘ä╪º┘à ┘à┘å ┘à┘ê╪▒╪»╪î ┘å╪º╪»┘è ╪ú┘ê╪º┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪» ┘ü┘ê╪▒╪º┘ï
            if (type === 'po_receipt') {
                this.fetchPendingPOs();
            }
            // ≡ƒÜÜ ┘ä┘ê ╪º┘ä╪╣┘à┘ä┘è╪⌐ ┘ç┘è ╪╡╪▒┘ü ┘ä╪¿┘è╪╣╪î ┘å╪º╪»┘è ╪ú┘ê╪º┘à╪▒ ╪º┘ä╪¿┘è╪╣ ┘ü┘ê╪▒╪º┘ï
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
            // 1. ╪Ñ┘è┘é╪º┘ü ╪º┘ä┘â╪º┘à┘è╪▒╪º ┘ü┘ê╪▒╪º┘ï ┘ê╪¿╪┤┘â┘ä ╪╡╪¡┘è╪¡
            if (this.isScanning) {
                // ╪¿┘å┘å╪º╪»┘è ╪╣┘ä┘ë ╪º┘ä┘à┘â╪¬╪¿╪⌐ ╪╣╪┤╪º┘å ╪¬┘ê┘é┘ü ╪º┘ä┘à╪│╪¡ ┘ê╪¬┘å╪╕┘ü ╪º┘ä┘Ç DOM
                const html5QrCode = new Html5Qrcode("reader");
                if (html5QrCode.isScanning) {
                    html5QrCode.stop().then(() => {
                        console.log("Camera Stopped");
                    }).catch(err => {
                        console.warn("Stop failed:", err);
                    });
                }
            }

            // 2. ╪¬╪╡┘ü┘è╪▒ ┘â┘ä ╪º┘ä╪¡╪º┘ä╪º╪¬ (╪º┘ä┘Ç Variables)
            this.activeOperation = null;
            this.isScanning = false;
            this.barcodeQuery = '';

            // ╪¬╪╡┘ü┘è╪▒ ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪º╪│╪¬┘ä╪º┘à ╪╣╪┤╪º┘å ┘ä┘ê ┘ü╪¬╪¡╪¬ ╪ú┘à╪▒ ╪¬┘ê╪▒┘è╪» ╪¬╪º┘å┘è ┘à┘è╪¿┘é╪º╪┤ ┘ü┘è┘ç ╪»╪º╪¬╪º ┘é╪»┘è┘à╪⌐
            this.forms.stock_entry = {
                po_id: '',
                items: []
            };

            // ╪Ñ╪«┘ü╪º╪í ╪ú┘è ╪▒╪│╪º╪ª┘ä Toast ┘é╪»┘è┘à╪⌐
            this.loading = false;
        },

        // ≡ƒÜÇ ╪Ñ╪╢╪º┘ü╪⌐ ╪º┘ä┘ä┘ê╪¼┘è┘â ╪º┘ä╪░┘â┘è ┘ä╪¼┘ä╪¿ ╪º┘ä┘Ç PO ┘ê╪¬╪¡╪»┘è╪» ╪º┘ä╪▒┘ü ╪¿┘å╪º╪í┘ï ╪╣┘ä┘ë ╪º┘ä╪┤╪▒┘â╪⌐
        async fetchPODetails() {
            const poId = this.forms.stock_entry.po_id;
            if (!poId) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/orders/${poId}/`);
                const data = await res.json();
                const currentOpcoId = parseInt(this.activeOpcoId);

                // ≡ƒÜÇ ╪¬╪¡╪»┘è╪» ┘å┘ê╪╣ ╪º┘ä╪¡╪▒┘â╪⌐ "╪Ñ╪╢╪º┘ü╪⌐" ┘ü┘ê╪▒ ╪º╪«╪¬┘è╪º╪▒ ╪º┘ä╪ú┘à╪▒
                this.forms.stock_entry.move_type = 'IN';

                this.forms.stock_entry.items = data.lines.map(i => {
                    const material = this.materials_list.find(m => m.id === i.material);

                    // ╪º╪│╪¬╪«╪▒╪º╪¼ ╪º┘ä╪▒┘ü ╪º┘ä╪º┘ü╪¬╪▒╪º╪╢┘è
                    let autoSelectedBin = i.default_bin || '';
                    if (!autoSelectedBin && material?.company_assignments) {
                        const assign = material.company_assignments.find(a => parseInt(a.opco_id) === currentOpcoId);
                        autoSelectedBin = assign?.primary_bin || (assign?.bins?.length > 0 ? assign.bins[0] : '');
                    }

                    return {
                        material_id: i.material,
                        material_name: i.material_name || material?.name || 'Unknown',
                        sku: i.material_sku || material?.sku || 'N/A',
                        ordered_qty: parseFloat(i.quantity),          // ╪º┘ä╪╖┘ä╪¿ ╪º┘ä╪ú╪╡┘ä┘è
                        received_before: parseFloat(i.received_qty || 0), // ╪º┘ä┘à╪│╪¬┘ä┘à ╪│╪º╪¿┘é╪º┘ï (┘à┘å ╪º┘ä╪│┘è╪▒┘ü╪▒)
                        received_qty: 0,                               // ╪º┘ä┘â┘à┘è╪⌐ ╪º┘ä╪¡╪º┘ä┘è╪⌐ (╪╡┘ü╪▒ ┘à╪ñ┘é╪¬╪º┘ï)
                        bin_id: autoSelectedBin
                    };
                });

                this.showToast(this.isArabic ? "╪¬┘à ╪¬╪¡┘à┘è┘ä ╪¬┘ü╪º╪╡┘è┘ä ╪º┘ä╪ú┘à╪▒ ┘ê╪º┘ä┘â┘à┘è╪º╪¬ ╪º┘ä╪│╪º╪¿┘é╪⌐" : "PO details and history loaded", 'success');
            } catch (e) {
                this.showToast(this.isArabic ? "╪«╪╖╪ú ┘ü┘è ╪¼┘ä╪¿ ╪º┘ä╪¿┘è╪º┘å╪º╪¬" : "Fetch error", 'error');
            } finally {
                this.loading = false;
            }
        },

        // ≡ƒÜÇ ╪»╪º┘ä╪⌐ ╪¼┘ä╪¿ ╪¬┘ü╪º╪╡┘è┘ä ╪ú┘à╪▒ ╪º┘ä╪¿┘è╪╣ ┘ä┘ä╪╡╪▒┘ü (SO Delivery)
        async fetchSODetailsForDelivery() {
            const soId = this.forms.stock_entry.so_id;
            if (!soId) return;

            try {
                this.loading = true;
                const res = await fetch(`/api/wms/sales-orders/${soId}/`);
                const data = await res.json();
                const currentOpcoId = parseInt(this.activeOpcoId);

                // ╪¬╪¡╪»┘è╪» ┘å┘ê╪╣ ╪º┘ä╪¡╪▒┘â╪⌐ "╪╡╪▒┘ü" ┘ü┘ê╪▒ ╪º╪«╪¬┘è╪º╪▒ ╪º┘ä╪ú┘à╪▒
                this.forms.stock_entry.move_type = 'OUT';

                this.forms.stock_entry.items = data.items.map(i => {
                    const material = this.materials_list.find(m => m.id === i.material_id);

                    // ╪º╪│╪¬╪«╪▒╪º╪¼ ╪º┘ä╪▒┘ü ╪º┘ä╪▒╪ª┘è╪│┘è ┘ä╪¼┘ä╪¿┘ç ┘â╪º┘ü╪¬╪▒╪º╪╢┘è ┘ä┘ä╪╡╪▒┘ü
                    let autoSelectedBin = '';
                    if (material?.company_assignments) {
                        const assign = material.company_assignments.find(a => parseInt(a.opco_id) === currentOpcoId);
                        autoSelectedBin = assign?.primary_bin || (assign?.bins?.length > 0 ? assign.bins[0] : '');
                    }

                    return {
                        material_id: i.material_id,
                        material_name: i.material_name || material?.name || 'Unknown',
                        sku: i.sku || material?.sku || 'N/A',
                        ordered_qty: parseFloat(i.ordered_qty),          // ╪º┘ä╪╖┘ä╪¿ ╪º┘ä╪ú╪╡┘ä┘è
                        received_before: parseFloat(i.received_qty || 0), // ╪º┘ä┘à╪╡╪▒┘ê┘ü ╪│╪º╪¿┘é╪º┘ï (┘à┘å ╪º┘ä╪│┘è╪▒┘ü╪▒)
                        received_qty: 0,                                  // ╪º┘ä┘â┘à┘è╪⌐ ╪º┘ä╪¡╪º┘ä┘è╪⌐ (╪╡┘ü╪▒ ┘à╪ñ┘é╪¬╪º┘ï)
                        bin_id: autoSelectedBin
                    };
                });

                this.showToast(this.isArabic ? "╪¬┘à ╪¬╪¡┘à┘è┘ä ╪¬┘ü╪º╪╡┘è┘ä ╪ú┘à╪▒ ╪º┘ä╪¿┘è╪╣ ┘ê╪º┘ä┘â┘à┘è╪º╪¬ ╪º┘ä┘à┘å╪╡╪▒┘ü╪⌐" : "SO details and delivery history loaded", 'success');
            } catch (e) {
                this.showToast(this.isArabic ? "╪«╪╖╪ú ┘ü┘è ╪¼┘ä╪¿ ╪º┘ä╪¿┘è╪º┘å╪º╪¬" : "Fetch error", 'error');
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

            // 1. ╪º┘ä╪¬╪¡┘é┘é ┘à┘å ╪º╪«╪¬┘è╪º╪▒ ╪ú┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪» / ╪º┘ä╪¿┘è╪╣
            if (!isDelivery && !entry.po_id) {
                this.showToast(this.isArabic ? "╪¿╪▒╪¼╪º╪í ╪º╪«╪¬┘è╪º╪▒ ╪ú┘à╪▒ ╪¬┘ê╪▒┘è╪»" : "Please select a PO", 'error');
                return;
            }
            if (isDelivery && !entry.so_id) {
                this.showToast(this.isArabic ? "╪¿╪▒╪¼╪º╪í ╪º╪«╪¬┘è╪º╪▒ ╪ú┘à╪▒ ╪¿┘è╪╣" : "Please select a SO", 'error');
                return;
            }

            // 2. ┘ü┘ä╪¬╪▒╪⌐ ╪º┘ä╪ú╪╡┘å╪º┘ü ╪º┘ä┘à╪│╪¬┘ä┘à╪⌐ / ╪º┘ä┘à╪╡╪▒┘ê┘ü╪⌐
            const itemsToProcess = entry.items.filter(i => parseFloat(i.received_qty) > 0);

            if (itemsToProcess.length === 0) {
                this.showToast(this.isArabic ? (isDelivery ? "┘è╪¼╪¿ ╪Ñ╪»╪«╪º┘ä ┘â┘à┘è╪⌐ ╪╡╪▒┘ü ┘ê╪º╪¡╪»╪⌐ ╪╣┘ä┘ë ╪º┘ä╪ú┘é┘ä" : "┘è╪¼╪¿ ╪Ñ╪»╪«╪º┘ä ┘â┘à┘è╪⌐ ╪º╪│╪¬┘ä╪º┘à ┘ê╪º╪¡╪»╪⌐ ╪╣┘ä┘ë ╪º┘ä╪ú┘é┘ä") : "Enter at least one quantity", 'error');
                return;
            }

            // ≡ƒÜÇ ╪º┘ä╪¬╪¡┘é┘é ┘à┘å ╪º┘ä┘â┘à┘è╪º╪¬ ╪º┘ä┘à╪│╪¬┘ä┘à╪⌐/╪º┘ä┘à╪╡╪▒┘ê┘ü╪⌐ ╪│╪º╪¿┘é╪º ┘ê╪º┘ä┘à╪¬╪¿┘é┘è╪⌐
            for (const item of itemsToProcess) {
                const balance = item.ordered_qty - (item.received_before || 0); // ╪º┘ä┘à╪¬╪¿┘é┘è ╪º┘ä╪¡┘é┘è┘é┘è
                if (item.received_qty > balance) {
                    this.showToast(
                        this.isArabic
                            ? `╪«╪╖╪ú: ╪º┘ä┘â┘à┘è╪⌐ ╪º┘ä┘à┘â╪¬┘ê╪¿╪⌐ ┘ä┘Ç (${item.material_name}) ┘ê┘ç┘è ${item.received_qty} ╪ú┘â╪¿╪▒ ┘à┘å ╪º┘ä┘à╪¬╪¿┘é┘è ┘ü┘è ╪º┘ä╪ú┘à╪▒ (${balance})`
                            : `Error: Quantity for ${item.material_name} exceeds remaining balance`,
                        'error'
                    );
                    return; // ┘ê┘é┘ü ╪º┘ä╪╣┘à┘ä┘è╪⌐ ┘ü┘ê╪▒╪º┘ï ┘ê┘à┘å╪╣ ╪º┘ä╪Ñ╪▒╪│╪º┘ä ┘ä┘ä╪│┘è╪▒┘ü╪▒
                }
            }

            // 3. ╪º┘ä╪¬╪¡┘é┘é ┘à┘å ╪º┘ä╪▒┘ü┘ê┘ü
            const missingBins = itemsToProcess.filter(i => !i.bin_id);
            if (missingBins.length > 0) {
                this.showToast(this.isArabic ? "╪¿╪▒╪¼╪º╪í ╪¬╪¡╪»┘è╪» ╪º┘ä╪▒┘ü ┘ä┘â┘ä ╪╡┘å┘ü" : "Select bins", 'error');
                return;
            }

            try {
                this.loading = true;

                // ╪º┘ä╪¬┘à┘è┘è╪▓ ╪¿┘è┘å ╪º┘ä╪º╪│╪¬┘ä╪º┘à ┘ê╪º┘ä╪╡╪▒┘ü (╪º╪│╪¬╪«╪»╪º┘à ╪º┘ä╪▒┘ê╪º╪¿╪╖ ╪º┘ä┘à┘ê╪¡╪»╪⌐ ╪º┘ä╪¼╪»┘è╪»╪⌐)
                const apiEndpoint = isDelivery ? '/api/stock-deliveries/' : '/api/stock-receipts/';
                const payload = {
                    opco: this.activeOpcoId,
                    items: itemsToProcess.map(item => ({
                        material: item.material_id, // ╪¬╪║┘è┘è╪▒ material_id ╪Ñ┘ä┘ë material
                        quantity: item.received_qty,
                        storage_bin: item.bin_id    // ╪¬╪║┘è┘è╪▒ bin_id ╪Ñ┘ä┘ë storage_bin
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
                        this.isArabic ? `╪¬┘à ╪¡┘ü╪╕ ╪º┘ä╪Ñ╪░┘å ╪▒┘é┘à ${docNumber} ╪¿┘å╪¼╪º╪¡` : `Document ${docNumber} saved`,
                        'success'
                    );

                    // ╪╖╪¿╪º╪╣╪⌐ ╪º┘ä╪Ñ╪░┘å ┘ü┘ê╪▒╪º┘ï
                    const printMsg = isDelivery ? "┘ç┘ä ╪¬╪▒┘è╪» ╪╖╪¿╪º╪╣╪⌐ ╪Ñ╪░┘å ╪º┘ä╪╡╪▒┘ü ╪º┘ä╪ó┘å╪ƒ" : "┘ç┘ä ╪¬╪▒┘è╪» ╪╖╪¿╪º╪╣╪⌐ ╪Ñ╪░┘å ╪º┘ä╪Ñ╪╢╪º┘ü╪⌐ ╪º┘ä╪ó┘å╪ƒ";
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
            const vendorName = prompt(this.isArabic ? "╪ú╪»╪«┘ä ╪º╪│┘à ╪º┘ä┘à┘ê╪▒╪» ╪º┘ä╪¼╪»┘è╪»:" : "Enter new vendor name:");
            if (!vendorName) return;

            // ╪Ñ┘å╪┤╪º╪í ┘â┘ê╪» ┘à╪¿╪»╪ª┘è ┘ä┘ä┘à┘ê╪▒╪»
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
                    this.vendors.push(newVendor); // ╪Ñ╪╢╪º┘ü╪¬┘ç ┘ä┘ä┘é╪º╪ª┘à╪⌐ ┘ü┘ê╪▒╪º┘ï
                    this.forms.po.vendor = newVendor.id; // ╪º╪«╪¬┘è╪º╪▒┘ç ╪¬┘ä┘é╪º╪ª┘è╪º┘ï ┘ü┘è ╪º┘ä┘ü┘ê╪▒┘à
                    this.showToast(this.isArabic ? "╪¬┘à ╪Ñ╪╢╪º┘ü╪⌐ ╪º┘ä┘à┘ê╪▒╪» ╪¿┘å╪¼╪º╪¡" : "Vendor added", "success");
                }
            } catch (e) {
                this.showToast("Error adding vendor", "error");
            } finally {
                this.loading = false;
            }
        },

        // ≡ƒÜÇ ╪»╪º┘ä╪⌐ ╪¬┘å╪│┘è┘é ╪º┘ä╪¬╪º╪▒┘è╪« ╪╣╪┤╪º┘å ╪º┘ä╪¼╪»┘ê┘ä ┘è╪╕┘ç╪▒ ╪¿╪┤┘â┘ä ╪┤┘è┘â ┘ê┘à┘è╪╢╪▒╪¿╪┤ ╪Ñ┘è╪▒┘ê╪▒
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

        // ╪ú╪╢┘ü ┘ç╪░┘ç ╪º┘ä╪»┘ê╪º┘ä ╪»╪º╪«┘ä methods
        addCompanyRow() {
            // ╪º┘ä╪¬╪ú┘â╪» ┘à┘å ┘ê╪¼┘ê╪» ╪º┘ä┘â╪º╪ª┘å ┘ê╪º┘ä┘à╪╡┘ü┘ê┘ü╪⌐ ╪ú┘ê┘ä╪º┘ï ┘ä╪¬╪¼┘å╪¿ ╪º┘ä┘Ç TypeError
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
            event.target.value = ""; // ╪¬╪╡┘ü┘è╪▒ ╪º┘ä╪º╪«╪¬┘è╪º╪▒ ╪¿╪╣╪» ╪º┘ä╪Ñ╪╢╪º┘ü╪⌐
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

        // ≡ƒÜÇ ┘å╪╕╪º┘à ╪º┘ä╪¬┘å╪¿┘è┘ç╪º╪¬ ╪º┘ä╪º╪¡╪¬╪▒╪º┘ü┘è ┘ü┘è ┘à┘å╪¬╪╡┘ü ╪º┘ä╪┤╪º╪┤╪⌐
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
                    // Γ£à ╪º╪│╪¬╪«╪»╪º┘à ╪º┘ä╪¬┘å╪¿┘è┘ç ╪º┘ä╪º╪¡╪¬╪▒╪º┘ü┘è
                    this.showToast(this.isArabic ? "╪╣╪░╪▒╪º┘ï╪î ┘ä╪º ╪¬┘à┘ä┘â ╪╡┘ä╪º╪¡┘è╪⌐ ╪º┘ä┘ê╪╡┘ê┘ä ┘ä┘ç╪░┘ç ╪º┘ä╪┤╪▒┘â╪⌐" : "Access denied for this company", 'error');
                }
            } catch (error) {
                console.error("Switch Company Error:", error);
                this.showToast(this.isArabic ? "╪¡╪»╪½ ╪«╪╖╪ú ╪ú╪½┘å╪º╪í ╪º┘ä╪¬╪¿╪»┘è┘ä" : "Error while switching", 'error');
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

        addRecipeLine() {
            itemMasterModule.methods.addRecipeLine(this);
        },

        editItem(type, item) {

            if (type === 'po' && ['Received', 'Confirmed'].includes(item.status)) {
                this.showToast(
                    this.isArabic ? "┘ä╪º ┘è┘à┘â┘å ╪¬╪╣╪»┘è┘ä ╪ú┘à╪▒ ╪¬┘ê╪▒┘è╪» ╪¬┘à ╪º╪│╪¬┘ä╪º┘à┘ç ╪ú┘ê ╪¬╪ú┘â┘è╪»┘ç" : "Cannot edit a Received/Confirmed PO",
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
                    // ≡ƒÜÇ ╪º┘ä╪¬╪╣╪»┘è┘ä ╪º┘ä╪¼┘ê┘ç╪▒┘è ┘ç┘å╪º ┘ä┘à┘ä╪í ╪º┘ä╪¼╪»┘ê┘ä ╪º┘ä╪»┘è┘å╪º┘à┘è┘â┘è ╪╣┘å╪» ╪º┘ä╪¬╪╣╪»┘è┘ä
                    // ┘å╪¡┘ê┘ä ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪º┘ä┘à╪│╪╖╪¡╪⌐ ╪º┘ä┘é╪º╪»┘à╪⌐ ┘à┘å ╪º┘ä╪│┘è╪▒┘ü╪▒ ╪Ñ┘ä┘ë ┘à╪╡┘ü┘ê┘ü╪⌐ ╪º┘ä┘Ç Assignments
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
            // 1. ╪¬╪¡╪»┘è╪½ ┘é┘è┘à╪⌐ ╪º┘ä╪▒┘ü ╪º┘ä╪▒╪ª┘è╪│┘è ┘ü┘è ┘å┘à┘ê╪░╪¼ ╪º┘ä╪╡┘å┘ü
            this.forms.material.primary_bin = binId;

            // 2. ╪º┘ä╪¬╪ú┘â╪» ┘à┘å ╪ú┘å ╪º┘ä╪▒┘ü ╪º┘ä┘à╪«╪¬╪º╪▒ ┘â┘Ç Primary ┘à┘ê╪¼┘ê╪» ╪ú╪╡┘ä╪º┘ï ┘ü┘è ┘é╪º╪ª┘à╪⌐ ╪º┘ä╪▒┘ü┘ê┘ü ╪º┘ä┘à╪«╪¬╪º╪▒╪⌐
            if (!this.forms.material.assigned_bins.includes(binId)) {
                this.forms.material.assigned_bins.push(binId);
            }

            // 3. ╪¬┘å╪¿┘è┘ç ╪¿╪╡╪▒┘ë ╪│╪▒┘è╪╣ ┘ä┘ä┘à╪│╪¬╪«╪»┘à
            this.showToast(
                this.isArabic ? "╪¬┘à ╪¬╪¡╪»┘è╪» ╪º┘ä╪▒┘ü ┘â┘ê╪¼┘ç╪⌐ ╪º┘ü╪¬╪▒╪º╪╢┘è╪⌐ ┘ä┘ä╪º╪│╪¬┘ä╪º┘à" : "Primary bin set for Putaway",
                'success'
            );
        },

        // ╪»╪º┘ä╪⌐ ┘à╪¡╪│┘å╪⌐ ┘ä╪º╪«╪¬┘è╪º╪▒/╪Ñ┘ä╪║╪º╪í ╪º╪«╪¬┘è╪º╪▒ ╪º┘ä╪▒┘ü┘ê┘ü
        toggleBinSelection(binId) {
            const index = this.forms.material.assigned_bins.indexOf(binId);
            if (index > -1) {
                // ╪Ñ╪░╪º ┘â╪º┘å ╪º┘ä┘à╪│╪¬╪«╪»┘à ┘è┘ä╪║┘è ╪º╪«╪¬┘è╪º╪▒ ╪▒┘ü ┘ç┘ê ╪ú╪╡┘ä╪º┘ï ╪º┘ä╪▒┘ü ╪º┘ä╪▒╪ª┘è╪│┘è
                if (this.forms.material.primary_bin === binId) {
                    this.forms.material.primary_bin = null;
                }
                this.forms.material.assigned_bins.splice(index, 1);
            } else {
                this.forms.material.assigned_bins.push(binId);
            }
        },

        async deleteItem(type, id) {
            // ≡ƒ¢í∩╕Å ╪╡┘à╪º┘à ╪º┘ä╪ú┘à╪º┘å: ╪¡┘à╪º┘è╪⌐ ╪º┘ä┘â┘è╪º┘å ╪º┘ä╪ú╪│╪º╪│┘è ┘à┘å ╪º┘ä╪¡╪░┘ü
            if (type === 'opco') {
                const targetOpco = (this.opcos || []).find(o => o.id === id);

                // ┘à┘å╪╣ ╪¡╪░┘ü ╪º┘ä╪┤╪▒┘â╪⌐ ╪Ñ╪░╪º ┘â╪º┘å╪¬ ┘ç┘è ╪º┘ä┘é╪º╪¿╪╢╪⌐ (Holding) ╪ú┘ê ╪º┘ä╪┤╪▒┘â╪⌐ ╪º┘ä╪ú┘à (╪º┘ä╪¬┘è ┘ä┘è╪│ ┘ä┘ç╪º Parent)
                if (targetOpco && (targetOpco.is_holding || !targetOpco.parent)) {
                    this.showToast(
                        this.isArabic ? "┘ä╪º ┘è┘à┘â┘å ╪¡╪░┘ü ╪º┘ä╪┤╪▒┘â╪⌐ ╪º┘ä╪ú╪│╪º╪│┘è╪⌐ ┘ä┘ä┘à┘å╪╕┘ê┘à╪⌐" : "The primary entity cannot be deleted",
                        'error'
                    );
                    return; // ╪Ñ┘è┘é╪º┘ü ╪º┘ä╪╣┘à┘ä┘è╪⌐ ┘ü┘ê╪▒╪º┘ï
                }
            }

            // 1∩╕ÅΓâú ╪Ñ╪╕┘ç╪º╪▒ ╪º┘ä┘à┘ê╪»╪º┘ä ╪º┘ä┘à╪«╪╡╪╡ ┘ä┘ä╪¬╪ú┘â┘è╪»
            this.confirmModal.show = true;

            // 2∩╕ÅΓâú ╪¬╪╣╪▒┘è┘ü ┘ê╪╕┘è┘ü╪⌐ "╪╣┘å╪» ╪º┘ä╪¬╪ú┘â┘è╪»" (Logic ╪º┘ä╪¡╪░┘ü ╪º┘ä┘ü╪╣┘ä┘è)
            this.confirmModal.onConfirm = async () => {
                this.confirmModal.show = false; // ╪Ñ╪«┘ü╪º╪í ╪º┘ä┘à┘ê╪»╪º┘ä ┘ü┘ê╪▒╪º┘ï
                try {
                    this.loading = true;
                    const res = await fetch(`/api/${type}s/${id}/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': this.getCookie('csrftoken')
                        }
                    });

                    if (res.ok) {
                        // ╪¬╪¡╪»┘è╪½ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ┘ü┘è ╪º┘ä┘ê╪º╪¼┘ç╪⌐
                        await this.refreshAllData();
                        // ╪Ñ╪╕┘ç╪º╪▒ ╪▒╪│╪º┘ä╪⌐ ┘å╪¼╪º╪¡ ╪º╪¡╪¬╪▒╪º┘ü┘è╪⌐ ┘ü┘è ┘à┘å╪¬╪╡┘ü ╪º┘ä╪┤╪º╪┤╪⌐
                        this.showToast(this.isArabic ? "╪¬┘à ╪º┘ä╪¡╪░┘ü ╪¿┘å╪¼╪º╪¡" : "Deleted successfully", 'success');
                    } else {
                        // ┘à╪╣╪º┘ä╪¼╪⌐ ┘ü╪┤┘ä ╪º┘ä╪¡╪░┘ü (┘à╪½┘ä╪º┘ï ┘ä┘ê╪¼┘ê╪» ╪¿┘è╪º┘å╪º╪¬ ┘à╪▒╪¬╪¿╪╖╪⌐)
                        const errorData = await res.text();
                        console.error("Delete Error:", errorData);
                        this.showToast(this.isArabic ? "┘ü╪┤┘ä ╪º┘ä╪¡╪░┘ü: ┘é╪» ┘è┘â┘ê┘å ╪º┘ä╪╣┘å╪╡╪▒ ┘à╪▒╪¬╪¿╪╖╪º┘ï ╪¿╪¿┘è╪º┘å╪º╪¬ ╪ú╪«╪▒┘ë" : "Delete failed: Item may be linked to other data", 'error');
                    }
                } catch (e) {
                    console.error("Network Error:", e);
                    this.showToast(this.isArabic ? "╪¡╪»╪½ ╪«╪╖╪ú ┘ü┘è ╪º┘ä╪┤╪¿┘â╪⌐ ╪ú╪½┘å╪º╪í ╪º┘ä╪¡╪░┘ü" : "Network error during deletion", 'error');
                } finally {
                    this.loading = false;
                }
            };

            // 3∩╕ÅΓâú ╪¬╪╣╪▒┘è┘ü ┘ê╪╕┘è┘ü╪⌐ "╪╣┘å╪» ╪º┘ä╪Ñ┘ä╪║╪º╪í"
            this.confirmModal.onCancel = () => {
                this.confirmModal.show = false;
                // ┘ä╪º ┘è╪¬┘à ╪º╪¬╪«╪º╪░ ╪ú┘è ╪Ñ╪¼╪▒╪º╪í ╪ó╪«╪▒
            };
        },

        async submitForm() {
            // 1. ╪º┘ä╪¬╪╣╪º┘à┘ä ┘à╪╣ ╪¡┘ü╪╕ ╪º┘ä╪Ñ╪╣╪»╪º╪»╪º╪¬ ╪º┘ä╪╣╪º┘à╪⌐ (╪«╪º╪▒╪¼ ╪º┘ä┘à┘ê╪»╪º┘ä)
            if (this.view === 'global_config' && !this.showModal) {
                return await this.saveGlobalConfig();
            }

            const type = this.modalType;
            if (!type || !this.forms[type]) return;

            // 2. ╪º┘ä╪¬╪¡┘é┘é ┘à┘å ┘à┘å╪╖┘é ╪º┘ä╪┤╪▒┘â╪º╪¬ ╪º┘ä╪¬╪º╪¿╪╣╪⌐ (Business Logic)
            if (type === 'opco' && this.forms.opco.parent) {
                const parentCompany = this.allOpcos.find(o => o.id === parseInt(this.forms.opco.parent));
                if (parentCompany && !parentCompany.is_holding) {
                    this.showToast(
                        this.isArabic ? "┘ä╪º ┘è┘à┘â┘å ╪Ñ╪╢╪º┘ü╪⌐ ╪┤╪▒┘â╪⌐ ╪¬╪º╪¿╪╣╪⌐ ╪Ñ┘ä╪º ╪¬╪¡╪¬ ╪┤╪▒┘â╪⌐ ┘é╪º╪¿╪╢╪⌐ (Holding)" : "Subsidiaries can only be added under a Holding company",
                        'error'
                    );
                    return;
                }
            }

            const isEdit = this.isEditing;
            const id = this.forms[type].id;

            // 3. ╪¬╪¡╪»┘è╪» ╪º┘ä╪▒╪º╪¿╪╖ ┘ê┘å┘ê╪╣ ╪º┘ä╪╖┘ä╪¿
            let url = isEdit ? `/api/${type}s/${id}/` : `/api/${type}s/`;
            let method = isEdit ? 'PATCH' : 'POST';
            const csrftoken = this.getCookie('csrftoken');

            // ╪¬╪╡╪¡┘è╪¡ ┘à╪│╪º╪▒╪º╪¬ ╪º┘ä┘Ç API ╪º┘ä╪«╪º╪╡╪⌐ ╪¿┘â┘ä ┘à┘ê╪»┘è┘ä
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

                    // ≡ƒÜÇ ╪Ñ╪╢╪º┘ü╪⌐ ╪º┘ä┘Ç opco ┘ä┘Ç FormData
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
                        else if (data[key] !== null && !['logo', 'image', 'assigned_bins', 'primary_bin', 'company_assignments', 'recipe_lines', 'combo_lines'].includes(key)) {
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

                    // ≡ƒÜÇ ≡ƒÜÇ ╪º┘ä╪¬╪╣╪»┘è┘ä ╪º┘ä╪¼┘ê┘ç╪▒┘è ┘ç┘å╪º ┘ä╪╢┘à╪º┘å ╪Ñ╪▒╪│╪º┘ä opco ┘à╪╣ ╪º┘ä┘Ç JSON
                    let finalData = { ...this.forms[type] };

                    // ╪Ñ╪░╪º ┘â╪º┘å ╪º┘ä╪¡┘é┘ä opco ┘ü╪º╪▒╪║╪î ┘å╪│╪¬╪«╪»┘à ╪º┘ä╪┤╪▒┘â╪⌐ ╪º┘ä┘å╪┤╪╖╪⌐ ╪¡╪º┘ä┘è╪º┘ï
                    if (!finalData.opco && this.activeOpcoId) {
                        finalData.opco = this.activeOpcoId;
                    }

                    payload = JSON.stringify(finalData);
                }

                // ╪¬┘å┘ü┘è╪░ ╪º┘ä╪╖┘ä╪¿
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
                    this.showToast(this.isArabic ? "╪¬┘à ╪¡┘ü╪╕ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪¿┘å╪¼╪º╪¡" : "Data saved successfully", 'success');
                } else {
                    const errorResponse = await response.text();
                    this.showToast(this.isArabic ? "┘ü╪┤┘ä ╪º┘ä╪¡┘ü╪╕: " + errorResponse : "Save failed: " + errorResponse, 'error');
                }
            } catch (error) {
                console.error("Network Error:", error);
                this.showToast(this.isArabic ? "╪¡╪»╪½ ╪«╪╖╪ú ┘ü┘è ╪º┘ä╪┤╪¿┘â╪⌐ ╪ú┘ê ╪º┘ä╪│┘è╪▒┘ü╪▒" : "Network or Server error", 'error');
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
                    this.showToast(this.isArabic ? "┘ü╪┤┘ä ╪¡┘ü╪╕ ╪º┘ä╪Ñ╪╣╪»╪º╪»╪º╪¬" : "Failed to save settings", 'error');
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
            // Γ£à ╪▒╪│╪º┘ä╪⌐ ┘å╪¼╪º╪¡ ╪º╪¡╪¬╪▒╪º┘ü┘è╪⌐
            this.showToast(this.isArabic ? '╪¬┘à ╪¡┘ü╪╕ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪¿┘å╪¼╪º╪¡' : 'Data saved successfully', 'success');
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
                                'procurement_module': 'procurement',
                                'sales_module': 'sales',
                                'accounting_module': 'sales', // Assuming accounting belongs to sales suite
                                'restaurant_pos_module': 'restaurant_pos'
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
                
                this.fetchSaleGroups();
                // ╪¬╪¡┘à┘è┘ä ╪º┘ä┘à┘ê╪▒╪»┘è┘å ┘ê╪º┘ä┘à╪┤╪¬╪▒┘è╪º╪¬ ╪ú┘è╪╢╪º┘ï
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

                    // ≡ƒÜÇ ╪¬┘ê┘ä┘è╪» ╪º┘ä╪Ñ╪┤╪╣╪º╪▒╪º╪¬ ╪»┘è┘å╪º┘à┘è┘â┘è╪º┘ï ┘à┘å ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä┘à╪«╪▓┘ê┘å ╪º┘ä┘à┘å╪«┘ü╪╢
                    this.notifications = [];
                    if (this.wms_stats.low_stock_list && this.wms_stats.low_stock_list.length > 0) {
                        this.wms_stats.low_stock_list.forEach(item => {
                            this.notifications.push({
                                type: 'low_stock',
                                title: this.isArabic ? '╪º┘å╪«┘ü╪º╪╢ ┘à╪«╪▓┘ê┘å ╪╡┘å┘ü' : 'Low Stock Alert',
                                message: this.isArabic 
                                    ? `╪º┘ä╪╡┘å┘ü #${item.sku} ┘ê╪╡┘ä ┘ä┘ä╪¡╪» ╪º┘ä╪ú╪»┘å┘ë (${item.current_qty})` 
                                    : `Item #${item.sku} reached minimum level (${item.current_qty})`,
                                time: this.isArabic ? '╪º┘ä╪ó┘å' : 'Now'
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
                    // ≡ƒÜÇ ╪º┘ä╪¬╪╣╪»┘è┘ä: ╪»┘à╪¼ ╪º┘ä╪¿┘è╪º┘å╪º╪¬ ╪¿╪¡╪░╪▒ ┘ä┘ä╪¡┘ü╪º╪╕ ╪╣┘ä┘ë ╪º┘ä┘ç┘è┘â┘ä
                    this.kpis.inventory.total_items = data.kpis.materials || 0;
                    this.kpis.inventory.stock_qty = data.kpis.stock_qty || 0;
                    this.kpis.procurement.total = data.kpis.pending_pos || 0;
                    this.kpis.vendors = data.kpis.vendors || 0;
                }
            } catch (e) { console.log("KPI fetch error"); }
        },
        // ╪»╪º╪«┘ä methods ┘ü┘è main.js
        async onMaterialSelect(item) {
            // 1. ╪¼┘ä╪¿ ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪╡┘å┘ü ╪┤╪º┘à┘ä╪⌐ ╪º┘ä╪▒┘ü┘ê┘ü
            const res = await fetch(`/api/materials/${item.material_id}/`);
            const data = await res.json();

            // 2. ╪º┘ä╪¿╪¡╪½ ╪╣┘å ╪º┘ä╪▒┘ü ╪º┘ä┘ä┘è ┘ê╪º╪«╪» ╪¬╪╣┘ä┘è┘à "is_primary"
            const primary = data.material_bins.find(b => b.is_primary);

            if (primary) {
                this.forms.stock_entry.bin_id = primary.storage_bin;
                this.showToast(this.isArabic ? "╪¬┘à ╪¬╪¡╪»┘è╪» ╪º┘ä╪▒┘ü ╪º┘ä╪º┘ü╪¬╪▒╪º╪╢┘è ╪¬┘ä┘é╪º╪ª┘è╪º┘ï" : "Default bin selected", 'success');
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

        // ≡ƒÜÇ ┘ê╪╕╪º╪ª┘ü ┘ä┘ê╪¡╪⌐ ╪º┘ä╪¬╪¡┘â┘à ╪º┘ä╪¡┘è╪⌐ (WMS Dashboard Actions)
        openReceiptModal(poId) {
            this.modalType = 'stock_entry';
            this.activeOperation = 'po_receipt'; // ┘ê╪╢╪╣ ╪º┘ä╪º╪│╪¬┘ä╪º┘à ┘à┘å ╪ú┘à╪▒ ╪┤╪▒╪º╪í
            this.forms.stock_entry.po_id = poId;
            this.showModal = true;
            this.fetchPODetailsForReceipt(); // ╪¼┘ä╪¿ ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪ú╪╡┘å╪º┘ü ┘ä┘ä╪ú┘à╪▒
        },

        openDeliveryModal(soId) {
            this.modalType = 'stock_entry';
            this.activeOperation = 'so_delivery'; // ┘ê╪╢╪╣ ╪º┘ä╪╡╪▒┘ü ┘ä╪ú┘à╪▒ ╪¿┘è╪╣
            this.forms.stock_entry.so_id = soId;
            this.showModal = true;
            this.fetchSODetailsForDelivery(); // ╪¼┘ä╪¿ ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪ú╪╡┘å╪º┘ü ┘ä┘ä╪ú┘à╪▒
        },

        printInventoryReport() {
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪¬╪¡╪╢┘è╪▒ ╪¬┘é╪▒┘è╪▒ ╪º┘ä╪¼╪▒╪»..." : "Preparing Inventory Report...", 'info');
            window.open('/api/wms/inventory/print_audit/?pdf=1', '_blank');
        },

        viewStagnantStock() {
            this.view = 'inventory_module';
            this.inventoryTab = 'levels';
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪╣╪▒╪╢ ╪º┘ä╪ú╪╡┘å╪º┘ü ╪º┘ä╪¡╪º┘ä┘è╪⌐" : "Viewing Current Stock Levels", 'info');
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
                    this.showToast(this.isArabic ? "╪¬┘à ┘ü╪¬╪¡ ╪Ñ╪░┘å ╪º╪│╪¬┘ä╪º┘à (Standalone Mode)" : "Opened Stock Receipt (Standalone)", 'info');
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
                this.showToast(this.isArabic ? "┘ä╪º ╪¬┘ê╪¼╪» ╪ú╪╡┘å╪º┘ü ╪¬╪¡╪¬ ╪¡╪» ╪º┘ä╪╖┘ä╪¿" : "No items below reorder point", 'info');
                return;
            }

            // ╪¡╪│╪º╪¿ ╪º┘ä┘â┘à┘è╪⌐ ╪º┘ä┘à╪╖┘ä┘ê╪¿╪⌐ = ╪º┘ä╪¡╪» ╪º┘ä╪ú┘é╪╡┘ë - ╪º┘ä╪▒╪╡┘è╪» ╪º┘ä╪¡╪º┘ä┘è
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
                // ┘ç┘å╪¼┘è╪¿ ┘â┘ä ╪ú┘ê╪º┘à╪▒ ╪º┘ä╪¬┘ê╪▒┘è╪» ╪º┘ä╪«╪º╪╡╪⌐ ╪¿╪º┘ä╪┤╪▒┘â╪⌐ ╪º┘ä╪¡╪º┘ä┘è╪⌐
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
                    this.showToast(this.isArabic ? "╪¬┘à ╪¬╪¡╪»┘è╪½ ╪¡╪º┘ä╪⌐ ╪º┘ä╪╖┘ä╪¿ ╪¿┘å╪¼╪º╪¡" : "PO Status Updated", 'success');
                    await this.fetchPurchaseOrders(); // ╪¬╪¡╪»┘è╪½ ╪º┘ä╪¼╪»┘ê┘ä ┘ü┘ê╪▒╪º┘ï
                }
            } catch (e) {
                this.showToast("Network Error", 'error');
            } finally {
                this.loading = false;
            }
        },

        // ╪╢┘è┘ü ╪»┘è ╪¼┘ê┘ç ╪º┘ä┘Ç methods
        viewPODetails(po) {
            this.modalType = 'view_po'; // ┘ç┘å╪¡╪¬╪º╪¼ ┘å╪¼┘ç╪▓ Modal ┘è╪╣╪▒╪╢ ╪º┘ä╪¿┘è╪º┘å╪º╪¬
            this.forms.po = JSON.parse(JSON.stringify(po)); // ┘å╪│╪« ╪¿┘è╪º┘å╪º╪¬ ╪º┘ä╪ú┘à╪▒ ┘ä┘ä┘ü┘ê╪▒┘à
            this.showModal = true;
            this.showToast(this.isArabic ? "╪¼╪º╪▒┘è ╪╣╪▒╪╢ ╪¬┘ü╪º╪╡┘è┘ä ╪º┘ä╪ú┘à╪▒" : "Viewing PO Details", 'success');
        },

        // ╪»╪º┘ä╪⌐ ┘ä╪¿╪»╪í ╪╣┘à┘ä┘è╪⌐ ╪º┘ä╪╡╪▒┘ü ╪¿┘å╪º╪í┘ï ╪╣┘ä┘ë ╪ú┘à╪▒ ╪º┘ä╪¿┘è╪╣
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
                    this.showToast(this.isArabic ? "╪¬┘à ╪¬╪ú┘â┘è╪» ╪º┘ä╪ú┘à╪▒ ╪¿┘å╪¼╪º╪¡" : "Order Confirmed", 'success');
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
                title: this.isArabic ? '╪Ñ╪╢╪º┘ü╪⌐ ┘à╪¼┘à┘ê╪╣╪⌐ ╪¿┘è╪╣┘è╪⌐ ╪¼╪»┘è╪»╪⌐' : 'Add New Sale Group',
                input: 'text',
                inputPlaceholder: this.isArabic ? '╪º╪│┘à ╪º┘ä┘à╪¼┘à┘ê╪╣╪⌐ (┘à╪½┘ä╪º┘ï: ┘à╪┤╪▒┘ê╪¿╪º╪¬╪î ╪¿┘è╪¬╪▓╪º...)' : 'Group Name (e.g. Drinks, Pizza...)',
                showCancelButton: true,
                confirmButtonText: this.isArabic ? '╪¡┘ü╪╕' : 'Save'
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
                        this.showToast(this.isArabic ? "╪¬┘à╪¬ ╪º┘ä╪Ñ╪╢╪º┘ü╪⌐ ╪¿┘å╪¼╪º╪¡" : "Group added successfully", 'success');
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
                        const sound = this.$refs.notificationSound;
                        if (sound) sound.play().catch(e => console.log("Sound blocked"));
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
                    this.showToast(this.isArabic ? "╪¬┘à ╪¬╪¡╪»┘è╪½ ╪¡╪º┘ä╪⌐ ╪º┘ä╪╖┘ä╪¿" : "Order status updated", "success");
                    await this.fetchKDSOrders();
                }
            } catch (e) {
                this.showToast("KDS Update Error", "error");
            } finally {
                this.draggedOrder = null;
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

        formatTime(isoString) {
            if (!isoString) return '--:--';
            const date = new Date(isoString);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    }
}).mount('#app');
