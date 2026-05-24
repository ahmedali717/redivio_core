from rest_framework import serializers
from .models import POSTerminal, POSOrder, POSOrderLine, POSSession, Recipe, RecipeItem, POSCashTransaction, RestaurantFloor, RestaurantTable

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
    
    class Meta:
        model = POSOrder
        fields = [
            'id', 'opco', 'session', 'order_ref', 'order_type', 
            'table_number', 'guest_count', 'total_amount', 'payment_method', 'status', 'created_at', 'lines'
        ]
        read_only_fields = ['order_ref']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
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


class RestaurantFloorSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantFloor
        fields = ['id', 'opco', 'name', 'number', 'is_active']


class RestaurantTableSerializer(serializers.ModelSerializer):
    floor_name = serializers.CharField(source='floor.name', read_only=True)
    active_order_ref = serializers.CharField(source='active_order.order_ref', read_only=True)
    active_order_total = serializers.DecimalField(source='active_order.total_amount', max_digits=12, decimal_places=2, read_only=True)
    active_order_detail = POSOrderSerializer(source='active_order', read_only=True)

    class Meta:
        model = RestaurantTable
        fields = [
            'id', 'opco', 'floor', 'floor_name', 'number', 'seats_limit',
            'current_guests', 'status', 'shape', 'position_x', 'position_y',
            'active_order', 'active_order_ref', 'active_order_total', 'active_order_detail'
        ]

