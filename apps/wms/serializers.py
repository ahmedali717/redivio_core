from rest_framework import serializers
from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove

# --- السيريالايزرز الأساسية ---

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'
        # Disable implicit DRF validators so our custom validate method runs
        validators = []

    def validate(self, attrs):
        code = attrs.get('code', getattr(self.instance, 'code', None))
        name = attrs.get('name', getattr(self.instance, 'name', None))
        opco = attrs.get('opco', getattr(self.instance, 'opco', None))

        request = self.context.get('request')
        is_arabic = request and request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        
        # Check unique constraint for code per opco
        if code and opco:
            qs = Plant.objects.filter(opco=opco, code=code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            existing = qs.first()
            if existing:
                msg = f"الكود مكرر ومستخدم بالفعل مع المنشأة: ({existing.name})" if is_arabic else f"Code is already used by plant: {existing.name}"
                raise serializers.ValidationError({"code": msg})

        # Check unique constraint for name per opco
        if name and opco:
            qs = Plant.objects.filter(opco=opco, name=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            existing = qs.first()
            if existing:
                msg = f"الاسم مكرر، توجد منشأة بنفس الاسم تم إنشاؤها مسبقاً بكود: ({existing.code})" if is_arabic else f"Name is already used by plant with code: {existing.code}"
                raise serializers.ValidationError({"name": msg})

        return attrs

class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'

class StorageBinSerializer(serializers.ModelSerializer):
    plant_name = serializers.SerializerMethodField()
    location_name = serializers.SerializerMethodField()
    plant_id = serializers.SerializerMethodField()

    class Meta:
        model = StorageBin
        fields = '__all__'

    def get_plant_name(self, obj):
        try:
            return obj.storage_location.plant.name
        except AttributeError:
            return "-"

    def get_location_name(self, obj):
        return obj.storage_location.name if obj.storage_location else "-"

    def get_plant_id(self, obj):
        try:
            return obj.storage_location.plant.id
        except AttributeError:
            return None

# --- سيريالايزر المخزون الحالي ---

class StockQuantSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    bin_code = serializers.CharField(source='storage_bin.code', read_only=True)
    plant_name = serializers.CharField(source='plant.name', read_only=True)
    plant_id = serializers.IntegerField(source='plant.id', read_only=True)
    location_name = serializers.SerializerMethodField()

    class Meta:
        model = StockQuant
        fields = '__all__'

    def get_location_name(self, obj):
        if obj.storage_bin and obj.storage_bin.storage_location:
            return obj.storage_bin.storage_location.name
        return "-"

# --- معالجة حركات المخزون المتعددة ---

class StockMoveItemSerializer(serializers.ModelSerializer):
    """سيريالايزر للعناصر الفردية"""
    material_id = serializers.IntegerField() 

    class Meta:
        model = StockMove
        fields = ['material_id', 'quantity', 'unit_cost', 'sales_price']

class StockMoveSerializer(serializers.ModelSerializer):
    items = StockMoveItemSerializer(many=True, write_only=True)
    
    material_name = serializers.CharField(source='material.name', read_only=True)
    source_loc = serializers.SerializerMethodField()
    dest_loc = serializers.SerializerMethodField()
    
    # إذا كان receipt_type غير موجود في الموديل، نعرفه هنا كـ Field إضافي
    # لمنع خطأ ImproperlyConfigured
    receipt_type = serializers.CharField(required=False, allow_blank=True, write_only=True)
    receipt_id = serializers.SerializerMethodField()
    customer_name = serializers.CharField(source='customer.name', read_only=True)

    class Meta:
        model = StockMove
        fields = [
            'id', 'created_at', 'items', 'move_type', 'receipt_type', 'opco', 'reference', 
            'vendor_name', 'customer_name', 'payment_term', 'payment_method', 'dest_bin', 'source_bin',
            'material_name', 'source_loc', 'dest_loc', 'material', 'quantity', 'receipt_id',
            'unit_cost', 'sales_price', 'vendor', 'customer'
        ]
        extra_kwargs = {
            'material': {'required': False, 'allow_null': True},
            'quantity': {'required': False},
            'dest_bin': {'required': False, 'allow_null': True},
            'source_bin': {'required': False, 'allow_null': True},
            'opco': {'required': False, 'allow_null': True},
        }

    def get_source_loc(self, obj):
        return obj.source_bin.code if obj.source_bin else "External"

    def get_dest_loc(self, obj):
        return obj.dest_bin.code if obj.dest_bin else "External"

    def get_receipt_id(self, obj):
        if obj.reference and obj.reference.startswith("GRN: "):
            receipt_no = obj.reference.split("GRN: ")[1].strip()
            from django.apps import apps
            try:
                StockReceipt = apps.get_model('procurement', 'StockReceipt')
                receipt = StockReceipt.objects.filter(receipt_number=receipt_no).first()
                if receipt:
                    return receipt.id
            except LookupError:
                pass
        return None

    def create(self, validated_data):
        """تصحيح: يجب أن تكون الدالة داخل الكلاس وبإزاحة صحيحة"""
        items_data = validated_data.pop('items')
        
        # استبعاد receipt_type إذا كان غير موجود في الموديل الفعلي لمنع أخطاء الـ create
        receipt_type = validated_data.pop('receipt_type', None)
        
        common_info = {
            'move_type': validated_data.get('move_type'),
            'reference': validated_data.get('reference', 'MANUAL'),
            'vendor_name': validated_data.get('vendor_name', ""),
            'customer_name': validated_data.get('customer_name', ""),
            'payment_term': validated_data.get('payment_term', "CASH"),
            'payment_method': validated_data.get('payment_method', "CASH"),
            'opco': validated_data.get('opco'),
            'dest_bin': validated_data.get('dest_bin'),
            'source_bin': validated_data.get('source_bin'),
        }

        last_move = None
        for item in items_data:
            last_move = StockMove.objects.create(
                material_id=item['material_id'],
                quantity=item['quantity'],
                unit_cost=item.get('unit_cost', 0),
                sales_price=item.get('sales_price', 0),
                **common_info
            )
        
        return last_move