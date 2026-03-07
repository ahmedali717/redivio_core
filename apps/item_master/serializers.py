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

# 3. سيريالايزر الأصناف المطور (النسخة النهائية المعتمدة)
class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    opco_name = serializers.CharField(source='opco.name', read_only=True)
    
    # حقل الرفوف المحددة من الواجهة
    assigned_bins = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )
    
    # 🚀 حقل الرف الافتراضي (قاعدة التوجيه - Putaway Rule)
    primary_bin = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Material
        fields = [
            'id', 'opco', 'sku', 'name', 'category', 'category_name', 
            'opco_name', 'base_uom', 'barcode', 'assigned_bins', 'primary_bin',
            'extra_data', 'image', 'reorder_level', 'max_level'
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Material.objects.all(),
                fields=['opco', 'sku'],
                message="خطأ: كود الصنف (SKU) هذا مسجل مسبقاً لهذه الشركة."
            )
        ]

    def create(self, validated_data):
        # استخراج بيانات الرفوف قبل إنشاء الصنف
        primary_bin_id = validated_data.pop('primary_bin', None)
        bins_ids = validated_data.pop('assigned_bins', [])
        target_opco = validated_data.get('opco')
        sku = validated_data.get('sku')

        # 1. إنشاء الصنف في الشركة الحالية (التابعة)
        material = Material.objects.create(**validated_data)
        
        # 2. ربط الرفوف المحددة وتعيين الرف الرئيسي (Putaway Rule)
        for bin_id in bins_ids:
            is_primary = (bin_id == primary_bin_id)
            MaterialLocation.objects.create(
                material=material, 
                storage_bin_id=bin_id, 
                is_primary=is_primary
            )

        # 🚀 3. التزامن التلقائي مع الشركة القابضة (Holding Propagation)
        if target_opco and target_opco.parent:
            holding_opco = target_opco.parent
            # التأكد من عدم وجود الصنف مسبقاً في القابضة بنفس الـ SKU
            if not Material.objects.filter(opco=holding_opco, sku=sku).exists():
                Material.objects.create(
                    opco=holding_opco,
                    sku=sku,
                    name=validated_data.get('name'),
                    category=validated_data.get('category'),
                    base_uom=validated_data.get('base_uom'),
                    barcode=validated_data.get('barcode'),
                    image=validated_data.get('image'),
                    reorder_level=validated_data.get('reorder_level', 0),
                    max_level=validated_data.get('max_level', 0)
                )
                print(f"✅ Auto-propagated SKU {sku} to Holding: {holding_opco.name}")

        return material

    def update(self, instance, validated_data):
        # استخراج بيانات الرفوف للتحديث
        primary_bin_id = validated_data.pop('primary_bin', None)
        bins_ids = validated_data.pop('assigned_bins', None)
        target_opco = instance.opco
        sku = validated_data.get('sku', instance.sku)

        # 1. تحديث الحقول الأساسية للصنف
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 2. تحديث علاقات الرفوف وقاعدة الـ Putaway
        if bins_ids is not None:
            # مسح الروابط القديمة وإعادة إنشائها بالقيم الجديدة
            instance.material_bins.all().delete()
            for bin_id in bins_ids:
                is_primary = (bin_id == primary_bin_id)
                MaterialLocation.objects.create(
                    material=instance, 
                    storage_bin_id=bin_id, 
                    is_primary=is_primary
                )

        # 🚀 3. تحديث "المراية" في الشركة القابضة (Full Sync)
        # لضمان بقاء بيانات الكتالوج موحدة عند تعديل الاسم أو الصورة
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