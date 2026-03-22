export const inventoryModule = {
    state: {
        inventoryList: [],
        inventoryMoves: [], // تأكد إن الاسم ده هو الموحد في كل مكان
        itemLogs: [],
        selectedItem: null,
        reportFilters: {
            material_id: '',
            location_id: '',
            date_from: '',
            date_to: ''
        },
        forms: {
            stock_entry: { 
                receipt_type: 'PURCHASE', 
                items: [{ material_id: '', quantity: 1, unit_cost: 0 }],
                target_plant: '', 
                target_location: ''
            }
        }
    },

    methods: {
        // الدالة الموحدة لجلب التقارير (بدون تمرير context معقد)
        async generateItemReport(instance) {
            const target = instance || this; // عشان يشتغل سواء من داخل الموديول أو من main.js
            
            if (!target.reportFilters.material_id) {
                target.showToast(target.isArabic ? "برجاء اختيار الصنف" : "Select Material", "error");
                return;
            }

            target.loading = true;
            try {
                // توحيد الرابط مع الـ Backend
                const query = new URLSearchParams({
                    material: target.reportFilters.material_id,
                    location: target.reportFilters.location_id,
                    from: target.reportFilters.date_from,
                    to: target.reportFilters.date_to
                }).toString();

                const res = await fetch(`/api/wms/moves/?${query}`);
                if (res.ok) {
                    const data = await res.json();
                    // تحديث المصفوفة اللي الجدول بيقرأ منها
                    target.inventoryMoves = Array.isArray(data) ? data : (data.results || []);
                    target.showToast(target.isArabic ? "تم تحديث البيانات" : "Data Updated", "success");
                }
            } catch (e) {
                console.error("Report Fetch Error:", e);
            } finally {
                target.loading = false;
            }
        },

        addItemRow(instance) {
            const target = instance || this;
            target.forms.stock_entry.items.push({ material_id: '', quantity: 1, unit_cost: 0 });
        }
    }
};