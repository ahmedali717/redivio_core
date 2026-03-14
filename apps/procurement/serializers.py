from rest_framework import serializers
# ✅ التصحيح: استيراد الموديلات من نفس التطبيق (.) وليس من core
from .models import Vendor, PurchaseOrder, PurchaseOrderLine

class VendorSerializer(serializers.ModelSerializer):
    extra_data = serializers.JSONField(required=False)
    class Meta:
        model = Vendor
        fields = '__all__'

class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    # هذه الحقول اختيارية وتعتمد على وجودها في موديل Material
    # material_default_plant = serializers.IntegerField(source='material.default_plant.id', read_only=True)
    # material_default_bin = serializers.IntegerField(source='material.default_bin.id', read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ['id', 'material', 'material_name', 'quantity', 'unit_price', 'po']
        read_only_fields = ['id', 'material_name', 'po']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, required=False)
    extra_data = serializers.JSONField(required=False)

    class Meta:
        model = PurchaseOrder
        # 🚀 تم حذف origin_pr من هنا
        fields = ['id', 'opco', 'vendor', 'vendor_name', 'po_number', 'date', 'status', 'extra_data', 'lines']