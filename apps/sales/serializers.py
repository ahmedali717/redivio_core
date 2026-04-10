from rest_framework import serializers
from .models import Customer, SalesOrder, SalesOrderLine, SalesInvoice, CustomerPayment, StockDelivery, StockDeliveryLine

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class SalesOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.name')
    class Meta:
        model = SalesOrderLine
        fields = ['id', 'so', 'material', 'material_name', 'quantity', 'unit_price', 'total', 'shipped_quantity', 'remaining_quantity']

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

class StockDeliveryLineSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.name')
    class Meta:
        model = StockDeliveryLine
        fields = ['id', 'material', 'material_name', 'quantity', 'storage_bin']

class StockDeliverySerializer(serializers.ModelSerializer):
    items = StockDeliveryLineSerializer(many=True) # جعلها قابلة للكتابة
    
    class Meta:
        model = StockDelivery
        fields = ['id', 'opco', 'delivery_number', 'so', 'date', 'created_by', 'items']
        read_only_fields = ['id', 'delivery_number', 'date', 'created_by']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        delivery = StockDelivery.objects.create(**validated_data)
        
        from django.apps import apps
        StockMove = apps.get_model('wms', 'StockMove')
        
        for item in items_data:
            # 1. إنشاء سطر الصرف
            StockDeliveryLine.objects.create(delivery=delivery, **item)
            
            # 2. تحديث التراكمي في الـ SO Line
            so_line = SalesOrderLine.objects.get(so=delivery.so, material=item['material'])
            so_line.shipped_quantity += item['quantity']
            so_line.save()
            
            # 3. تسجيل حركة مخزنية (OUT)
            StockMove.objects.create(
                opco=delivery.opco,
                material=item['material'],
                quantity=item['quantity'],
                move_type='OUT',
                source_bin=item['storage_bin'],
                reference=f"DN: {delivery.delivery_number}"
            )
            
        # 4. تحديث حالة أمر البيع لو تم شحن كل الأصناف
        so = delivery.so
        if all(line.shipped_quantity >= line.quantity for line in so.lines.all()):
            so.status = 'DELIVERED'
            so.save()
            # إنشاء فاتورة تلقائياً
            if hasattr(so, 'create_invoice'):
                so.create_invoice()
        else:
            so.status = 'SHIPPED'
            so.save()

        return delivery