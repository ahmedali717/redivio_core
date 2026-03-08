from rest_framework import serializers
# 👈 1. شيلنا FieldDefinition من السطر ده
from .models import Material, Category, MaterialLocation

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    opco_name = serializers.CharField(source='opco.name', read_only=True)
    
    # حقول الكتابة (تستخدم عند إرسال البيانات من الواجهة)
    assigned_bins = serializers.ListField(
        child=serializers.IntegerField(), 
        write_only=True, 
        required=False
    )
    primary_bin = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    # 🚀 حقول القراءة (تضمن ظهور الرفوف والنجمة فور فتح المودال للتعديل)
    storage_locations_ids = serializers.SerializerMethodField()
    current_primary_bin = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            'id', 'opco', 'sku', 'name', 'category', 'category_name', 
            'opco_name', 'base_uom', 'barcode', 'assigned_bins', 'primary_bin',
            'storage_locations_ids', 'current_primary_bin',
            'image', 'tracking', 'weight', 'volume', 'reorder_level', 'max_level' # 👈 تأكد من أسماء الحقول المضافة للموديل
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Material.objects.all(),
                fields=['opco', 'sku'],
                message="خطأ: كود الصنف (SKU) هذا مسجل مسبقاً لهذه الشركة."
            )
        ]

    # جلب قائمة IDs الرفوف المختارة حالياً
    def get_storage_locations_ids(self, obj):
        return list(obj.material_bins.values_list('storage_bin_id', flat=True))

    # جلب ID الرف الرئيسي (الـ Putaway Rule الحالية)
    def get_current_primary_bin(self, obj):
        primary = obj.material_bins.filter(is_primary=True).first()
        return primary.storage_bin_id if primary else None

    def create(self, validated_data):
        # استخراج بيانات الرفوف قبل الإنشاء
        bins_ids = validated_data.pop('assigned_bins', [])
        primary_bin_id = validated_data.pop('primary_bin', None)
        target_opco = validated_data.get('opco')
        sku = validated_data.get('sku')

        # 1. إنشاء الصنف الأساسي
        material = super().create(validated_data)
        
        # 2. تطبيق قواعد الـ Putaway (ربط الرفوف)
        if bins_ids:
            for bin_id in bins_ids:
                MaterialLocation.objects.create(
                    material=material, 
                    storage_bin_id=bin_id, 
                    is_primary=(str(bin_id) == str(primary_bin_id))
                )

        # 3. مزامنة "مرآة" الصنف في الشركة القابضة (Odoo Multi-company Style)
        if target_opco and target_opco.parent:
            holding_opco = target_opco.parent
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
        return material

    def update(self, instance, validated_data):
        # استخراج بيانات الرفوف للتحديث
        bins_ids = validated_data.pop('assigned_bins', None)
        primary_bin_id = validated_data.pop('primary_bin', None)
        target_opco = instance.opco
        sku = validated_data.get('sku', instance.sku)

        # 1. تحديث الحقول الأساسية
        instance = super().update(instance, validated_data)

        # 2. تحديث قواعد الـ Putaway (مسح وإعادة بناء الروابط)
        if bins_ids is not None:
            instance.material_bins.all().delete()
            for bin_id in bins_ids:
                MaterialLocation.objects.create(
                    material=instance, 
                    storage_bin_id=bin_id, 
                    is_primary=(str(bin_id) == str(primary_bin_id))
                )

        # 3. تحديث الشركة القابضة لضمان توحيد بيانات الكتالوج
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