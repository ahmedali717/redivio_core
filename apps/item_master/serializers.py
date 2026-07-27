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
    on_hand = serializers.SerializerMethodField()
    recipe_lines = serializers.SerializerMethodField()
    combo_lines = serializers.SerializerMethodField()
    stock_details = serializers.SerializerMethodField()
    allowed_terminals = serializers.SerializerMethodField()
    plant_prices = serializers.SerializerMethodField()
    
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    sale_group = serializers.PrimaryKeyRelatedField(queryset=SaleGroup.objects.all(), required=False, allow_null=True)
    parent_template = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all(), required=False, allow_null=True)

    class Meta:
        model = Material
        fields = [
            'id', 'sku', 'name', 'description', 'category', 'category_name', 'sale_group', 'sale_group_name',
            'base_uom', 'alternate_uom', 'uom_conversion_factor', 'is_active', 'barcode', 'company_assignments',
            'standard_price', 'sales_price', 'tax_rate', 'plant_prices',
            'image', 'tracking', 'reorder_level', 'max_level', 'on_hand', 'stock_details',
            'is_pos_item', 'is_combo', 'expiry_date', 'recipe_lines', 'combo_lines', 'allowed_terminals',
            'has_variants', 'parent_template', 'variant_name', 'variants'
        ]

    def to_internal_value(self, data):
        raw_data = {}
        if hasattr(data, 'dict'):
            raw_data = data.dict()
        elif isinstance(data, dict):
            raw_data = data.copy()
        else:
            raw_data = dict(data)

        # 🚀 تنظيف الحقول المرتبطة (Foreign Keys)
        for fk_field in ['category', 'sale_group', 'parent_template']:
            val = raw_data.get(fk_field)
            if isinstance(val, list):
                val = val[0] if len(val) > 0 else None
            if val in ['', 'null', 'undefined', 'None', None]:
                raw_data[fk_field] = None

        # 🚀 تنظيف حقل التواريخ
        for date_field in ['expiry_date']:
            val = raw_data.get(date_field)
            if isinstance(val, list):
                val = val[0] if len(val) > 0 else None
            if val in ['', 'null', 'undefined', 'None', None]:
                raw_data[date_field] = None

        # 🚀 تنظيف حقول الأرقام والمبالغ
        for num_field in ['reorder_level', 'max_level', 'standard_price', 'sales_price', 'tax_rate', 'weight', 'volume', 'uom_conversion_factor']:
            val = raw_data.get(num_field)
            if isinstance(val, list):
                val = val[0] if len(val) > 0 else None
            if val in ['', 'null', 'undefined', 'None', None]:
                raw_data[num_field] = 0

        return super().to_internal_value(raw_data)

    def get_plant_prices(self, obj):
        return [{
            'plant_id': p.plant_id,
            'plant_name': p.plant.name,
            'standard_price': float(p.standard_price),
            'sales_price': float(p.sales_price)
        } for p in obj.plant_prices.all()]

    def get_variants(self, obj):
        if obj.has_variants:
            return MaterialSerializer(obj.variants.all(), many=True, context=self.context).data
        return []

    def get_on_hand(self, obj):
        details = self.get_stock_details(obj)
        return sum(item['quantity'] for item in details)

    def get_recipe_lines(self, obj):
        try:
            recipe = obj.recipe # OneToOneField related_name='recipe'
            return [{
                'ingredient_id': item.ingredient_id,
                'ingredient_name': item.ingredient.name,
                'quantity': item.quantity,
                'uom': item.uom,
                'on_hand': item.ingredient.total_on_hand
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
        request = self.context.get('request')
        terminal_id = request.query_params.get('terminal') if request else None
        
        quants = StockQuant.objects.filter(material=obj, opco=obj.opco)
        
        if terminal_id and terminal_id not in ['null', 'undefined', '']:
            try:
                from apps.restaurant_pos.models import POSTerminal
                term = POSTerminal.objects.filter(id=int(terminal_id)).first()
                if term and term.plant:
                    quants = quants.filter(storage_bin__plant=term.plant)
            except (ValueError, TypeError):
                pass
                
        return [{
            'bin_id': q.storage_bin.id,
            'bin': q.storage_bin.code,
            'location': "-",
            'plant': q.storage_bin.plant.name,
            'quantity': q.quantity
        } for q in quants]

    def get_allowed_terminals(self, obj):
        return list(obj.allowed_terminals.values_list('id', flat=True))

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
                    'max_level': validated_data.get('max_level', 0),
                    'has_variants': validated_data.get('has_variants', False)
                }
            )
            
            # Handle variants
            if mat.has_variants:
                variants_data = request.data.get('variants', [])
                if isinstance(variants_data, str):
                    try: variants_data = json.loads(variants_data)
                    except: variants_data = []
                
                # We need to create/update each variant
                for v_data in variants_data:
                    Material.objects.update_or_create(
                        sku=v_data.get('sku'),
                        opco_id=opco_id,
                        defaults={
                            'name': mat.name,
                            'parent_template': mat,
                            'variant_name': v_data.get('variant_name'),
                            'category': mat.category,
                            'sale_group': mat.sale_group,
                            'base_uom': mat.base_uom,
                            'barcode': v_data.get('barcode', ''),
                            'sales_price': v_data.get('sales_price', mat.sales_price),
                            'standard_price': mat.standard_price,
                            'tax_rate': mat.tax_rate,
                            'is_pos_item': mat.is_pos_item,
                            'has_variants': False
                        }
                    )
            
            # Save Recipe if provided
            recipe_data = request.data.get('recipe_lines')
            if recipe_data is not None:
                if isinstance(recipe_data, str):
                    try: recipe_data = json.loads(recipe_data)
                    except: recipe_data = []
                
                if not isinstance(recipe_data, (list, tuple, set)):
                    recipe_data = []

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
                
                if not isinstance(combo_data, (list, tuple, set)):
                    combo_data = []

                mat.combo_items.all().delete()
                for c_line in combo_data:
                    if c_line.get('item_id'):
                        ComboItem.objects.create(
                            parent_material=mat,
                            item_id=c_line.get('item_id'),
                            quantity=c_line.get('quantity', 1),
                            extra_price=c_line.get('extra_price', 0)
                        )

            # Save Allowed Terminals if provided
            allowed_terminals_data = request.data.get('allowed_terminals')
            if allowed_terminals_data is not None:
                if isinstance(allowed_terminals_data, str):
                    try: allowed_terminals = json.loads(allowed_terminals_data)
                    except: allowed_terminals = []
                else:
                    allowed_terminals = allowed_terminals_data
                
                if not isinstance(allowed_terminals, (list, tuple, set)):
                    if allowed_terminals and not isinstance(allowed_terminals, bool):
                        allowed_terminals = [allowed_terminals]
                    else:
                        allowed_terminals = []

                from apps.restaurant_pos.models import POSTerminal
                valid_terminals = POSTerminal.objects.filter(id__in=allowed_terminals, opco_id=mat.opco_id)
                mat.allowed_terminals.set(valid_terminals)

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

        if material_instance is None:
            material_instance = super().create(validated_data)
            allowed_terminals_data = request.data.get('allowed_terminals')
            if allowed_terminals_data is not None:
                if isinstance(allowed_terminals_data, str):
                    try: allowed_terminals = json.loads(allowed_terminals_data)
                    except: allowed_terminals = []
                else:
                    allowed_terminals = allowed_terminals_data
                
                if not isinstance(allowed_terminals, (list, tuple, set)):
                    if allowed_terminals and not isinstance(allowed_terminals, bool):
                        allowed_terminals = [allowed_terminals]
                    else:
                        allowed_terminals = []

                from apps.restaurant_pos.models import POSTerminal
                valid_terminals = POSTerminal.objects.filter(id__in=allowed_terminals, opco_id=material_instance.opco_id)
                material_instance.allowed_terminals.set(valid_terminals)

        return material_instance

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
                        'max_level': instance.max_level,
                        'has_variants': instance.has_variants
                    }
                )

                # Handle variants in update
                if mat.has_variants:
                    variants_data = request.data.get('variants', [])
                    if isinstance(variants_data, str):
                        try: variants_data = json.loads(variants_data)
                        except: variants_data = []
                    
                    for v_data in variants_data:
                        v_sku = v_data.get('sku')
                        if v_sku:
                            Material.objects.update_or_create(
                                sku=v_sku,
                                opco_id=opco_id,
                                defaults={
                                    'name': mat.name,
                                    'parent_template': mat,
                                    'variant_name': v_data.get('variant_name'),
                                    'category': mat.category,
                                    'sale_group': mat.sale_group,
                                    'base_uom': mat.base_uom,
                                    'barcode': v_data.get('barcode', ''),
                                    'sales_price': v_data.get('sales_price', mat.sales_price),
                                    'standard_price': mat.standard_price,
                                    'tax_rate': mat.tax_rate,
                                    'is_pos_item': mat.is_pos_item,
                                    'has_variants': False
                                }
                            )

                # Save Recipe
                recipe_data = request.data.get('recipe_lines')
                if recipe_data is not None:
                    if isinstance(recipe_data, str):
                        try: recipe_data = json.loads(recipe_data)
                        except: recipe_data = []
                    
                    if not isinstance(recipe_data, (list, tuple, set)):
                        recipe_data = []

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
                    
                    if not isinstance(combo_data, (list, tuple, set)):
                        combo_data = []

                    mat.combo_items.all().delete()
                    for c_line in combo_data:
                        if c_line.get('item_id'):
                            ComboItem.objects.create(
                                parent_material=mat,
                                item_id=c_line.get('item_id'),
                                quantity=c_line.get('quantity', 1),
                                extra_price=c_line.get('extra_price', 0)
                            )
                
                # Save Allowed Terminals
                allowed_terminals_data = request.data.get('allowed_terminals')
                if allowed_terminals_data is not None:
                    if isinstance(allowed_terminals_data, str):
                        try: allowed_terminals = json.loads(allowed_terminals_data)
                        except: allowed_terminals = []
                    else:
                        allowed_terminals = allowed_terminals_data
                    
                    if not isinstance(allowed_terminals, (list, tuple, set)):
                        if allowed_terminals and not isinstance(allowed_terminals, bool):
                            allowed_terminals = [allowed_terminals]
                        else:
                            allowed_terminals = []

                    from apps.restaurant_pos.models import POSTerminal
                    valid_terminals = POSTerminal.objects.filter(id__in=allowed_terminals, opco_id=mat.opco_id)
                    mat.allowed_terminals.set(valid_terminals)

                bins = assign.get('bins', [])
                primary = assign.get('primary_bin')
                mat.material_bins.all().delete()
                for bin_id in bins:
                    MaterialLocation.objects.create(
                        material=mat,
                        storage_bin_id=bin_id,
                        is_primary=(str(bin_id) == str(primary))
                    )

        # Update allowed terminals on primary instance as well
        allowed_terminals_data = request.data.get('allowed_terminals')
        if allowed_terminals_data is not None:
            if isinstance(allowed_terminals_data, str):
                try: allowed_terminals = json.loads(allowed_terminals_data)
                except: allowed_terminals = []
            else:
                allowed_terminals = allowed_terminals_data
            
            if not isinstance(allowed_terminals, (list, tuple, set)):
                if allowed_terminals and not isinstance(allowed_terminals, bool):
                    allowed_terminals = [allowed_terminals]
                else:
                    allowed_terminals = []

            from apps.restaurant_pos.models import POSTerminal
            valid_terminals = POSTerminal.objects.filter(id__in=allowed_terminals, opco_id=instance.opco_id)
            instance.allowed_terminals.set(valid_terminals)

        return instance