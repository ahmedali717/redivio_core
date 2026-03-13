import { utils } from './modules/utils.js';
import { inventoryModule } from './modules/inventory.js';
import { orgModule } from './modules/org_builder.js';
import { itemMasterModule } from './modules/itemMaster.js';

const { createApp } = Vue;

createApp({
    delimiters: ['[[', ']]'],
    data() {
        return {
            // 🚀 ضيف المتغير ده هنا في أول سطر
            activeOperation: null,
            
            // 1. جعل الموديول الموحد هو الشاشة الافتراضية (اختياري)
            view: 'inventory_module', 
            
            // 🚀 إضافة المتغير الجديد للتبديل بين الأصناف والأرصدة
            inventoryTab: 'levels', 

            loading: false, 
            sidebarCollapsed: false,
            isArabic: true,
            isEditing: false,
            isAdvancedMode: false,
            
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
                    { id: 'inventory_module', name: { ar: 'إدارة المستودعات', en: 'Inventory WMS' }, icon: 'fas fa-boxes-stacked' }
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

            kpis: { 
                materials: 0,         // عدد الأصناف
                total_stock_value: 0,  // إجمالي قيمة المخزون
                low_stock_count: 0,    // أصناف تحت حد الطلب
                active_bins: 0,        // الرفوف المستغلة
                stock_qty: 0,          // إجمالي القطع
                pending_pos: 0         // المشتريات المعلقة
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
                opco: { ar: 'إضافة شركة تابعة / مشغلة', en: 'Add Subsidiary / OpCo' }
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
                    // 🚀 الهيكل الجديد لدعم تعدد الشركات
                    company_assignments: [
                        { opco_id: null, bins: [], primary_bin: null } 
                    ],
                    tracking: 'none', 
                    reorder_level: 0, 
                    max_level: 0 
                }
            }
        };
    },

    computed: {
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
            // تهيئة الفورم عند فتح عملية جديدة
            if (!this.forms.stock_entry) {
                this.forms.stock_entry = { items: [], po_id: '' };
            } else {
                this.forms.stock_entry.items = [];
                this.forms.stock_entry.po_id = '';
            }
        },
        
        goBackToOperations() {
            this.activeOperation = null;
        },

        // 🚀 إضافة اللوجيك الذكي لجلب الـ PO وتحديد الرف بناءً على الشركة
        async fetchPODetails() {
            const poId = this.forms.stock_entry.po_id;
            if (!poId) return;

            try {
                this.loading = true;
                // افتراضاً هذا هو رابط الـ API
                const res = await fetch(`/api/purchase-orders/${poId}/`);
                const data = await res.json();
                
                const currentOpcoId = parseInt(this.activeOpcoId);

                this.forms.stock_entry.items = data.items.map(i => {
                    const material = this.materials_list.find(m => m.id === i.material);
                    let autoSelectedBin = '';

                    // اللوجيك الذكي للبحث عن الرف للشركة المحددة
                    if (material && material.company_assignments) {
                        const assignment = material.company_assignments.find(a => parseInt(a.opco_id) === currentOpcoId);
                        if (assignment) {
                            autoSelectedBin = assignment.primary_bin || (assignment.bins.length > 0 ? assignment.bins[0] : '');
                        }
                    }

                    return {
                        material_id: i.material,
                        material_name: i.material_name || material?.name || 'Unknown',
                        sku: i.sku || material?.sku || 'N/A',
                        ordered_qty: i.quantity,
                        received_qty: i.quantity, 
                        bin_id: autoSelectedBin 
                    };
                });

                if (this.forms.stock_entry.items.some(i => i.bin_id)) {
                    this.showToast(this.isArabic ? "تم تحديد الرفوف المخصصة لشركتك تلقائياً" : "Bins auto-assigned based on your OpCo", 'success');
                }

            } catch (e) {
                console.error(e);
                this.showToast(this.isArabic ? "خطأ في جلب أمر التوريد" : "Error fetching PO details", 'error');
            } finally {
                this.loading = false;
            }
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
            
            // 3. تحديد الرابط ونوع الطلب (PATCH للتعديل و POST للإضافة)
            let url = isEdit ? `/api/${type}s/${id}/` : `/api/${type}s/`;
            let method = isEdit ? 'PATCH' : 'POST'; 
            const csrftoken = this.getCookie('csrftoken');

            try {
                this.loading = true;
                let payload;
                let headers = { 'X-CSRFToken': csrftoken };

                // 4. الأصناف والشركات تحتاج FormData لدعم رفع الصور (Image/Logo)
                const useFormData = (type === 'material' || type === 'opco');

                // ابحث عن السطر الذي يبدأ بـ if (useFormData) داخل submitForm
                if (useFormData) {
                    payload = new FormData();
                    const data = this.forms[type];
                    
                    Object.keys(data).forEach(key => {
                        if (type === 'material' && key === 'company_assignments') {
                            // 🚀 تحويل المصفوفة لنص JSON (ضروري جداً لنجاح json.loads في بايثون)
                            // قمنا بإضافة فلترة بسيطة لضمان عدم إرسال أسطر "فارغة" بدون شركة مختارة
                            const validAssignments = data[key].filter(assign => assign.opco_id);
                            payload.append('company_assignments', JSON.stringify(validAssignments));
                        } 
                        // 🛡️ منع إرسال الحقول القديمة (assigned_bins) لأننا استبدلناها بـ company_assignments
                        else if (data[key] !== null && !['logo', 'image', 'assigned_bins', 'primary_bin', 'company_assignments'].includes(key)) {
                            let val = data[key];
                            // تحويل البوليان لنص يفهمه بايثون
                            if (typeof val === 'boolean') val = val ? 'true' : 'false';
                            payload.append(key, val);
                        }
                    });

                    // 📸 إرفاق الصورة أو اللوجو
                    if (this.selectedFile) {
                        const fileKey = (type === 'material') ? 'image' : 'logo';
                        payload.append(fileKey, this.selectedFile);
                    }
                }

                // 6. تنفيذ طلب الـ Fetch
                const response = await fetch(url, {
                    method: method,
                    headers: headers,
                    body: payload
                });

                const contentType = response.headers.get("content-type");

                if (response.ok) {
                    // نجاح العملية
                    if (contentType && contentType.includes("application/json")) {
                        await response.json();
                    }
                    this.showModal = false;
                    this.selectedFile = null;
                    this.imagePreview = null;
                    
                    // تحديث كافة البيانات في الواجهة لتعكس التغييرات
                    await this.refreshAllData();
                    
                    this.showToast(
                        this.isArabic ? "تم حفظ البيانات بنجاح" : "Data saved successfully", 
                        'success'
                    );
                } else {
                    // معالجة أخطاء السيرفر
                    const errorResponse = await response.text();
                    console.error("Server Error:", errorResponse);

                    if (errorResponse.includes("<!DOCTYPE")) {
                        let errWindow = window.open("", "_blank");
                        errWindow.document.write(errorResponse);
                        errWindow.document.close();
                        this.showToast(this.isArabic ? "خطأ في السيرفر! راجع النافذة الجديدة." : "Server Error! Check the new tab.", 'error');
                    } else {
                        this.showToast(this.isArabic ? "فشل الحفظ: " + errorResponse : "Save failed: " + errorResponse, 'error');
                    }
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
                    this.fetchMaterialsList() 
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
                    // تحديث قيم الـ KPIs من بيانات الـ WMS
                    this.kpis.total_stock_value = this.wms_stats.total_value;
                    this.kpis.low_stock_count = this.wms_stats.low_stock;
                }
            } catch (e) { console.error("Stats Error", e); }
        },

        async fetchDashboardData() {
            try {
                const res = await fetch('/api/dashboard-data/');
                const data = await res.json();
                if(data.kpis) this.kpis = data.kpis;
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

        openModal(type, data = null) {
            this.isEditing = false;
            this.modalType = type;
            this.materialTab = 'general';
            this.showModal = true;
            this.imagePreview = null;
            this.selectedFile = null;

            if (type === 'plant') this.forms.plant = { id: null, opco: this.activeOpcoId, code: '', name: '' };
            else if (type === 'location') this.forms.location = { id: null, plant: this.activePlantId, code: '', name: '' };
            else if (type === 'bin') this.forms.bin = { id: null, storage_location: this.activeLocationId, code: '' };
            else if (type === 'material') {
                this.forms.material = {
                    id: null, 
                    sku: '', 
                    name: '', 
                    category: '', 
                    base_uom: 'PCS', 
                    barcode: '', 
                    // 🚀 التحديث هنا: تهيئة المصفوفة الجديدة بدلاً من الحقل القديم
                    company_assignments: [
                        { 
                            opco_id: this.activeOpcoId, // تعيين الشركة النشطة حالياً كخيار افتراضي
                            bins: [], 
                            primary_bin: null 
                        }
                    ],
                    tracking: 'none', 
                    reorder_level: 0, 
                    max_level: 0 
                };
            }
            else if (type === 'stock_entry') {
                this.forms.stock_entry = { 
                    receipt_type: 'PURCHASE', 
                    items: [{ material_id: '', quantity: 1, unit_cost: 0 }],
                    target_plant: this.activePlantId || '', 
                    bin_id: '', 
                    quantity: 1
                };
            }
            else if (type === 'opco') {
                this.forms.opco = { 
                    id: null, 
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