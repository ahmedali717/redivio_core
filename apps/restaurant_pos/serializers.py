from rest_framework import serializers
from .models import POSTerminal, POSOrder, POSOrderLine, POSSession, Recipe, RecipeItem, POSCashTransaction, RestaurantFloor, RestaurantTable, PromoCode


class POSTerminalSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSTerminal
        fields = '__all__'


class POSOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)

    class Meta:
        model = POSOrderLine
        fields = ['id', 'material', 'material_name', 'qty', 'unit_price', 'subtotal', 'kitchen_notes']


class POSOrderSerializer(serializers.ModelSerializer):
    lines = POSOrderLineSerializer(many=True)
    net_total = serializers.SerializerMethodField()
    discount_type = serializers.SerializerMethodField()
    discount_value = serializers.SerializerMethodField()
    discount_amount = serializers.SerializerMethodField()
    promo_code_text = serializers.SerializerMethodField()
    discount_approved_by = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    customer_phone = serializers.SerializerMethodField()
    customer_address = serializers.SerializerMethodField()
    delivery_notes = serializers.SerializerMethodField()
    sales_customer = serializers.SerializerMethodField()

    def _safe_get(self, obj, attr, default=None):
        """يرجع قيمة الحقل بأمان حتى لو العمود مش موجود في الـ DB بعد"""
        try:
            return getattr(obj, attr, default)
        except Exception:
            return default

    def get_net_total(self, obj):
        try:
            disc = float(self._safe_get(obj, 'discount_amount', 0) or 0)
            return round(float(obj.total_amount) - disc, 2)
        except Exception:
            return float(obj.total_amount)

    def get_discount_type(self, obj):     return self._safe_get(obj, 'discount_type', 'none')
    def get_discount_value(self, obj):    return self._safe_get(obj, 'discount_value', 0)
    def get_discount_amount(self, obj):   return self._safe_get(obj, 'discount_amount', 0)
    def get_promo_code_text(self, obj):   return self._safe_get(obj, 'promo_code_text', '')
    def get_discount_approved_by(self, obj): return self._safe_get(obj, 'discount_approved_by', '')
    def get_customer_name(self, obj):     return self._safe_get(obj, 'customer_name', '')
    def get_customer_phone(self, obj):    return self._safe_get(obj, 'customer_phone', '')
    def get_customer_address(self, obj):  return self._safe_get(obj, 'customer_address', '')
    def get_delivery_notes(self, obj):    return self._safe_get(obj, 'delivery_notes', '')
    def get_sales_customer(self, obj):
        try:
            sc = getattr(obj, 'sales_customer_id', None)
            return sc
        except Exception:
            return None

    class Meta:
        model = POSOrder
        fields = [
            'id', 'opco', 'session', 'order_ref', 'order_type',
            'table_number', 'guest_count', 'total_amount', 'net_total',
            'payment_method', 'status', 'created_at', 'lines',
            'discount_type', 'discount_value', 'discount_amount', 'promo_code_text', 'discount_approved_by',
            'customer_name', 'customer_phone', 'customer_address', 'delivery_notes', 'sales_customer'
        ]
        read_only_fields = ['order_ref', 'net_total']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        
        # Pull read-only customer fields from initial_data to save them in DB if present on the model
        for f in ['customer_name', 'customer_phone', 'customer_address', 'delivery_notes']:
            val = self.initial_data.get(f)
            if val is not None:
                if hasattr(POSOrder, f):
                    validated_data[f] = val
                    
        order = POSOrder.objects.create(**validated_data)
        for line_data in lines_data:
            POSOrderLine.objects.create(order=order, **line_data)
        return order


class POSSessionSerializer(serializers.ModelSerializer):
    terminal_type = serializers.SerializerMethodField()
    terminal_name = serializers.SerializerMethodField()

    class Meta:
        model = POSSession
        fields = '__all__'

    def get_terminal_type(self, obj):
        if obj.terminal:
            return obj.terminal.terminal_type
        return 'DIRECT'

    def get_terminal_name(self, obj):
        if obj.terminal:
            return obj.terminal.name
        return ''


class POSCashTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSCashTransaction
        fields = '__all__'


class POSOrderFallbackSerializer(serializers.ModelSerializer):
    """
    Serializer احتياطي يستخدم فقط الحقول الأصلية القديمة.
    يُستخدم عند فشل POSOrderSerializer بسبب migration لم تُطبَّق بعد.
    """
    lines = POSOrderLineSerializer(many=True)

    class Meta:
        model = POSOrder
        fields = [
            'id', 'opco', 'session', 'order_ref', 'order_type',
            'table_number', 'guest_count', 'total_amount',
            'payment_method', 'status', 'created_at', 'lines',
        ]
        read_only_fields = ['order_ref']


class RestaurantFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantFloor
        fields = ['id', 'opco', 'name', 'number', 'is_active']


class RestaurantTableSerializer(serializers.ModelSerializer):
    floor_name = serializers.CharField(source='floor.name', read_only=True)
    active_order_ref = serializers.CharField(source='active_order.order_ref', read_only=True)
    active_order_total = serializers.DecimalField(source='active_order.total_amount', max_digits=12, decimal_places=2, read_only=True)
    active_order_detail = serializers.SerializerMethodField()

    def get_active_order_detail(self, obj):
        """يجيب تفاصيل الأوردر النشط بأمان حتى لو في columns جديدة مش في الـ DB"""
        if not obj.active_order:
            return None
        try:
            return POSOrderSerializer(obj.active_order, context=self.context).data
        except Exception:
            try:
                return POSOrderFallbackSerializer(obj.active_order, context=self.context).data
            except Exception:
                return {'id': obj.active_order.id, 'order_ref': obj.active_order.order_ref,
                        'total_amount': float(obj.active_order.total_amount), 'status': obj.active_order.status}

    class Meta:
        model = RestaurantTable
        fields = [
            'id', 'opco', 'floor', 'floor_name', 'number', 'seats_limit',
            'current_guests', 'status', 'shape', 'position_x', 'position_y',
            'active_order', 'active_order_ref', 'active_order_total', 'active_order_detail'
        ]


class PromoCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromoCode
        fields = '__all__'
