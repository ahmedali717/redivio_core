from rest_framework import serializers
from .models import (
    Vendor, PurchaseOrder, PurchaseOrderLine, StockReceipt, StockReceiptLine,
    PurchaseRequisition, PurchaseRequisitionLine, RequestForQuotation, RFQLine,
    SupplierQuotation, SupplierQuotationLine, QuotationComparison, PurchaseReturn, PurchaseReturnLine
)

class VendorSerializer(serializers.ModelSerializer):
    extra_data = serializers.JSONField(required=False)
    class Meta:
        model = Vendor
        fields = '__all__'


# --- 1. Purchase Requisition Serializers (PR) ---
class PurchaseRequisitionLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)

    class Meta:
        model = PurchaseRequisitionLine
        fields = ['id', 'material', 'material_name', 'material_sku', 'quantity', 'notes']


class PurchaseRequisitionSerializer(serializers.ModelSerializer):
    lines = PurchaseRequisitionLineSerializer(many=True)
    requested_by_name = serializers.CharField(source='requested_by.username', read_only=True)
    plant_name = serializers.CharField(source='plant.name', read_only=True)

    class Meta:
        model = PurchaseRequisition
        fields = ['id', 'opco', 'requisition_number', 'plant', 'plant_name', 'requested_by', 'requested_by_name', 'date', 'required_date', 'status', 'notes', 'lines']
        read_only_fields = ['id', 'requisition_number', 'date']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        pr = PurchaseRequisition.objects.create(**validated_data)
        for line in lines_data:
            PurchaseRequisitionLine.objects.create(requisition=pr, **line)
        return pr


# --- 2. RFQ & Supplier Quotation Serializers ---
class RFQLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)

    class Meta:
        model = RFQLine
        fields = ['id', 'material', 'material_name', 'quantity', 'target_price']


class RequestForQuotationSerializer(serializers.ModelSerializer):
    lines = RFQLineSerializer(many=True)
    vendor_names = serializers.SerializerMethodField()

    class Meta:
        model = RequestForQuotation
        fields = ['id', 'opco', 'rfq_number', 'pr', 'date', 'deadline', 'status', 'notes', 'vendors', 'vendor_names', 'lines']
        read_only_fields = ['id', 'rfq_number', 'date']

    def get_vendor_names(self, obj):
        return [v.name for v in obj.vendors.all()]

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        vendors = validated_data.pop('vendors', [])
        rfq = RequestForQuotation.objects.create(**validated_data)
        rfq.vendors.set(vendors)
        for line in lines_data:
            RFQLine.objects.create(rfq=rfq, **line)
        return rfq


class SupplierQuotationLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)

    class Meta:
        model = SupplierQuotationLine
        fields = ['id', 'material', 'material_name', 'quantity', 'unit_price', 'discount_rate', 'tax_rate', 'line_total']
        read_only_fields = ['line_total']


class SupplierQuotationSerializer(serializers.ModelSerializer):
    lines = SupplierQuotationLineSerializer(many=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = SupplierQuotation
        fields = ['id', 'opco', 'quotation_number', 'rfq', 'vendor', 'vendor_name', 'date', 'valid_until', 'delivery_lead_time_days', 'payment_terms', 'total_amount', 'notes', 'lines']
        read_only_fields = ['id', 'quotation_number', 'date']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        sq = SupplierQuotation.objects.create(**validated_data)
        total = 0
        for line in lines_data:
            l_obj = SupplierQuotationLine.objects.create(quotation=sq, **line)
            total += l_obj.line_total
        sq.total_amount = total
        sq.save()
        return sq


# --- 3. Quotation Comparison Serializer ---
class QuotationComparisonSerializer(serializers.ModelSerializer):
    rfq_number = serializers.CharField(source='rfq.rfq_number', read_only=True)
    winning_vendor_name = serializers.CharField(source='winning_vendor.name', read_only=True)
    quotations = SupplierQuotationSerializer(source='rfq.supplier_quotations', many=True, read_only=True)

    class Meta:
        model = QuotationComparison
        fields = ['id', 'opco', 'comparison_number', 'rfq', 'rfq_number', 'date', 'winning_vendor', 'winning_vendor_name', 'winning_quotation', 'status', 'notes', 'quotations']
        read_only_fields = ['id', 'comparison_number', 'date']


# --- 4. Purchase Order & Lines Serializers ---
class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    received_qty = serializers.DecimalField(source='received_quantity', max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = PurchaseOrderLine
        fields = ['id', 'material', 'material_name', 'material_sku', 'quantity', 'received_qty', 'unit_price', 'po']
        read_only_fields = ['id', 'material_name', 'material_sku', 'po', 'received_qty']


class StockReceiptLineSerializer(serializers.ModelSerializer):
    material_id = serializers.IntegerField(required=False)
    material_name = serializers.CharField(source='material.name', read_only=True)
    
    class Meta:
        model = StockReceiptLine
        fields = ['material', 'material_id', 'material_name', 'quantity', 'storage_bin']
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
        po = data.get('po')
        if not po:
            return data
            
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

            StockReceiptLine.objects.create(receipt=receipt, **item)
            
            if receipt.po:
                po_line = PurchaseOrderLine.objects.get(po=receipt.po, material=item['material'])
                po_line.received_quantity += item['quantity']
                po_line.save()
            
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


class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    lines = PurchaseOrderLineSerializer(many=True) 
    extra_data = serializers.JSONField(required=False)
    receipts = StockReceiptSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'opco', 'vendor', 'vendor_name', 'pr', 'rfq', 'comparison', 'po_number', 'date', 'status', 'extra_data', 'lines', 'receipts']
        read_only_fields = ['id', 'po_number', 'date']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        for line_data in lines_data:
            PurchaseOrderLine.objects.create(po=purchase_order, **line_data)
        return purchase_order


# --- 5. Purchase Return (RTV) Serializers ---
class PurchaseReturnLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)

    class Meta:
        model = PurchaseReturnLine
        fields = ['id', 'material', 'material_name', 'quantity', 'unit_price']


class PurchaseReturnSerializer(serializers.ModelSerializer):
    lines = PurchaseReturnLineSerializer(many=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta:
        model = PurchaseReturn
        fields = ['id', 'opco', 'return_number', 'vendor', 'vendor_name', 'po', 'grn', 'date', 'status', 'reason', 'total_amount', 'lines']
        read_only_fields = ['id', 'return_number', 'date']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        rtv = PurchaseReturn.objects.create(**validated_data)
        for line in lines_data:
            PurchaseReturnLine.objects.create(return_doc=rtv, **line)
        return rtv