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
        fields = ['id', 'so', 'material', 'material_name', 'quantity', 'unit_price', 'total', 'shipped_quantity', 'billed_quantity', 'remaining_quantity', 'unbilled_quantity']

class StockDeliveryLineSerializer(serializers.ModelSerializer):
    material_id = serializers.IntegerField(required=False)
    material_name = serializers.ReadOnlyField(source='material.name')
    
    class Meta:
        model = StockDeliveryLine
        fields = ['id', 'material', 'material_id', 'material_name', 'quantity', 'storage_bin']
        extra_kwargs = {
            'material': {'required': False, 'allow_null': True},
            'storage_bin': {'required': False, 'allow_null': True},
        }

class StockDeliverySerializer(serializers.ModelSerializer):
    items = StockDeliveryLineSerializer(many=True)
    manual_contact_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = StockDelivery
        fields = ['id', 'opco', 'delivery_number', 'so', 'date', 'created_by', 'items', 'manual_contact_name']
        read_only_fields = ['id', 'delivery_number', 'date', 'created_by']
        extra_kwargs = {
            'so': {'required': False, 'allow_null': True},
        }

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        manual_contact = validated_data.pop('manual_contact_name', None)
        delivery = StockDelivery.objects.create(**validated_data)
        
        from django.apps import apps
        StockMove = apps.get_model('wms', 'StockMove')
        
        for item in items_data:
            material_id = item.pop('material_id', None)
            material = item.get('material')
            if not material and material_id:
                from apps.item_master.models import Material
                material = Material.objects.get(id=material_id)
                item['material'] = material

            # 1. إنشاء سطر الصرف
            StockDeliveryLine.objects.create(delivery=delivery, **item)
            
            # 2. تحديث التراكمي في الـ SO Line فقط لو فيه SO
            if delivery.so:
                try:
                    so_line = SalesOrderLine.objects.get(so=delivery.so, material=item['material'])
                    so_line.shipped_quantity += item['quantity']
                    so_line.save()
                except SalesOrderLine.DoesNotExist:
                    pass
            
            # 3. تسجيل حركة مخزنية (OUT)
            bin_obj = item.get('storage_bin')
            if not bin_obj:
                from apps.wms.models import StorageBin
                # البحث عن أول رف متاح به كمية من هذا الصنف أو أي رف
                bin_obj = StorageBin.objects.filter(storage_location__plant__opco=delivery.opco).first()

            StockMove.objects.create(
                opco=delivery.opco,
                material=item['material'],
                quantity=item['quantity'],
                move_type='OUT',
                source_bin=bin_obj,
                reference=f"DN: {delivery.delivery_number}",
                vendor_name=manual_contact or (delivery.so.customer.name if delivery.so else "")
            )
            
        if delivery.so:
            delivery.so.save()
        return delivery

class SalesOrderSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    customer_name = serializers.ReadOnlyField(source='customer.name')
    deliveries = StockDeliverySerializer(many=True, read_only=True) # تم تعريفه الآن في الأعلى
    
    class Meta:
        model = SalesOrder
        fields = ['id', 'opco', 'so_number', 'customer', 'customer_name', 'date', 'status', 'total_amount', 'tax_amount', 'grand_total', 'notes', 'lines', 'deliveries']

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