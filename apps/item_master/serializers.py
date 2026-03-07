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

# 3. سيريالايزر الأصناف المطور (النسخة النهائية المصححة)
class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    opco_name = serializers.CharField(source='opco.name', read_only=True)
    
    # حقول الكتابة (تستخدم عند الحفظ والتعديل)
    assigned_bins = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )
    primary_bin = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    # 🚀 حقول القراءة (تستخدم لإظهار البيانات في الواجهة وقت التعديل)
    storage_locations_ids = serializers.SerializerMethodField()
    current_primary_bin = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            'id', 'opco', 'sku', 'name', 'category', 'category_name', 
            'opco_name', 'base_uom', 'barcode', 'assigned_bins', 'primary_bin',
            'storage_locations_ids', 'current_primary_bin', # الحقول المضافة للعرض
            'extra_data', 'image', 'reorder_level', 'max_level'
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Material.objects.all(),
                fields=['opco', 'sku'],
                message="خطأ: كود الصنف (SKU) هذا مسجل مسبقاً لهذه الشركة."
            )
        ]

    # دالة لجلب قائمة الـ IDs الخاصة بالرفوف المرتبطة بالصنف
    def get_storage_locations_ids(self, obj):
        return list(obj.material_bins.values_list('storage_bin_id', flat=True))

    # دالة لجلب الـ ID الخاص بالرف الرئيسي (صاحب النجمة)
    def get_current_primary_bin(self, obj):
        primary = obj.material_bins.filter(is_primary=True).first()
        return primary.storage_bin_id if primary else None

    def create(self, validated_data):
        # 🚀 فحص المسميين لضمان الاستلام
        bins_ids = validated_data.pop('assigned_bins', validated_data.pop('storage_locations', []))
        primary_bin_id = validated_data.pop('primary_bin', None)
        
        material = Material.objects.create(**validated_data)
        
        # ربط الرفوف
        if bins_ids:
            for bin_id in bins_ids:
                MaterialLocation.objects.create(
                    material=material, 
                    storage_bin_id=bin_id, 
                    is_primary=(str(bin_id) == str(primary_bin_id))
                )
        return material

    def update(self, instance, validated_data):
        # 🚀 نفس الفحص في التحديث
        bins_ids = validated_data.pop('assigned_bins', validated_data.pop('storage_locations', None))
        primary_bin_id = validated_data.pop('primary_bin', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if bins_ids is not None:
            instance.material_bins.all().delete()
            for bin_id in bins_ids:
                MaterialLocation.objects.create(
                    material=instance, 
                    storage_bin_id=bin_id, 
                    is_primary=(str(bin_id) == str(primary_bin_id))
                )
        return instance
        primary_bin_id = validated_data.pop('primary_bin', None)
        bins_ids = validated_data.pop('assigned_bins', None)
        target_opco = instance.opco
        sku = validated_data.get('sku', instance.sku)

        # 1. تحديث البيانات الأساسية
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 2. تحديث الرفوف (حذف القديم وإضافة الجديد)
        if bins_ids is not None:
            instance.material_bins.all().delete()
            for bin_id in bins_ids:
                is_primary = (bin_id == primary_bin_id)
                MaterialLocation.objects.create(
                    material=instance, 
                    storage_bin_id=bin_id, 
                    is_primary=is_primary
                )

        # 3. تحديث الشركة القابضة
        if target_opco and target_opco.parent:
            holding_opco = target_opco.parent
            Material.objects.filter(opco=holding_opco, sku=sku).update(
                name=validated_data.get('name', instance.name),
                category=validated_data.get('category', instance.category),
                base_uom=validated_data.get('base_uom', instance.base_uom),
                barcode=validated_data.get('barcode', instance.barcode),
                image=validated_data.get('image', instance.image)
            )

        return instance