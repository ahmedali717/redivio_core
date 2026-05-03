from rest_framework import serializers
from .models import POSOrder, POSOrderLine, POSSession, Recipe, RecipeItem, POSCashTransaction

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
            'table_number', 'total_amount', 'status', 'created_at', 'lines'
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        order = POSOrder.objects.create(**validated_data)
        for line_data in lines_data:
            POSOrderLine.objects.create(order=order, **line_data)
        return order

class POSSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSSession
        fields = '__all__'

class POSCashTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = POSCashTransaction
        fields = '__all__'
