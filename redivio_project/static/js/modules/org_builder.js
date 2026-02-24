/**
 * موديول بناء الهيكل التنظيمي (Org Builder Module)
 * مسؤول عن: الربط بين الشركات، المنشآت، المواقع، والأرفف.
 */
export const orgModule = {
    methods: {
        // حماية المصفوفات باستخدام (|| []) لمنع خطأ TypeError: Cannot read properties of undefined
        getPlantsForOpco(instance, id) { 
            return (instance.plants || []).filter(p => p.opco === id); 
        },
        getLocationsForPlant(instance, id) { 
            return (instance.locations || []).filter(l => l.plant === id); 
        },
        getBinsForLocation(instance, id) { 
            return (instance.bins || []).filter(b => b.storage_location === id); 
        },
        getBinsCount(instance, id) { 
            const bins = this.getBinsForLocation(instance, id);
            return bins ? bins.length : 0; 
        },
        
        handleDrop(instance, targetType, parentId) {
            // منطق تحديد النوع المسحوب وفتح النافذة المناسبة
            if (instance.draggedType === 'plant' && targetType === 'plant') {
                instance.activeOpcoId = parentId; 
                instance.openModal('plant'); 
            } else if (instance.draggedType === 'location' && targetType === 'location') {
                instance.activePlantId = parentId; 
                instance.openModal('location'); 
            } else if (instance.draggedType === 'bin' && targetType === 'bin') {
                instance.activeLocationId = parentId; 
                instance.openModal('bin'); 
            }
            instance.draggedType = null;
        }
    }
};