import { utils } from './modules/utils.js';
import { inventoryModule } from './modules/inventory.js';
import { orgModule } from './modules/org_builder.js';
import { itemMasterModule } from './modules/itemMaster.js';

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            // 1. الحالة العامة (UI State)
            view: 'org_builder', 
            loading: false, 
            sidebarCollapsed: false,
            isArabic: true,
            isEditing: false,

            sidebarGroups: {
                settings: [
                    { id: 'global_config', name: { ar: 'الإعدادات العامة', en: 'Global Config' }, icon: 'fas fa-cogs' },
                    { id: 'users', name: { ar: 'المستخدمين', en: 'Users' }, icon: 'fas fa-users' },
                    { id: 'customize_form', name: { ar: 'تخصيص النماذج', en: 'Customize Form' }, icon: 'fas fa-edit' }
                ],
                operations: [
                    { id: 'org_builder', name: { ar: 'بناء الهيكل', en: 'Org Builder' }, icon: 'fas fa-sitemap' },
                    { id: 'inventory', name: { ar: 'المخزون', en: 'Inventory' }, icon: 'fas fa-boxes' },
                    { id: 'item_master', name: { ar: 'سجل الأصناف', en: 'Item Master' }, icon: 'fas fa-barcode' }
                ]
            },

            // 2. دمج الحالات
            ...(utils.state || {}),
            ...(inventoryModule.state || {}),
            
            // 3. بيانات النظام الأساسية
            user: { name: 'Loading...', role: '...', is_superuser: false },
            config: { company_name: 'Loading...' },
            kpis: { materials: 0, stock_qty: 0, vendors: 0, pending_pos: 0 },
            opcos: [], 
            plants: [], 
            locations: [], 
            bins: [],
            materials_list: [], // تأكد من وجودها هنا
            inventoryList: [],
            wms_stats: {},

            showModal: false, 
            modalType: '', 
            draggedType: null,
            activeOpcoId: null, 
            activePlantId: null, 
            activeLocationId: null,
            imagePreview: null,
            selectedFile: null,

            modalTitles: {
                plant: { ar: 'إضافة منشأة جديدة', en: 'Add New Facility' },
                location: { ar: 'إضافة موقع تخزين', en: 'Add Storage Location' },
                bin: { ar: 'إضافة رف/حاوية', en: 'Add New Bin' },
                material: { ar: 'تعريف صنف جديد', en: 'Define New Material' },
                stock_entry: { ar: 'إذن استلام / تحويل مخزني', en: 'Stock Inbound / Transfer' },
                opco: { ar: 'إضافة شركة مشغلة', en: 'Add Operating Company' }
            },

            forms: {
                ...(inventoryModule.state?.forms || {}),
                opco: { id: null, code: '', name: '', currency: 'USD' },
                plant: { id: null, opco: null, code: '', name: '' },
                location: { id: null, plant: null, code: '', name: '' },
                bin: { id: null, storage_location: null, code: '' },
                material: { 
                    id: null, sku: '', name: '', category: '', 
                    base_uom: 'PCS', barcode: '', opco: null, assigned_bins: [] 
                }
            }
        };
    },

    computed: {
        filteredInventory() {
            if (!this.activeOpcoId) return this.inventoryList;
            return this.inventoryList.filter(item => item.opco_id === this.activeOpcoId);
        },
        activeLocationName() {
            const loc = this.locations.find(l => l.id === this.activeLocationId);
            return loc ? loc.name : '...';
        }
    },

    methods: {
        ...utils.methods,
        ...itemMasterModule.methods,
        startClock() { utils.methods.startClock(this); },
        triggerReadySystem() { utils.methods.triggerReadySystem(this); },

        // Inventory & Image Methods
        // ابحث عن handleImageUpload وحدثها لتصبح هكذا:
        handleImageUpload(event) {
            if (this.modalType === 'material' || this.view === 'item_master') {
                itemMasterModule.methods.handleImageUpload(event, this);
            } else {
                inventoryModule.methods.handleImageUpload(event, this);
            }
        },
        async openItemCard(item) { await inventoryModule.methods.openItemCard(item, this); },
        addItemRow() { inventoryModule.methods.addItemRow(this); },
        removeItemRow(index) { inventoryModule.methods.removeItemRow(index, this); },
        async fetchSODetails() { await inventoryModule.methods.fetchSODetails(this); },
        onSOMaterialSelect() { inventoryModule.methods.onSOMaterialSelect(this); },

        // Org Builder Methods
        getPlantsForOpco(id) { return orgModule.methods.getPlantsForOpco(this, id); },
        getLocationsForPlant(id) { return orgModule.methods.getLocationsForPlant(this, id); },
        getBinsForLocation(id) { return orgModule.methods.getBinsForLocation(this, id); },
        getBinsCount(id) { return orgModule.methods.getBinsCount(this, id); },
        handleDrop(targetType, parentId) { orgModule.methods.handleDrop(this, targetType, parentId); },
        onDragStart(type) { this.draggedType = type; },
        startDrag(type) { this.onDragStart(type); },

        editItem(type, item) {
            this.isEditing = true;
            this.modalType = type;
            this.forms[type] = JSON.parse(JSON.stringify(item));
            this.showModal = true;
        },

        async deleteItem(type, id) {
            if (!confirm(this.isArabic ? "هل أنت متأكد من الحذف؟" : "Are you sure?")) return;
            try {
                const res = await fetch(`/api/${type}s/${id}/`, {
                    method: 'DELETE',
                    headers: { 'X-CSRFToken': this.getCookie('csrftoken') }
                });
                if (res.ok) await this.refreshAllData();
            } catch (e) { console.error(e); }
        },

        async submitForm() {
            const type = this.modalType;
            const isEdit = this.isEditing;
            const id = this.forms[type]?.id;

            let url = isEdit ? `/api/${type}s/${id}/` : `/api/${type}s/`; 
            let method = isEdit ? 'PUT' : 'POST'; 
            let payload;
            const csrftoken = this.getCookie('csrftoken');

            try {
                if (type === 'material') {
                    payload = new FormData();
                    const opcoId = this.forms.material.opco || this.activeOpcoId || (this.opcos[0]?.id);
                    payload.append('opco', parseInt(opcoId));
                    payload.append('sku', this.forms.material.sku);
                    payload.append('name', this.forms.material.name);
                    payload.append('base_uom', this.forms.material.base_uom);
                    if (this.forms.material.assigned_bins) {
                        this.forms.material.assigned_bins.forEach(binId => payload.append('assigned_bins', binId));
                    }
                    if (this.selectedFile) payload.append('image', this.selectedFile);
                } 
                else if (type === 'stock_entry') {
                    url = '/api/moves/';
                    const f = this.forms.stock_entry;
                    const items = f.receipt_type === 'PURCHASE' ? f.items : [{ material_id: f.material_id, quantity: f.quantity, unit_cost: f.unit_cost }];
                    payload = JSON.stringify({
                        move_type: f.receipt_type === 'TRANSFER' ? 'TRANSFER' : 'IN',
                        opco: this.activeOpcoId, 
                        receipt_type: f.receipt_type,
                        reference: f.so_ref || f.production_ref || "MANUAL",
                        dest_bin: f.bin_id || null,
                        items: items.map(i => ({ material_id: i.material_id, quantity: parseFloat(i.quantity), unit_cost: parseFloat(i.unit_cost) }))
                    });
                } 
                else {
                    payload = JSON.stringify(this.forms[type]);
                }

                const headers = { 'X-CSRFToken': csrftoken };
                if (!(payload instanceof FormData)) headers['Content-Type'] = 'application/json';
                
                const response = await fetch(url, { method, headers, body: payload });
                if (response.ok) {
                    this.showModal = false;
                    await this.refreshAllData();
                    alert(this.isArabic ? "تم الحفظ بنجاح" : "Saved successfully");
                }
            } catch (error) { console.error("Submit Error:", error); }
        },

        editMaterial(item) { 
            itemMasterModule.methods.editMaterial(item, this); 
        },
        async fetchMaterials() {
            try {
                const res = await fetch('/api/materials/');
                if (res.ok) {
                    const data = await res.json();
                    this.materials_list = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) { console.error("Materials Fetch Error", e); }
        },
        // أضف هذه الدالة داخل قسم methods في ملف main.js
        getBinLocationName(binId) {
            // البحث عن الرف (bin) أولاً
            const bin = this.bins.find(b => b.id === binId);
            if (!bin) return '...';

            // البحث عن الموقع (location) المرتبط بهذا الرف
            const loc = this.locations.find(l => l.id === bin.storage_location);
            return loc ? loc.name : '...';
        },
        // دالة شاملة للتعامل مع أي عملية تعديل من أي واجهة

        async refreshAllData() {
            this.loading = true;
            try {
                // تم دمج جميع الطلبات في دالة واحدة لضمان التزامن
                await Promise.all([
                    this.fetchAll(), 
                    this.fetchDashboardData(), 
                    this.getListData(), 
                    this.fetchWMSStats(),
                    this.fetchMaterials() 
                ]);
            } finally {
                this.loading = false;
            }
        },

        async checkAuth() {
            try {
                const res = await fetch('/api/check-auth/');
                const data = await res.json();
                if (!data.authenticated) { window.location.href = "/"; } 
                else {
                    this.user = { name: data.user, is_superuser: data.is_superuser, role: 'Admin' };
                    this.config.company_name = data.company;
                    await this.refreshAllData();
                    this.triggerReadySystem();
                }
            } catch (e) { console.error("Auth Error", e); }
        },

        async fetchAll() {
            try {
                // جلب البيانات الأساسية للهيكل
                const endpoints = ['opcos', 'plants', 'locations', 'bins'];
                const results = await Promise.all(endpoints.map(e => fetch(`/api/${e}/`).then(r => r.json())));
                this.opcos = results[0];
                this.plants = results[1];
                this.locations = results[2];
                this.bins = results[3];
            } catch (e) { console.error("Core Data Error", e); }
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
                const res = await fetch('/api/wms/stats/');
                if (res.ok) this.wms_stats = await res.json();
            } catch (e) { console.error("Stats Error", e); }
        },

        async fetchDashboardData() {
            try {
                const res = await fetch('/api/dashboard-data/');
                const data = await res.json();
                if(data.kpis) this.kpis = data.kpis;
            } catch (e) { console.log("KPI fetch error"); }
        },

        openModal(type) {
            this.isEditing = false;
            this.modalType = type;
            this.showModal = true;
            this.imagePreview = null;
            this.selectedFile = null;

            if(type === 'plant') this.forms.plant = { id: null, opco: this.activeOpcoId, code: '', name: '' };
            else if(type === 'location') this.forms.location = { id: null, plant: this.activePlantId, code: '', name: '' };
            else if(type === 'bin') this.forms.bin = { id: null, storage_location: this.activeLocationId, code: '' };
            else if(type === 'material') {
                this.forms.material = { id: null, sku: '', name: '', base_uom: 'PCS', opco: this.activeOpcoId, assigned_bins: [] };
            }
            else if(type === 'stock_entry') {
                this.forms.stock_entry = { 
                    receipt_type: 'PURCHASE', items: [{ material_id: '', quantity: 1, unit_cost: 0 }],
                    target_plant: this.activePlantId || '', bin_id: '', quantity: 1
                };
            }
        }
    },
    mounted() {
        this.checkAuth();
        this.startClock();
    }
}).mount('#app');