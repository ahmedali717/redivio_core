from rest_framework import serializers
from .models import Vendor, PurchaseOrder, PurchaseOrderLine, StockReceipt, StockReceiptLine

class VendorSerializer(serializers.ModelSerializer):
    extra_data = serializers.JSONField(required=False)
    class Meta:
        model = Vendor
        fields = '__all__'

class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    # 🚀 التعديل: إضافة الحقل الجديد عشان الـ Vue يعرف إحنا استلمنا كام قبل كدة
    received_qty = serializers.DecimalField(source='received_quantity', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrderLine
        fields = ['id', 'material', 'material_name', 'material_sku', 'quantity', 'received_qty', 'unit_price', 'po']
        read_only_fields = ['id', 'material_name', 'material_sku', 'po', 'received_qty']

# --- 🚀 سيريالايزر الـ GRN الجديد ---

class StockReceiptLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockReceiptLine
        fields = ['material', 'quantity', 'storage_bin']

class StockReceiptSerializer(serializers.ModelSerializer):
    items = StockReceiptLineSerializer(many=True)
    
    class Meta:
        model = StockReceipt
        fields = ['id', 'receipt_number', 'po', 'opco', 'date', 'items']
        read_only_fields = ['id', 'receipt_number', 'date']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        receipt = StockReceipt.objects.create(**validated_data)
        
        # ربط الـ Models ديناميكياً لتجنب الـ Circular Import لو حصل
        from django.apps import apps
        StockMove = apps.get_model('wms', 'StockMove')
        
        for item in items_data:
            # 1. إنشاء سطر الاستلام
            StockReceiptLine.objects.create(receipt=receipt, **item)
            
            # 2. تحديث التراكمي في الـ PO Line عشان الـ Progress Bar والحسابات
            po_line = PurchaseOrderLine.objects.get(po=receipt.po, material=item['material'])
            po_line.received_quantity += item['quantity']
            po_line.save()
            
            # 3. تسجيل حركة مخزنية (Stock Move) لزيادة الأرصدة فوراً
            StockMove.objects.create(
                opco=receipt.opco,
                material=item['material'],
                quantity=item['quantity'],
                move_type='IN',
                dest_bin=item['storage_bin'],
                reference=f"GRN: {receipt.receipt_number} (PO: {receipt.po.po_number})"
            )
            
        return receipt

# --- 🚀 نهاية سيريالايزر الـ GRN ---

class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    lines = PurchaseOrderLineSerializer(many=True) 
    extra_data = serializers.JSONField(required=False)
    # لعرض حركات الاستلام المرتبطة بهذا الـ PO
    receipts = StockReceiptSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'opco', 'vendor', 'vendor_name', 'po_number', 'date', 'status', 'extra_data', 'lines', 'receipts']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        for line_data in lines_data:
            PurchaseOrderLine.objects.create(po=purchase_order, **line_data)
        return purchase_order