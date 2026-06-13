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
    material_id = serializers.IntegerField(required=False)
    
    class Meta:
        model = StockReceiptLine
        fields = ['material', 'material_id', 'quantity', 'storage_bin']
        extra_kwargs = {
            'material': {'required': False, 'allow_null': True},
            'storage_bin': {'required': False, 'allow_null': True},
        }

class StockReceiptSerializer(serializers.ModelSerializer):
    items = StockReceiptLineSerializer(many=True)
    manual_contact_name = serializers.CharField(required=False, allow_blank=True)
    
    class Meta:
        model = StockReceipt
        fields = ['id', 'receipt_number', 'po', 'opco', 'date', 'items', 'manual_contact_name']
        read_only_fields = ['id', 'receipt_number', 'date']
        extra_kwargs = {
            'po': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        """
        تعديل: التحقق من PO فقط إذا كان موجوداً (Modular Mode)
        """
        po = data.get('po')
        if not po:
            return data # تخطي التحقق في حالة الـ Standalone
            
        items = data['items']
        for item in items:
            material = item.get('material')
            if not material: continue
            
            qty_to_receive = item['quantity']
            try:
                po_line = PurchaseOrderLine.objects.get(po=po, material=material)
                remaining_balance = po_line.quantity - po_line.received_quantity
                if qty_to_receive > remaining_balance:
                    raise serializers.ValidationError({
                        "items": f"الصنف {material.name} الكمية المطلوبة ({qty_to_receive}) تتخطى المتبقي ({remaining_balance})"
                    })
            except PurchaseOrderLine.DoesNotExist:
                raise serializers.ValidationError({"items": f"الصنف {material.name} غير موجود في أمر التوريد!"})
        return data

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        manual_contact = validated_data.pop('manual_contact_name', None)
        receipt = StockReceipt.objects.create(**validated_data)
        
        from django.apps import apps
        StockMove = apps.get_model('wms', 'StockMove')
        
        for item in items_data:
            material_id = item.pop('material_id', None)
            material = item.get('material')
            if not material and material_id:
                from apps.item_master.models import Material
                material = Material.objects.get(id=material_id)
                item['material'] = material

            # 1. إنشاء سطر الاستلام
            StockReceiptLine.objects.create(receipt=receipt, **item)
            
            # 2. تحديث PO Line فقط لو فيه PO
            if receipt.po:
                po_line = PurchaseOrderLine.objects.get(po=receipt.po, material=item['material'])
                po_line.received_quantity += item['quantity']
                po_line.save()
            
            # 3. تسجيل حركة مخزنية
            # البحث عن أول رف متاح لو مفيش رف محدد (للوضع اليدوي)
            bin_obj = item.get('storage_bin')
            if not bin_obj:
                from apps.wms.models import StorageBin
                bin_obj = StorageBin.objects.filter(plant__opco=receipt.opco).first()

            StockMove.objects.create(
                opco=receipt.opco,
                material=item['material'],
                quantity=item['quantity'],
                move_type='IN',
                dest_bin=bin_obj,
                reference=f"GRN: {receipt.receipt_number}",
                vendor_name=manual_contact or (receipt.po.vendor.name if receipt.po else "")
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