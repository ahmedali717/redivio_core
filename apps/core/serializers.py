from rest_framework import serializers
from apps.core.models import OpCo
from apps.wms.models import Plant, StorageLocation, StorageBin

class OpCoSerializer(serializers.ModelSerializer):
    # ✅ ضمان وصول التاريخ بصيغة ISO لسهولة معالجته في JavaScript (License calculation)
    # هذا التنسيق يمنع أخطاء الـ Invalid Date في المتصفحات
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    
    class Meta:
        model = OpCo
        fields = [
            'id', 'name', 'code', 'created_at', 'is_holding', 
            'plan', 'tax_id', 'cr_number', 'logo', 'brand_color', 'parent', 'currency'
        ]

    # ✅ تعديل لضمان سلاسة التعامل مع الهيكل الهرمي في Vue.js
    def to_representation(self, instance):
        """
        تحويل البيانات لتبسيط المعالجة في الواجهة الأمامية.
        """
        representation = super().to_representation(instance)
        
        # تحويل الـ parent لـ ID صريح بدلاً من كائن كامل 
        # لسهولة المقارنة في الـ computed properties مثل (currentSubsidiaries)
        if instance.parent:
            representation['parent'] = instance.parent.id
        else:
            representation['parent'] = None
            
        return representation

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'

class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'

class StorageBinSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageBin
        fields = '__all__'