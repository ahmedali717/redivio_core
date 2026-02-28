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

            // دمج الحالات من الموديولات
            ...(utils.state || {}),
            ...(inventoryModule.state || {}),
            
            user: { name: '...', role: '...', is_superuser: false },
            
            // كائن الإعدادات (Data Model for Global Config)
            config: { 
                company_name: '', 
                is_holding: false,
                tax_id: '',
                cr_number: '',
                created_at: null,
                logo: null 
            },

            license: {
                days_limit: 15,
                sku_limit: 50
            },

            kpis: { materials: 0, stock_qty: 0, vendors: 0, pending_pos: 0 },
            
            opcos: [], 
            subsidiaries: [], 
            plants: [], 
            locations: [], 
            bins: [],
            materials_list: [], 
            inventoryList: [],
            wms_stats: {},

            showModal: false, 
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
                opco: { ar: 'إضافة شركة تابعة / مشغلة', en: 'Add Subsidiary / OpCo' }
            },

            forms: {
                ...(inventoryModule.state?.forms || {}),
                opco: { id: null, code: '', name: '', currency: 'USD', parent: null, is_holding: false },
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
        currentSubsidiaries() {
    if (!this.activeOpcoId) return [];
    
    return this.opcos.filter(o => {
        // 1. استخراج قيمة الأب (سواء كانت Object أو ID مباشر)
        const rawParent = (o.parent && typeof o.parent === 'object') ? o.parent.id : o.parent;
        
        // 2. إذا لم يكن هناك أب أصلاً، استبعد هذه الشركة فوراً
        if (rawParent === null || rawParent === undefined) return false;

        // 3. المقارنة بعد التأكد من أن الطرفين أرقام صحيحة
        return parseInt(rawParent) === parseInt(this.activeOpcoId);
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
            let active = this.opcos.find(o => o.id === parseInt(this.activeOpcoId));
            
            if (!active && this.opcos.length > 0) {
                active = this.opcos[0];
            }

            const rawDate = active ? (active.created_at || active.created_on) : null;
            let daysRemaining = 15;

            if (rawDate) {
                const createdDate = new Date(rawDate);
                const diffDays = Math.floor((new Date() - createdDate) / (1000 * 60 * 60 * 24));
                daysRemaining = Math.max(15 - diffDays, 0);
            }

            return {
                daysRemaining: daysRemaining,
                companyName: active ? active.name : 'ERP System',
                createdAt: rawDate 
            };
        }
    },

    watch: {
        activeOpcoId(newId) {
            if (newId) this.syncGlobalConfig(newId);
        }
    },

    methods: {
        ...utils.methods,
        ...itemMasterModule.methods,
        // دالة لتصحيح المسار (أضفها ضمن الـ methods)
fixImagePath(path) {
    if (!path) return null;
    // إذا كان الرابط يحتوي على localhost، نحذفه ونأخذ المسار الذي يبدأ بـ /media/
    if (path.includes('localhost') || path.includes('127.0.0.1')) {
        const parts = path.split('/media/');
        return '/media/' + parts[1];
    }
    // إذا كان المسار لا يبدأ بـ / أضفها له
    if (!path.startsWith('http') && !path.startsWith('/')) {
        return '/' + path;
    }
    return path;
},

        syncGlobalConfig(opcoId) {
    if (!opcoId || this.opcos.length === 0) return;

    const active = this.opcos.find(o => o.id === parseInt(opcoId));
    if (active) {
        // نستخدم دالة fixImagePath لضمان إزالة localhost وإضافة السلاش
        const finalLogo = this.fixImagePath(active.logo);

        this.config = {
            company_name: active.name || '',
            is_holding: !!active.is_holding,
            tax_id: active.tax_id || '',
            cr_number: active.cr_number || '',
            logo: finalLogo // تم التصحيح هنا
        };
        this.imagePreview = finalLogo; // تم التصحيح هنا
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
        // 1. تخزين الملف لإرساله للسيرفر عند الحفظ
        this.newLogoFile = file; 

        // 2. توليد رابط "معاينة" مؤقت للملف المرفوع الآن من الجهاز
        // نستخدم URL.createObjectURL لكي تظهر الصورة فوراً للمستخدم قبل الرفع
        const previewUrl = URL.createObjectURL(file);
        
        // 3. تحديث المعاينة في الواجهة
        this.imagePreview = previewUrl;
        this.config.logo = previewUrl;
    }
},

        async openItemCard(item) { await inventoryModule.methods.openItemCard(item, this); },
        addItemRow() { inventoryModule.methods.addItemRow(this); },
        removeItemRow(index) { inventoryModule.methods.removeItemRow(index, this); },
        async fetchSODetails() { await inventoryModule.methods.fetchSODetails(this); },
        onSOMaterialSelect() { inventoryModule.methods.onSOMaterialSelect(this); },

        getPlantsForOpco(id) { 
            return orgModule.methods.getPlantsForOpco(this, id); 
        },
        getLocationsForPlant(id) { 
            return orgModule.methods.getLocationsForPlant(this, id); 
        },
        getBinsForLocation(id) { 
            // التعديل: تمرير this أولاً ليتوافق مع تصميم الموديول
            return orgModule.methods.getBinsForLocation(this, id); 
        },
        getBinsCount(id) { 
            // التعديل: تمرير this أولاً
            return orgModule.methods.getBinsCount(this, id); 
        },
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
    if (this.view === 'global_config' && !this.showModal) {
        return await this.saveGlobalConfig();
    }
    const type = this.modalType;
    if (!type || !this.forms[type]) return;

    // --- بداية الجزء الجديد للتحقق من الـ Bin ---
    if (type === 'bin') {
        const binCode = this.forms.bin.code.trim().toUpperCase();
        
        // البحث في كل الـ bins المحملة عن كود مطابق
        const isDuplicate = this.bins.some(b => 
            b.code.trim().toUpperCase() === binCode && 
            b.id !== this.forms.bin.id // تجاهل السجل الحالي إذا كنا في وضع التعديل
        );

        if (isDuplicate) {
            alert(this.isArabic ? 
                `خطأ: كود الرف (${binCode}) مستخدم بالفعل في مكان آخر بالشركة!` : 
                `Error: Bin code (${binCode}) is already in use!`);
            return; // توقف عن إكمال عملية الحفظ
        }
    }

    const isEdit = this.isEditing;
    const id = this.forms[type].id;
    let url = isEdit ? `/api/${type}s/${id}/` : `/api/${type}s/`;
    let method = isEdit ? 'PUT' : 'POST';
    const csrftoken = this.getCookie('csrftoken');

    try {
        this.loading = true;
        let payload;

        // تعديل: استخدام FormData للـ opco أيضاً لدعم رفع الملفات وتجنب خطأ الـ logo
        if (type === 'material' || type === 'opco') {
            payload = new FormData();
            const data = this.forms[type];
            
            // إضافة كل الحقول للـ FormData
            Object.keys(data).forEach(key => {
                if (data[key] !== null && key !== 'logo') {
                    payload.append(key, data[key]);
                }
            });

            // إضافة الملف فقط إذا اختار المستخدم ملفاً جديداً
            if (this.selectedFile) {
                payload.append('logo', this.selectedFile);
            }
        } else {
            payload = JSON.stringify(this.forms[type]);
        }

        const response = await fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': csrftoken,
                // لا نضع Content-Type إذا كان payload هو FormData، المتصفح سيقوم بذلك تلقائياً
                ...(type !== 'material' && type !== 'opco' && { 'Content-Type': 'application/json' })
            },
            body: payload
        });

        if (response.ok) {
            this.showModal = false;
            this.selectedFile = null; // تنظيف الملف بعد الحفظ
            await this.refreshAllData();
            alert(this.isArabic ? "تم الحفظ بنجاح" : "Saved successfully");
        } else {
            const errorData = await response.json();
            console.error("خطأ من السيرفر:", errorData);
            alert(this.isArabic ? "فشل الحفظ: راجع بيانات الشعار أو الكود" : "Save failed: Check logo or code");
        }
    } catch (error) {
        console.error("Submit Error:", error);
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
        
        // 1. إرسال البيانات النصية
        formData.append('name', this.config.company_name); 
        formData.append('is_holding', this.config.is_holding ? 'true' : 'false');
        formData.append('tax_id', this.config.tax_id || '');
        formData.append('cr_number', this.config.cr_number || '');
        
        // 2. إرسال الكود (تأكد من إرسال الكود الحالي للشركة حتى لا يشتكي السيرفر)
        const activeOpco = this.opcos.find(o => o.id === parseInt(targetId));
        if (activeOpco) {
            formData.append('code', activeOpco.code); 
        }

        // 3. الحل الجذري لمشكلة الـ Logo:
        // لا نرسل حقل logo إلا إذا كان هناك ملف جديد (File Object)
        if (this.newLogoFile instanceof File) {
            formData.append('logo', this.newLogoFile);
        }
        // ملاحظة: إذا لم نضف حقل logo، سيحتفظ Django بالصورة القديمة تلقائياً

        const url = `/api/opcos/${targetId}/`; 

        const response = await fetch(url, {
            method: 'PATCH', // استخدام PATCH أفضل من PUT عند تعديل أجزاء من البيانات
            headers: { 'X-CSRFToken': this.getCookie('csrftoken') },
            body: formData
        });

        if (response.ok) {
            const data = await response.json();
            this.handleSaveSuccess(data);
        } else {
            const errorData = await response.json();
            console.error("تفاصيل الخطأ من السيرفر:", errorData);
            
            // إظهار تنبيه مفصل للمستخدم
            let msg = this.isArabic ? "فشل الحفظ:\n" : "Save Failed:\n";
            if(errorData.code) msg += `Code: ${errorData.code[0]}\n`;
            if(errorData.logo) msg += `Logo: ${errorData.logo[0]}\n`;
            alert(msg);
        }
    } catch (error) {
        console.error("Save Error:", error);
    } finally {
        this.loading = false;
    }
},

