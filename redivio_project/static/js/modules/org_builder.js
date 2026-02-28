/**
 * موديول بناء الهيكل التنظيمي (Org Builder Module)
 */
export const orgModule = {
    methods: {
        getPlantsForOpco(instance, id) { 
            return (instance.plants || []).filter(p => Number(p.opco) === Number(id)); 
        },
        
        getLocationsForPlant(instance, id) { 
            return (instance.locations || []).filter(l => Number(l.plant) === Number(id)); 
        },

        getBinsForLocation(instance, id) { 
            return (instance.bins || []).filter(b => Number(b.storage_location) === Number(id)); 
        },

        getBinsCount(instance, id) { 
            // استخدام orgModule.methods بدلاً من this لضمان الوصول للدالة
            const bins = orgModule.methods.getBinsForLocation(instance, id);
            return bins ? bins.length : 0; 
        },
        
        handleDrop(instance, targetType, parentId) {
            const type = instance.draggedType;
            
            // حالة إضافة شركة تابعة
            if (type === 'opco') {
                const targetOpco = (instance.opcos || []).find(o => o.id === parentId);
                if (targetOpco && targetOpco.is_holding) {
                    const subCount = (instance.opcos || []).filter(o => {
                        const pId = (o.parent && typeof o.parent === 'object') ? o.parent.id : o.parent;
                        return Number(pId) === Number(parentId);
                    }).length;
                    instance.openModal('opco', { parent: parentId, code: `${targetOpco.code}-${subCount + 1}` });
                } else if (!parentId) {
                    instance.openModal('opco');
                }
            } 
            
            // حالة إضافة مستودع (Plant) فوق شركة
            else if (type === 'plant' && targetType === 'opco') {
                instance.activeOpcoId = parentId;
                instance.openModal('plant');
            }
            
            // حالة إضافة موقع (Location) فوق مستودع
            else if (type === 'location' && targetType === 'plant') {
                instance.activePlantId = parentId;
                instance.openModal('location');
            }
            
            // حالة إضافة رف (Bin) فوق موقع
            else if (type === 'bin' && targetType === 'location') {
                instance.activeLocationId = parentId;
                instance.openModal('bin');
            }

            instance.draggedType = null;
        }
    }
};