from rest_framework import serializers
from .models import Material, Category, FieldDefinition, MaterialLocation

# 1. سيريالايزر الحقول المخصصة
class FieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FieldDefinition
        fields = '__all__'

# 2. سيريالايزر مجموعات الأصناف
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

# 3. سيريالايزر الأصناف (المعدل لدعم المواقع المتعددة)
class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    opco_name = serializers.CharField(source='opco.name', read_only=True)
    
    # لاستقبال مصفوفة الـ Bins من الواجهة الأمامية
    assigned_bins = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )

    class Meta:
        model = Material
        fields = [
            'id', 'opco', 'sku', 'name', 'category', 'category_name', 
            'opco_name', 'base_uom', 'barcode', 'assigned_bins', 'extra_data', 'image' # أضف هذا هنا
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Material.objects.all(),
                fields=['opco', 'sku'],
                message="خطأ: كود الصنف (SKU) هذا مسجل مسبقاً لهذه الشركة."
            )
        ]

    def create(self, validated_data):
        bins_ids = validated_data.pop('assigned_bins', [])
        material = Material.objects.create(**validated_data)
        
        for bin_id in bins_ids:
            MaterialLocation.objects.create(material=material, storage_bin_id=bin_id)
            
        return material