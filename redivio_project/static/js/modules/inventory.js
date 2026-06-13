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
                target_location: '',
                transfer_material: '',
                transfer_source_bin: '',
                transfer_dest_bin: '',
                transfer_quantity: 1
            }
        }
    },

    methods: {
        async submitInternalTransfer(instance) {
            const entry = instance.forms.stock_entry;
            if (!entry.transfer_material) {
                instance.showToast(instance.isArabic ? "برجاء اختيار الصنف أولاً" : "Please select a material first", "error");
                return;
            }
            if (!entry.transfer_source_bin) {
                instance.showToast(instance.isArabic ? "برجاء اختيار الرف المصدر" : "Please select the source bin", "error");
                return;
            }
            if (!entry.transfer_dest_bin) {
                instance.showToast(instance.isArabic ? "برجاء اختيار الرف الوجهة" : "Please select the destination bin", "error");
                return;
            }
            if (String(entry.transfer_source_bin) === String(entry.transfer_dest_bin)) {
                instance.showToast(instance.isArabic ? "الرف المصدر لا يمكن أن يكون هو نفسه الرف الوجهة" : "Source and destination bin cannot be the same", "error");
                return;
            }
            const qty = parseFloat(entry.transfer_quantity);
            if (isNaN(qty) || qty <= 0) {
                instance.showToast(instance.isArabic ? "الرجاء إدخال كمية صالحة أكبر من الصفر" : "Please enter a valid quantity greater than zero", "error");
                return;
            }

            try {
                instance.loading = true;
                const payload = {
                    material: entry.transfer_material,
                    source_bin: entry.transfer_source_bin,
                    dest_bin: entry.transfer_dest_bin,
                    quantity: qty,
                    reference: entry.reference || (instance.isArabic ? "تحويل مخزني داخلي" : "Internal Stock Transfer")
                };

                const response = await fetch('/api/wms/moves/internal_transfer/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': instance.getCookie('csrftoken')
                    },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    instance.showModal = false;
                    // Reset fields
                    entry.transfer_material = '';
                    entry.transfer_source_bin = '';
                    entry.transfer_dest_bin = '';
                    entry.transfer_quantity = 1;
                    entry.reference = '';
                    
                    await instance.refreshAllData();
                    instance.showToast(instance.isArabic ? "تم تحويل المخزون بنجاح" : "Stock transferred successfully", "success");
                } else {
                    const err = await response.json();
                    instance.showToast(err.error || (instance.isArabic ? "فشل تحويل المخزون" : "Transfer failed"), "error");
                }
            } catch (e) {
                console.error("Internal transfer error:", e);
                instance.showToast(instance.isArabic ? "حدث خطأ أثناء الاتصال بالسيرفر" : "Network error", "error");
            } finally {
                instance.loading = false;
            }
        },
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