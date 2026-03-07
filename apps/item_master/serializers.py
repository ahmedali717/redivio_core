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
    
    # تأكد أن الاسم هنا يطابق ما ترسله من الفرونت-إند (assigned_bins)
    assigned_bins = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )

    class Meta:
        model = Material
        fields = [
            'id', 'opco', 'sku', 'name', 'category', 'category_name', 
            'opco_name', 'base_uom', 'barcode', 'assigned_bins', 
            'extra_data', 'image', 'reorder_level', 'max_level' # تأكد من إضافة حقول الحدود
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Material.objects.all(),
                fields=['opco', 'sku'],
                message="خطأ: كود الصنف (SKU) هذا مسجل مسبقاً لهذه الشركة."
            )
        ]

    def create(self, validated_data):
        # --- الجزء الخاص بالعرض في الـ Terminal ---
        print("\n" + "="*50)
        print("🚀 [CREATE] Incoming Data to Serializer:")
        for key, value in validated_data.items():
            print(f"🔹 {key}: {value}")
        print("="*50 + "\n")
        # ------------------------------------------

        bins_ids = validated_data.pop('assigned_bins', [])
        material = Material.objects.create(**validated_data)
        
        for bin_id in bins_ids:
            MaterialLocation.objects.create(material=material, storage_bin_id=bin_id)
            
        return material

    def update(self, instance, validated_data):
        # --- الجزء الخاص بالعرض في الـ Terminal عند التعديل ---
        print("\n" + "="*50)
        print(f"📝 [UPDATE] Editing Material ID: {instance.id}")
        print("="*50 + "\n")
        # ---------------------------------------------------

        bins_ids = validated_data.pop('assigned_bins', None)
        
        # تحديث الحقول الأساسية
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # تحديث الرفوف (حذف القديم وإضافة الجديد)
        if bins_ids is not None:
            instance.material_bins.all().delete()
            for bin_id in bins_ids:
                MaterialLocation.objects.create(material=instance, storage_bin_id=bin_id)

        return instance