/**
 * موديول إدارة المخازن (Inventory/WMS Module)
 * يتم دمجه في الـ App الرئيسي باستخدام ...inventoryModule.methods
 */
export const inventoryModule = {
    // 1. الحالة (State) - القيم الافتراضية
    state: {
        inventoryList: [],
        inventoryMoves: [], // المصفوفة الموحدة لعرض حركة الصنف
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

    // 2. الدوال (Methods)
    methods: {
        /**
         * دالة جلب تقرير "حركة صنف"
         * تعالج الفلاتر وترسلها للـ Backend بأسماء صحيحة
         */
        async generateItemReport() {
            // التحقق من أن المستخدم اختار صنفاً
            if (!this.reportFilters.material_id) {
                this.showToast(this.isArabic ? "برجاء اختيار الصنف أولاً" : "Select material first", "error");
                return;
            }

            this.loading = true;
            try {
                // بناء المعاملات (Query Params) - نقوم بإرسال القيم الموجودة فقط
                const queryObj = {};
                if (this.reportFilters.material_id) queryObj.material_id = this.reportFilters.material_id;
                if (this.reportFilters.location_id) queryObj.location_id = this.reportFilters.location_id;
                if (this.reportFilters.date_from)   queryObj.date_from   = this.reportFilters.date_from;
                if (this.reportFilters.date_to)     queryObj.date_to     = this.reportFilters.date_to;

                const params = new URLSearchParams(queryObj).toString();

                // استدعاء الـ API الخاص بـ StockMoveViewSet
                const res = await fetch(`/api/wms/moves/?${params}`);
                
                if (res.ok) {
                    const data = await res.json();
                    
                    // التعامل مع صيغ البيانات المختلفة (Array مباشرة أو نتائج Pagination)
                    this.inventoryMoves = Array.isArray(data) ? data : (data.results || []);
                    
                    // تنبيه المستخدم بالنتيجة
                    if (this.inventoryMoves.length === 0) {
                        this.showToast(this.isArabic ? "لا توجد حركات مسجلة لهذا الصنف" : "No movements found", "info");
                    } else {
                        const count = this.inventoryMoves.length;
                        this.showToast(this.isArabic ? `تم تحديث البيانات (${count} حركة)` : `Data Updated (${count} moves)`, "success");
                    }
                } else {
                    const errData = await res.text();
                    throw new Error(errData || "Server Error");
                }
            } catch (e) {
                console.error("Report Fetch Error:", e);
                this.showToast(this.isArabic ? "عذراً، فشل جلب بيانات التقرير" : "Failed to fetch report", "error");
            } finally {
                this.loading = false;
            }
        },

        /**
         * إضافة سطر جديد في نموذج الاستلام/الصرف
         */
        addItemRow() {
            // التأكد من أن الهيكل موجود لتجنب أخطاء undefined
            if (!this.forms.stock_entry) {
                this.forms.stock_entry = { items: [] };
            }
            if (!this.forms.stock_entry.items) {
                this.forms.stock_entry.items = [];
            }

            this.forms.stock_entry.items.push({ 
                material_id: '', 
                quantity: 1, 
                unit_cost: 0 
            });
        },

        /**
         * حذف سطر من نموذج الاستلام
         */
        removeItemRow(index) {
            if (this.forms.stock_entry.items.length > 1) {
                this.forms.stock_entry.items.splice(index, 1);
            } else {
                this.showToast(this.isArabic ? "يجب إدراج صنف واحد على الأقل" : "At least one item required", "info");
            }
        }
    }
};