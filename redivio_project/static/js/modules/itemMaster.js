/**
 * 🚀 موديول رئيس الأصناف (Item Master Module) - النسخة الاحترافية
 * متوافق مع نظام Odoo 19 Enterprise
 */
export const itemMasterModule = {
    state: {
        isAdvancedMode: false,    // التبديل بين Plug & Play و Advanced
        materialTab: 'general',   // التبويب النشط (General | Inventory)
        materials_list: [],       // قائمة الأصناف
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
                opco: null,
                // حقول الـ Putaway Rules
                assigned_bins: [], 
                primary_bin: null,
                // حقول الـ Advanced Mode
                tracking: 'none',
                weight: 0,
                volume: 0,
                reorder_level: 0,
                max_level: 0
            }
        }
    },

    methods: {
        /**
         * 🖼️ معالجة رفع ومعاينة صورة الصنف
         */
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
         * ⭐️ تعيين الرف كـ Primary (Putaway Rule)
         */
        setPrimaryBin(binId, instance) {
            instance.forms.material.primary_bin = binId;
            // ضمان إضافة الرف للقائمة المختارة إذا لم يكن موجوداً
            if (!instance.forms.material.assigned_bins.includes(binId)) {
                instance.forms.material.assigned_bins.push(binId);
            }
            instance.showToast(instance.isArabic ? "تم تحديد الرف كوجهة افتراضية" : "Primary bin set", 'success');
        },

        /**
         * ✅ تبديل اختيار الرف (Toggle Bin)
         */
        toggleBinSelection(binId, instance) {
            const index = instance.forms.material.assigned_bins.indexOf(binId);
            if (index > -1) {
                // لو لغى اختيار الرف وكان هو الـ Primary، امسح الـ Primary أيضاً
                if (instance.forms.material.primary_bin === binId) {
                    instance.forms.material.primary_bin = null;
                }
                instance.forms.material.assigned_bins.splice(index, 1);
            } else {
                instance.forms.material.assigned_bins.push(binId);
            }
        },

        /**
         * 📝 تحضير بيانات الصنف للتعديل (التحول الجوهري)
         * نضمن هنا ظهور كل البيانات المحفوظة بما فيها النجمة والرفوف
         */
        editMaterial(material, instance) {
            if (!instance) return;

            instance.isEditing = true;
            instance.modalType = 'material';
            instance.materialTab = 'general';
            instance.showModal = true;
            
            // ربط البيانات بالنموذج (بما في ذلك حقول القراءة من السيريالايزر)
            instance.forms.material = {
                id: material.id,
                sku: material.sku,
                name: material.name,
                category: material.category,
                base_uom: material.base_uom,
                barcode: material.barcode || '',
                opco: (typeof material.opco === 'object') ? material.opco.id : material.opco,
                
                // 🚀 استرجاع الرفوف والنجمة من حقول القراءة المخصصة
                assigned_bins: material.storage_locations_ids || [], 
                primary_bin: material.current_primary_bin || null,
                
                // استرجاع حقول الـ Advanced
                tracking: material.tracking || 'none',
                weight: material.weight || 0,
                volume: material.volume || 0,
                reorder_level: material.reorder_level || 0,
                max_level: material.max_level || 0
            };
            
            // معاينة الصورة
            instance.imagePreview = instance.fixImagePath(material.image); 
            instance.selectedFile = null;
        }
    }
};