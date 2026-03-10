from rest_framework import serializers
from .models import Material, Category, MaterialLocation
import json

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
        assignments_data = request.data.get('company_assignments', [])

        # 🚀 الزتونة: إذا كانت البيانات واصلة كـ string بسبب FormData، فك تشفيرها
        if isinstance(assignments_data, str):
            try:
                assignments = json.loads(assignments_data)
            except:
                assignments = []
        else:
            assignments = assignments_data

        sku = validated_data.get('sku')
        material_instance = None

        if assignments:
            for assign in assignments:
                opco_id = assign.get('opco_id') # الآن لن يحدث خطأ لأن assign أصبح Dictionary
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
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        assignments_data = request.data.get('company_assignments', [])

        # 🚀 نفس الإصلاح لعملية الـ PATCH/Update
        if isinstance(assignments_data, str):
            try:
                assignments = json.loads(assignments_data)
            except:
                assignments = []
        else:
            assignments = assignments_data

        # 1. تحديث البيانات الأساسية
        instance = super().update(instance, validated_data)

        # 2. تحديث الروابط في كل الشركات
        if assignments:
            for assign in assignments:
                opco_id = assign.get('opco_id')
                if not opco_id: continue
                
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