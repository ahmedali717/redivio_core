from rest_framework import serializers
from .models import Customer, SalesOrder, SalesOrderLine, SalesInvoice, CustomerPayment

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class SalesOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.name')
    class Meta:
        model = SalesOrderLine
        fields = ['id', 'so', 'material', 'material_name', 'quantity', 'unit_price', 'total']

class SalesOrderSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    customer_name = serializers.ReadOnlyField(source='customer.name')
    
    class Meta:
        model = SalesOrder
        fields = ['id', 'opco', 'so_number', 'customer', 'customer_name', 'date', 'status', 'total_amount', 'tax_amount', 'grand_total', 'notes', 'lines']

class SalesInvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    class Meta:
        model = SalesInvoice
        fields = '__all__'

class CustomerPaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    class Meta:
        model = CustomerPayment
        fields = '__all__'