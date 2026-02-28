export const configModule = {
    state: {
        config: { 
            company_name: 'REDIVIO ERP', // قيمة افتراضية
            is_holding: false, 
            tax_id: '', 
            cr_number: '' 
        },
        licenseStatus: { 
            companyName: '', 
            daysRemaining: 15, 
            todayStr: new Date().toLocaleDateString(), // يقرأ تاريخ اليوم فوراً
            createdStr: '2024-05-20' // التاريخ الذي بدأت فيه المنشأة
        }
    },
    methods: {
        updateConfig(newData) {
            Object.assign(this.config, newData);
        },
        calculateLicense(createdDateStr) {
            const created = new Date(createdDateStr);
            const today = new Date();
            
            // حساب الفرق بالأيام
            const diffTime = today - created;
            const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
            
            // حساب المتبقي من 15 يوم (مع ضمان عدم النزول عن الصفر)
            const remaining = 15 - diffDays;
            this.licenseStatus.daysRemaining = remaining > 0 ? remaining : 0;
            
            // تحديث التاريخ للعرض في الكرت
            this.licenseStatus.todayStr = today.toLocaleDateString();
        }
    }
};