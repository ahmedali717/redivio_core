/**
 * موديول إدارة المخزون (Inventory Module)
 * مسؤول عن: أرصدة المستودعات، سجل الحركات، وأذونات الاستلام/التحويل.
 */
export const inventoryModule = {
    state: {
        inventoryList: [],        // أرصدة المخزون الحالية
        itemLogs: [],             // سجل حركات الصنف المختار
        selectedItem: null,       // الصنف النشط في بطاقة العرض
        targetLocations: [],      // المواقع المتاحة للوجهة
        targetBins: [],           // الأرفف المتاحة للوجهة
        sourceLocations: [],      // المواقع المتاحة للمصدر
        sourceBins: [],           // الأرفف المتاحة للمصدر
        forms: {
            stock_entry: { 
                receipt_type: 'PURCHASE', 
                items: [{ material_id: '', quantity: 1, unit_cost: 0 }],
                so_ref: '', 
                target_plant: '', 
                target_location: '', 
                src_plant: '', 
                src_location: '', 
                src_bin: ''
            }
        }
    },

    methods: {
        /**
         * فتح بطاقة الصنف وجلب سجل حركاته من الـ API
         */
        async openItemCard(item, context) {
            if (!item) return;
            
            const materialId = item.id || item.material_id; // دعم كلا الحقلين
            if (!materialId) return;

            context.selectedItem = item;
            context.showItemCard = true;
            context.loadingLogs = true;
            context.itemLogs = []; 

            try {
                // الفلترة باستخدام معرف الصنف الصحيح
                const url = `/api/moves/?material_id=${materialId}`; 
                const res = await fetch(url);
                
                if (res.ok) {
                    const data = await res.json();
                    context.itemLogs = Array.isArray(data) ? data : (data.results || []);
                }
            } catch (e) {
                console.error("Fetch error in inventory logs:", e);
            } finally {
                context.loadingLogs = false;
            }
        },

        addItemRow(instance) {
            instance.forms.stock_entry.items.push({ material_id: '', quantity: 1, unit_cost: 0 });
        },

        removeItemRow(index, instance) {
            if (instance.forms.stock_entry.items.length > 1) {
                instance.forms.stock_entry.items.splice(index, 1);
            }
        }
    }
};