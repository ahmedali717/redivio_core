import json
from rest_framework import serializers
from .models import Material, Category, MaterialLocation, SaleGroup, ComboItem

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class SaleGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleGroup
        fields = '__all__'

class MaterialSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    sale_group_name = serializers.CharField(source='sale_group.name', read_only=True)
    company_assignments = serializers.SerializerMethodField()
    on_hand = serializers.DecimalField(source='total_on_hand', max_digits=12, decimal_places=2, read_only=True)
    recipe_lines = serializers.SerializerMethodField()
    combo_lines = serializers.SerializerMethodField()
    stock_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Material
        fields = [
            'id', 'sku', 'name', 'category', 'category_name', 'sale_group', 'sale_group_name',
            'base_uom', 'barcode', 'company_assignments','standard_price', 'sales_price', 'tax_rate',
            'image', 'tracking', 'reorder_level', 'max_level', 'on_hand', 'stock_details',
            'is_pos_item', 'is_combo', 'expiry_date', 'recipe_lines', 'combo_lines'
        ]

    def get_recipe_lines(self, obj):
        try:
            recipe = obj.recipe # OneToOneField related_name='recipe'
            return [{
                'ingredient_id': item.ingredient_id,
                'quantity': item.quantity,
                'uom': item.uom
            } for item in recipe.ingredients.all()]
        except:
            return []

    def get_combo_lines(self, obj):
        return [{
            'item_id': item.item_id,
            'quantity': item.quantity,
            'extra_price': item.extra_price
        } for item in obj.combo_items.all()]

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
                    'sale_group': validated_data.get('sale_group'),
                    'base_uom': validated_data.get('base_uom'),
                    'barcode': validated_data.get('barcode'),
                    'tracking': validated_data.get('tracking', 'none'),
                    'image': validated_data.get('image'),
                    'is_pos_item': validated_data.get('is_pos_item', False),
                    'is_combo': validated_data.get('is_combo', False),
                    'expiry_date': validated_data.get('expiry_date'),
                    'standard_price': validated_data.get('standard_price', 0),
                    'sales_price': validated_data.get('sales_price', 0),
                    'tax_rate': validated_data.get('tax_rate', 15),
                    'reorder_level': validated_data.get('reorder_level', 0),
                    'max_level': validated_data.get('max_level', 0)
                }
            )
            
            # Save Recipe if provided
            recipe_data = request.data.get('recipe_lines')
            if recipe_data is not None:
                if isinstance(recipe_data, str):
                    try: recipe_data = json.loads(recipe_data)
                    except: recipe_data = []
                
                from apps.restaurant_pos.models import Recipe, RecipeItem
                recipe, _ = Recipe.objects.update_or_create(
                    opco=mat.opco, finished_good=mat,
                    defaults={'name': f"Recipe for {mat.name}"}
                )
                recipe.ingredients.all().delete()
                for r_line in recipe_data:
                    if r_line.get('ingredient_id'):
                        RecipeItem.objects.create(
                            recipe=recipe,
                            ingredient_id=r_line.get('ingredient_id'),
                            quantity=r_line.get('quantity', 0),
                            uom=r_line.get('uom', 'KG')
                        )

            # Save Combo Lines if provided
            combo_data = request.data.get('combo_lines')
            if combo_data is not None:
                if isinstance(combo_data, str):
                    try: combo_data = json.loads(combo_data)
                    except: combo_data = []
                
                mat.combo_items.all().delete()
                for c_line in combo_data:
                    if c_line.get('item_id'):
                        ComboItem.objects.create(
                            parent_material=mat,
                            item_id=c_line.get('item_id'),
                            quantity=c_line.get('quantity', 1),
                            extra_price=c_line.get('extra_price', 0)
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
                        'sale_group': instance.sale_group,
                        'base_uom': instance.base_uom,
                        'barcode': instance.barcode,
                        'image': instance.image,
                        'is_pos_item': instance.is_pos_item,
                        'is_combo': instance.is_combo,
                        'expiry_date': instance.expiry_date,
                        'standard_price': instance.standard_price,
                        'sales_price': instance.sales_price,
                        'tax_rate': instance.tax_rate,
                        'reorder_level': instance.reorder_level,
                        'max_level': instance.max_level
                    }
                )

                # Save Recipe
                recipe_data = request.data.get('recipe_lines')
                if recipe_data is not None:
                    if isinstance(recipe_data, str):
                        try: recipe_data = json.loads(recipe_data)
                        except: recipe_data = []
                    
                    from apps.restaurant_pos.models import Recipe, RecipeItem
                    recipe, _ = Recipe.objects.update_or_create(
                        opco=mat.opco, finished_good=mat,
                        defaults={'name': f"Recipe for {mat.name}"}
                    )
                    recipe.ingredients.all().delete()
                    for r_line in recipe_data:
                        if r_line.get('ingredient_id'):
                            RecipeItem.objects.create(
                                recipe=recipe,
                                ingredient_id=r_line.get('ingredient_id'),
                                quantity=r_line.get('quantity', 0),
                                uom=r_line.get('uom', 'KG')
                            )
                
                # Save Combo Lines
                combo_data = request.data.get('combo_lines')
                if combo_data is not None:
                    if isinstance(combo_data, str):
                        try: combo_data = json.loads(combo_data)
                        except: combo_data = []
                    
                    mat.combo_items.all().delete()
                    for c_line in combo_data:
                        if c_line.get('item_id'):
                            ComboItem.objects.create(
                                parent_material=mat,
                                item_id=c_line.get('item_id'),
                                quantity=c_line.get('quantity', 1),
                                extra_price=c_line.get('extra_price', 0)
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