from rest_framework import serializers
from apps.core.models import OpCo
# ✅ تأكد من استيراد StorageBin من هنا
from apps.wms.models import Plant, StorageLocation, StorageBin

class OpCoSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpCo
        # أضفنا 'parent' هنا لضمان حفظ الربط بين الشركات
        fields = [
            'id', 'name', 'code', 'created_at', 'is_holding', 
            'plan', 'tax_id', 'cr_number', 'logo', 'parent', 'currency'
        ]

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'

class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'

# ✅ هذا هو الكلاس الذي يسبب الخطأ لعدم وجوده
class StorageBinSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageBin
        fields = '__all__'