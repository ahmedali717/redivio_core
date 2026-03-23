export const inventoryModule = {
    // الـ State الموحد
    state: {
        inventoryList: [],
        inventoryMoves: [], // الاسم الموحد الذي يقرأ منه الجدول في HTML
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
        /**
         * الدالة الموحدة لجلب التقارير
         * تم تصحيح أسماء المعاملات لتطابق Django Backend (views.py)
         */
        async generateItemReport() {
            // التحقق من اختيار الصنف
            if (!this.reportFilters.material_id) {
                this.showToast(this.isArabic ? "برجاء اختيار الصنف أولاً" : "Select material first", "error");
                return;
            }

            this.loading = true;
            try {
                // 1. توحيد المعاملات مع ما ينتظره السيرفر في views.py
                const params = new URLSearchParams({
                    material_id: this.reportFilters.material_id, // كان "material" وتم تصحيحه
                    location_id: this.reportFilters.location_id, // كان "location" وتم تصحيحه
                    date_from: this.reportFilters.date_from,     // كان "from" وتم تصحيحه
                    date_to: this.reportFilters.date_to          // كان "to" وتم تصحيحه
                }).toString();

                // 2. طلب البيانات من الرابط الصحيح
                const res = await fetch(`/api/wms/moves/?${params}`);
                
                if (res.ok) {
                    const data = await res.json();
                    
                    // 3. تحديث المصفوفة ودعم الـ Pagination إذا وجد
                    this.inventoryMoves = Array.isArray(data) ? data : (data.results || []);
                    
                    // 4. رسالة توضيحية للمستخدم
                    if (this.inventoryMoves.length === 0) {
                        this.showToast(this.isArabic ? "لا توجد حركات لهذا الصنف" : "No movements found", "info");
                    } else {
                        this.showToast(this.isArabic ? "تم تحديث البيانات" : "Data Updated", "success");
                    }
                } else {
                    throw new Error("Server Response Error");
                }
            } catch (e) {
                console.error("Report Fetch Error:", e);
                this.showToast(this.isArabic ? "خطأ في جلب البيانات" : "Error fetching data", "error");
            } finally {
                this.loading = false;
            }
        },

        /**
         * إضافة سطر جديد في نموذج الاستلام المخزني
         */
        addItemRow() {
            // الوصول المباشر عبر this لأن الموديول مدمج في الـ App
            if (this.forms && this.forms.stock_entry) {
                this.forms.stock_entry.items.push({ 
                    material_id: '', 
                    quantity: 1, 
                    unit_cost: 0 
                });
            }
        }
    }
};