// دالة مساعدة لتحديث البيانات بعد النجاح
handleSaveSuccess(updatedData) {
    // 1. تصحيح مسار الشعار (Logo)
    let logoUrl = updatedData.logo;
    if (logoUrl && !logoUrl.startsWith('http') && !logoUrl.startsWith('/')) {
        logoUrl = '/' + logoUrl;
    }

    // 2. تحديث المصفوفة الكبيرة (opcos) - هذا هو مفتاح الحل للظهور الفوري
    const index = this.opcos.findIndex(o => o.id === updatedData.id);
    
    if (index !== -1) {
        // إذا كانت الشركة موجودة (تعديل)، نستخدم splice لضمان استجابة Vue (Reactivity)
        this.opcos.splice(index, 1, { ...updatedData, logo: logoUrl });
    } else {
        // إذا كانت شركة تابعة جديدة، نضيفها للمصفوفة
        this.opcos.push({ ...updatedData, logo: logoUrl });
    }

    // 3. تحديث بيانات العرض في شاشة الإعدادات (إذا كانت هي الشركة النشطة)
    if (parseInt(this.activeOpcoId) === parseInt(updatedData.id)) {
        this.config = {
            company_name: updatedData.name,
            is_holding: updatedData.is_holding,
            tax_id: updatedData.tax_id,
            cr_number: updatedData.cr_number,
            logo: logoUrl 
        };
        this.imagePreview = logoUrl;
    }

    // 4. تنظيف حالة الرفع
    this.newLogoFile = null;

    // 5. إشعار المستخدم
    alert(this.isArabic ? 'تم حفظ البيانات وظهورها بنجاح' : 'Data saved and updated successfully');
},

        async refreshAllData() {
    this.loading = true;
    try {
        await this.fetchAll(); 
        await Promise.all([
            this.fetchDashboardData(), 
            this.getListData(), 
            this.fetchWMSStats(),
            this.fetchMaterialsList() // تم التعديل للاسم الصحيح الموجود في ميثودز
        ]);
        if (this.activeOpcoId) this.syncGlobalConfig(this.activeOpcoId);
    } catch (e) {
        console.error("Error in refreshAllData:", e); // أضفنا catch لرؤية أي أخطاء أخرى
    } finally {
        this.loading = false;
    }
},

        async checkAuth() {
    try {
        const res = await fetch('/api/check-auth/');
        const data = await res.json();
        if (data.authenticated) {
            this.user = { name: data.user, is_superuser: data.is_superuser, role: 'Admin' };
            
            // أولاً: جلب كل البيانات الأساسية (opcos, plants...)
            await this.fetchAll(); 
            
            // ثانياً: ضبط المعرف النشط
            if (data.company_id) {
                this.activeOpcoId = data.company_id;
            } else if (this.opcos.length > 0) {
                this.activeOpcoId = this.opcos[0].id;
            }

            // ثالثاً: الآن المزامنة ستجد بيانات في opcos
            this.syncGlobalConfig(this.activeOpcoId);
            await this.refreshAllData();
        }
    } catch (e) { console.error("Auth Error", e); }
},

        async fetchAll() {
            try {
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

        openModal(type , data = null) {
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
            else if(type === 'opco') {
        this.forms.opco = { 
            id: null, 
            // استخدام البيانات القادمة من دالة handleDrop
            code: data ? data.code : '', 
            name: '', 
            currency: 'USD', 
            parent: data ? data.parent : (this.activeOpcoId || null), 
            is_holding: false 
        };
            }
        }
    },
    mounted() {
        this.checkAuth();
        this.startClock();
    }
}).mount('#app');