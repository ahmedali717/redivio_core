from rest_framework import serializers
from .models import Customer, SalesOrder, SalesOrderLine, SalesInvoice, CustomerPayment, StockDelivery, StockDeliveryLine

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

class SalesOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.name')
    material_sku = serializers.ReadOnlyField(source='material.sku')
    price = serializers.DecimalField(source='unit_price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = SalesOrderLine
        fields = [
            'id', 'so', 'material', 'material_name', 'material_sku', 'uom', 'quantity', 'unit_price', 'price',
            'discount_rate', 'discount_amount', 'gross_total', 'total', 'tax_rate', 'tax_amount',
            'shipped_quantity', 'billed_quantity', 'remaining_quantity', 'unbilled_quantity',
            'storage_bin', 'notes', 'extra_data'
        ]
        read_only_fields = [
            'id', 'so', 'material_name', 'material_sku', 'price',
            'gross_total', 'total', 'tax_amount', 'discount_amount',
            'shipped_quantity', 'billed_quantity', 'remaining_quantity', 'unbilled_quantity'
        ]

class StockDeliveryLineSerializer(serializers.ModelSerializer):
    material_id = serializers.IntegerField(required=False)
    material_name = serializers.ReadOnlyField(source='material.name')
    material_sku = serializers.ReadOnlyField(source='material.sku')
    storage_bin_code = serializers.ReadOnlyField(source='storage_bin.bin_code')
    
    class Meta:
        model = StockDeliveryLine
        fields = ['id', 'material', 'material_id', 'material_name', 'material_sku', 'quantity', 'storage_bin', 'storage_bin_code']
        extra_kwargs = {
            'material': {'required': False, 'allow_null': True},
            'storage_bin': {'required': False, 'allow_null': True},
        }

class StockDeliverySerializer(serializers.ModelSerializer):
    items = StockDeliveryLineSerializer(many=True)
    manual_contact_name = serializers.CharField(required=False, allow_blank=True)
    customer_name = serializers.ReadOnlyField(source='so.customer.name')
    so_number = serializers.ReadOnlyField(source='so.so_number')
    
    class Meta:
        model = StockDelivery
        fields = [
            'id', 'opco', 'delivery_number', 'so', 'so_number', 'customer_name', 'date', 'created_by', 
            'tracking_number', 'driver_name', 'vehicle_plate', 'delivery_address', 
            'notes', 'extra_data', 'items', 'manual_contact_name'
        ]
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
                bin_obj = StorageBin.objects.filter(plant__opco=delivery.opco).first()

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

class SalesInvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    so_number = serializers.ReadOnlyField(source='sales_order.so_number')
    is_posted = serializers.SerializerMethodField()

    class Meta:
        model = SalesInvoice
        fields = '__all__'

    def get_is_posted(self, obj):
        if obj.extra_data and obj.extra_data.get('is_posted'):
            return True
        try:
            from apps.accounting.models import GLEntry
            return GLEntry.objects.filter(opco=obj.opco, voucher_no=obj.invoice_number, is_cancelled=False).exists()
        except Exception:
            return False

class SalesOrderSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True, required=False)
    customer_name = serializers.ReadOnlyField(source='customer.name')
    deliveries = StockDeliverySerializer(many=True, read_only=True)
    invoices = SalesInvoiceSerializer(many=True, read_only=True)
    deliveries_count = serializers.SerializerMethodField()
    invoices_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'opco', 'so_number', 'customer', 'customer_name', 'date', 
            'delivery_date', 'customer_po_reference', 'customer_po_date',
            'currency', 'exchange_rate', 'payment_terms', 'shipping_terms',
            'shipping_address', 'billing_address', 'status',
            'subtotal', 'discount_rate', 'discount_amount', 'total_amount', 'tax_amount', 'grand_total',
            'terms_and_conditions', 'notes', 'extra_data',
            'lines', 'deliveries', 'invoices', 'deliveries_count', 'invoices_count'
        ]

    def get_deliveries_count(self, obj):
        return obj.deliveries.count()

    def get_invoices_count(self, obj):
        return obj.invoices.count()

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        so = SalesOrder.objects.create(**validated_data)
        for line in lines_data:
            material = line.get('material')
            if isinstance(material, dict):
                line['material_id'] = material.get('id')
                line.pop('material', None)
            SalesOrderLine.objects.create(so=so, **line)
        so.calculate_totals()
        return so

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None and instance.status in ['DRAFT', 'draft']:
            instance.lines.all().delete()
            for line in lines_data:
                material = line.get('material')
                if isinstance(material, dict):
                    line['material_id'] = material.get('id')
                    line.pop('material', None)
                SalesOrderLine.objects.create(so=instance, **line)
        instance.calculate_totals()
        return instance

class CustomerPaymentSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    class Meta:
        model = CustomerPayment
        fields = '__all__'


# --- Sales Return Serializers ---
from .models import SalesReturn, SalesReturnLine

class SalesReturnLineSerializer(serializers.ModelSerializer):
    material_name = serializers.ReadOnlyField(source='material.name')

    class Meta:
        model = SalesReturnLine
        fields = ['id', 'material', 'material_name', 'quantity', 'unit_price']


class SalesReturnSerializer(serializers.ModelSerializer):
    lines = SalesReturnLineSerializer(many=True)
    customer_name = serializers.ReadOnlyField(source='customer.name')

    class Meta:
        model = SalesReturn
        fields = ['id', 'opco', 'return_number', 'customer', 'customer_name', 'sales_order', 'invoice', 'date', 'status', 'reason', 'total_amount', 'lines']
        read_only_fields = ['id', 'return_number', 'date']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        rfc = SalesReturn.objects.create(**validated_data)
        for line in lines_data:
            SalesReturnLine.objects.create(return_doc=rfc, **line)
        return rfc