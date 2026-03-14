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
    lines = PurchaseOrderLineSerializer(many=True) # شيل required=False عشان نضمن وجود أصناف
    extra_data = serializers.JSONField(required=False)

    class Meta:
        model = PurchaseOrder
        fields = ['id', 'opco', 'vendor', 'vendor_name', 'po_number', 'date', 'status', 'extra_data', 'lines']

    def create(self, validated_data):
        # 🚀 1. استخراج بيانات السطور لوحدها
        lines_data = validated_data.pop('lines', [])
        
        # 🚀 2. حفظ أمر التوريد الرئيسي أولاً
        purchase_order = PurchaseOrder.objects.create(**validated_data)
        
        # 🚀 3. حفظ كل سطر وربطه بأمر التوريد اللي لسه كريتناه
        for line_data in lines_data:
            PurchaseOrderLine.objects.create(po=purchase_order, **line_data)
            
        return purchase_order

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # تحديث الحقول الأساسية
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # تحديث السطور (مسح القديم وإضافة الجديد)
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                PurchaseOrderLine.objects.create(po=instance, **line_data)
        
        return instance