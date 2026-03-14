from rest_framework import serializers
from .models import Vendor, PurchaseOrder, PurchaseOrderLine

class VendorSerializer(serializers.ModelSerializer):
    extra_data = serializers.JSONField(required=False)
    class Meta:
        model = Vendor
        fields = '__all__'

class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    material_name = serializers.CharField(source='material.name', read_only=True)
    # 🚀 التعديل 1: إضافة الـ SKU عشان يظهر في جدول الاستلام
    material_sku = serializers.CharField(source='material.sku', read_only=True)
    
    # 🚀 التعديل 2: إضافة حقل للرف الافتراضي (اختياري لو محتاجه من الـ Item Master)
    # ملاحظة: هيرجع الـ ID بتاع الرف عشان الـ Vue يختاره تلقائياً
    default_bin = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrderLine
        # ضفنا material_sku و default_bin للقائمة
        fields = ['id', 'material', 'material_name', 'material_sku', 'quantity', 'unit_price', 'po', 'default_bin']
        read_only_fields = ['id', 'material_name', 'material_sku', 'po']

    def get_default_bin(self, obj):
        # لو عندك منطق في الموديل بيحدد الرف الرئيسي للصنف، حطه هنا
        # حالياً هنرجعه None والـ Vue هيدور عليه في الـ company_assignments
        return None

class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    lines = PurchaseOrderLineSerializer(many=True) 
    extra_data = serializers.JSONField(required=False)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'opco', 'vendor', 'vendor_name', 'po_number', 'date', 'status', 'extra_data', 'lines']

    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        for line_data in lines_data:
            PurchaseOrderLine.objects.create(po=purchase_order, **line_data)
        return purchase_order

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                PurchaseOrderLine.objects.create(po=instance, **line_data)
        return instance