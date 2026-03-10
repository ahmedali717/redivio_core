from rest_framework import serializers
from .models import Material, Category, MaterialLocation

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    opco_name = serializers.CharField(source='opco.name', read_only=True)
    
    # 🚀 الحقل الأساسي لربط الجدول الديناميكي في Vue.js (Read-only)
    company_assignments = serializers.SerializerMethodField()

    # حقول القراءة القديمة (للإبقاء على التوافق)
    storage_locations_ids = serializers.SerializerMethodField()
    current_primary_bin = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            'id', 'opco', 'sku', 'name', 'category', 'category_name', 
            'opco_name', 'base_uom', 'barcode', 'company_assignments',
            'storage_locations_ids', 'current_primary_bin',
            'image', 'tracking', 'reorder_level', 'max_level'
        ]
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=Material.objects.all(),
                fields=['opco', 'sku'],
                message="خطأ: كود الصنف (SKU) هذا مسجل مسبقاً لهذه الشركة."
            )
        ]

    # --- دالات القراءة (GET) ---

    def get_company_assignments(self, obj):
        """ يجهز البيانات للجدول الديناميكي ليظهر الصنف في كل الشركات المرتبطة به """
        assignments = []
        related_materials = Material.objects.filter(sku=obj.sku)
        for mat in related_materials:
            assignments.append({
                'opco_id': mat.opco_id,
                'bins': list(mat.material_bins.values_list('storage_bin_id', flat=True)),
                'primary_bin': mat.material_bins.filter(is_primary=True).values_list('storage_bin_id', flat=True).first()
            })
        return assignments

    def get_storage_locations_ids(self, obj):
        return list(obj.material_bins.values_list('storage_bin_id', flat=True))

    def get_current_primary_bin(self, obj):
        primary = obj.material_bins.filter(is_primary=True).first()
        return primary.storage_bin_id if primary else None

    # --- دالات الكتابة (POST/PATCH) ---

    def create(self, validated_data):
        request = self.context.get('request')
        # استلام المصفوفة من Vue.js
        assignments = request.data.get('company_assignments', [])
        
        sku = validated_data.get('sku')
        material_instance = None

        if assignments:
            # 🚀 أسلوب تعدد الشركات: إنشاء سجل لكل شركة في الجدول
            for assign in assignments:
                opco_id = assign.get('opco_id')
                if not opco_id: continue
                
                mat, created = Material.objects.update_or_create(
                    sku=sku,
                    opco_id=opco_id,
                    defaults={
                        'name': validated_data.get('name'),
                        'category': validated_data.get('category'),
                        'base_uom': validated_data.get('base_uom'),
                        'barcode': validated_data.get('barcode'),
                        'tracking': validated_data.get('tracking', 'none'),
                        'reorder_level': validated_data.get('reorder_level', 0),
                        'max_level': validated_data.get('max_level', 0),
                        'image': validated_data.get('image')
                    }
                )
                
                # ربط الرفوف
                bins = assign.get('bins', [])
                primary = assign.get('primary_bin')
                mat.material_bins.all().delete()
                for bin_id in bins:
                    MaterialLocation.objects.create(
                        material=mat,
                        storage_bin_id=bin_id,
                        is_primary=(str(bin_id) == str(primary))
                    )
                material_instance = mat
            return material_instance
        
        # fallback للإنشاء العادي لو مفيش مصفوفة
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        assignments = request.data.get('company_assignments', [])
        
        # 1. تحديث البيانات الأساسية (الاسم، الكود، إلخ)
        instance = super().update(instance, validated_data)

        # 2. إذا تم إرسال مصفوفة الشركات، نقوم بتحديث الروابط
        if assignments:
            for assign in assignments:
                opco_id = assign.get('opco_id')
                if not opco_id: continue
                
                # تحديث الصنف التابع لتلك الشركة أو إنشاؤه
                mat, _ = Material.objects.update_or_create(
                    sku=instance.sku,
                    opco_id=opco_id,
                    defaults={
                        'name': instance.name,
                        'category': instance.category,
                        'base_uom': instance.base_uom,
                        'barcode': instance.barcode,
                        'image': instance.image
                    }
                )
                
                # تحديث الرفوف
                bins = assign.get('bins', [])
                primary = assign.get('primary_bin')
                mat.material_bins.all().delete()
                for bin_id in bins:
                    MaterialLocation.objects.create(
                        material=mat,
                        storage_bin_id=bin_id,
                        is_primary=(str(bin_id) == str(primary))
                    )
        return instance