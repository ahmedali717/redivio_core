/**
 * موديول رئيس الأصناف (Item Master Module)
 * مسؤول عن: تعريف الأصناف، رفع الصور، وإدارة البيانات الأساسية.
 */
export const itemMasterModule = {
    state: {
        materials_list: [],       // قائمة الأصناف المعرفة (Item Master)
        imagePreview: null,       // معاينة الصورة قبل الحفظ
        selectedFile: null,       // الملف الفعلي للرفع
        forms: {
            material: { 
                id: null, 
                sku: '', 
                name: '', 
                category: '', 
                base_uom: 'PCS', 
                barcode: '', 
                assigned_bins: [], 
                opco: null 
            }
        }
    },

    methods: {
        /**
         * معالجة رفع ومعاينة صورة الصنف مع التحقق من الحجم
         */
        handleImageUpload(event, instance) {
            const file = event.target.files[0];
            if (file) {
                if (file.size > 2 * 1024 * 1024) { 
                    alert("حجم الصورة كبير جداً (الأقصى 2MB)!");
                    return;
                }
                instance.selectedFile = file;
                instance.imagePreview = URL.createObjectURL(file); 
            }
        },

        /**
         * تحضير بيانات صنف موجود للتعديل (Edit Mode)
         */
        editMaterial(material, instance) {
    if (!instance) {
        console.error("Vue instance is missing in editMaterial!");
        return;
    }
    instance.isEditing = true;
    instance.modalType = 'material';
    instance.showModal = true;
    
    instance.forms.material = {
        id: material.id,
        sku: material.sku,
        name: material.name,
        category: material.category,
        base_uom: material.base_uom,
        barcode: material.barcode || '',
        opco: (typeof material.opco === 'object') ? material.opco.id : material.opco,
        assigned_bins: material.assigned_bins || []
    };
    
    // استخدام fixImagePath لضمان ظهور الصورة في المودال
    instance.imagePreview = instance.fixImagePath(material.image); 
    instance.selectedFile = null;
}
    }
};