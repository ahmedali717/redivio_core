import json
from rest_framework import serializers
from .models import Material, Category, MaterialLocation

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    company_assignments = serializers.SerializerMethodField()
    on_hand = serializers.DecimalField(source='total_on_hand', max_digits=12, decimal_places=2, read_only=True)
    stock_details = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            'id', 'sku', 'name', 'category', 'category_name', 
            'base_uom', 'barcode', 'company_assignments','standard_price',
            'image', 'tracking', 'reorder_level', 'max_level', 'on_hand', 'stock_details'
        ]

    def get_stock_details(self, obj):
        """إرجاع الأرصدة مقسمة بالأرفف للأودو 19 موديول"""
        from apps.wms.models import StockQuant
        quants = StockQuant.objects.filter(material=obj, opco=obj.opco)
        return [{
            'bin': q.storage_bin.code,
            'location': q.storage_bin.storage_location.name,
            'plant': q.storage_bin.storage_location.plant.name,
            'quantity': q.quantity
        } for q in quants]

    def get_company_assignments(self, obj):
        assignments = []
        related_materials = Material.objects.filter(sku=obj.sku)
        for mat in related_materials:
            assignments.append({
                'opco_id': mat.opco_id,
                'bins': list(mat.material_bins.values_list('storage_bin_id', flat=True)),
                'primary_bin': mat.material_bins.filter(is_primary=True).values_list('storage_bin_id', flat=True).first()
            })
        return assignments

    def create(self, validated_data):
        request = self.context.get('request')
        assignments_data = request.data.get('company_assignments', [])

        # تحويل النص لـ JSON لو جاي من FormData
        if isinstance(assignments_data, str):
            try:
                assignments = json.loads(assignments_data)
            except:
                assignments = []
        else:
            assignments = assignments_data

        material_instance = None
        for assign in assignments:
            opco_id = assign.get('opco_id')
            if not opco_id: continue
            
            mat, _ = Material.objects.update_or_create(
                sku=validated_data.get('sku'),
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
        return material_instance or super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        assignments_data = request.data.get('company_assignments', [])

        if isinstance(assignments_data, str):
            try:
                assignments = json.loads(assignments_data)
            except:
                assignments = []
        else:
            assignments = assignments_data

        instance = super().update(instance, validated_data)

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