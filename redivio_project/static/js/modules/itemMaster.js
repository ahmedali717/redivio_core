/**
 * 🚀 موديول رئيس الأصناف (Item Master Module) - النسخة الاحترافية المحدثة
 * متوافق مع نظام تعدد الشركات و Putaway Rules
 */
export const itemMasterModule = {
    state: {
        isAdvancedMode: false,
        materialTab: 'general',
        materials_list: [],
        imagePreview: null,
        selectedFile: null,
        forms: {
            material: { 
                id: null, 
                sku: '', 
                name: '', 
                category: '', 
                base_uom: 'PCS', 
                barcode: '', 
                // 🚀 الهيكل الجديد والموحد
                company_assignments: [
                    { opco_id: null, bins: [], primary_bin: null }
                ],
                tracking: 'none',
                weight: 0,
                volume: 0,
                reorder_level: 0,
                max_level: 0,
                standard_price: 0,
                sales_price: 0,
                tax_rate: 15,
                // 🚀 POS & Recipe extensions
                is_pos_item: false,
                is_combo: false,
                sale_group: '',
                expiry_date: null,
                recipe_lines: [],
                combo_lines: []
            }
        }
    },

    methods: {
        addRecipeLine(instance) {
            if (!instance.forms.material.recipe_lines) {
                instance.forms.material.recipe_lines = [];
            }
            instance.forms.material.recipe_lines.push({
                ingredient_id: '',
                quantity: 1,
                uom: 'KG'
            });
        },

        addComboLine(instance) {
            if (!instance.forms.material.combo_lines) {
                instance.forms.material.combo_lines = [];
            }
            instance.forms.material.combo_lines.push({
                item_id: '',
                quantity: 1,
                extra_price: 0
            });
        },

        handleImageUpload(event, instance) {
            const file = event.target.files[0];
            if (file) {
                if (file.size > 2 * 1024 * 1024) { 
                    instance.showToast(instance.isArabic ? "حجم الصورة كبير جداً (الأقصى 2MB)!" : "File too large!", 'error');
                    return;
                }
                instance.selectedFile = file;
                instance.imagePreview = URL.createObjectURL(file); 
            }
        },

        /**
         * ⭐️ تعيين الرف كـ Primary داخل سطر شركة محدد
         */
        setPrimaryBinInRow(rowIndex, binId, instance) {
            const row = instance.forms.material.company_assignments[rowIndex];
            row.primary_bin = binId;
            // ضمان إضافة الرف للقائمة المختارة داخل هذا السطر
            if (!row.bins.includes(binId)) {
                row.bins.push(binId);
            }
            instance.showToast(instance.isArabic ? "تم تحديد الرف كوجهة افتراضية" : "Primary bin set", 'success');
        },

        /**
         * ✅ تبديل اختيار الرف داخل سطر شركة محدد
         */
        toggleBinInRow(rowIndex, binId, instance) {
            const row = instance.forms.material.company_assignments[rowIndex];
            const index = row.bins.indexOf(binId);
            if (index > -1) {
                if (row.primary_bin === binId) row.primary_bin = null;
                row.bins.splice(index, 1);
            } else {
                row.bins.push(binId);
            }
        },

        /**
         * 📝 تحضير بيانات الصنف للتعديل (التحول الجوهري)
         * نستخدم هنا البيانات الموحدة القادمة من السيريالايزر الجديد
         */
        editMaterial(material, instance) {
            if (!instance) return;

            instance.isEditing = true;
            instance.modalType = 'material';
            instance.materialTab = 'general';
            instance.showModal = true;
            
            // تحويل البيانات القادمة من السيرفر للهيكل الجديد
            instance.forms.material = {
                id: material.id,
                sku: material.sku,
                name: material.name,
                category: material.category,
                base_uom: material.base_uom,
                barcode: material.barcode || '',
                
                // 🚀 سحب مصفوفة الربط المجهزة من السيريالايزر (get_company_assignments)
                company_assignments: material.company_assignments && material.company_assignments.length > 0 
                    ? JSON.parse(JSON.stringify(material.company_assignments))
                    : [{ opco_id: material.opco, bins: material.storage_locations_ids || [], primary_bin: material.current_primary_bin || null }],
                
                tracking: material.tracking || 'none',
                standard_price: material.standard_price || 0,
                sales_price: material.sales_price || 0,
                tax_rate: material.tax_rate || 15,
                weight: material.weight || 0,
                volume: material.volume || 0,
                reorder_level: material.reorder_level || 0,
                max_level: material.max_level || 0,

                // 🚀 POS & Recipe & Combo
                is_pos_item: material.is_pos_item || false,
                is_combo: material.is_combo || false,
                sale_group: material.sale_group || '',
                expiry_date: material.expiry_date || null,
                recipe_lines: material.recipe_lines || [],
                combo_lines: material.combo_lines || [],
                
                // 🚀 البيانات الجديدة لعرض الأرصدة (Odoo 19 Modal)
                on_hand: material.on_hand || 0,
                stock_details: material.stock_details || []
            };
            
            instance.imagePreview = instance.fixImagePath(material.image); 
            instance.selectedFile = null;
        }
    }
};