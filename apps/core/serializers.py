from rest_framework import serializers
from apps.core.models import OpCo, CompanyUser
from apps.wms.models import Plant, StorageLocation, StorageBin
from django.contrib.auth import get_user_model

User = get_user_model()

class OpCoSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S", read_only=True)
    
    class Meta:
        model = OpCo
        fields = [
            'id', 'name', 'code', 'created_at', 'is_holding', 
            'plan', 'tax_id', 'cr_number', 'logo', 'brand_color', 'parent', 'currency'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.parent:
            representation['parent'] = instance.parent.id
        else:
            representation['parent'] = None
        return representation

class PlantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plant
        fields = '__all__'
        validators = []

    def validate(self, attrs):
        code = attrs.get('code', getattr(self.instance, 'code', None))
        name = attrs.get('name', getattr(self.instance, 'name', None))
        opco = attrs.get('opco', getattr(self.instance, 'opco', None))

        request = self.context.get('request')
        is_arabic = request and request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        
        # Check unique constraint for code per opco
        if code and opco:
            qs = Plant.objects.filter(opco=opco, code=code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            existing = qs.first()
            if existing:
                msg = f"الكود مكرر ومستخدم بالفعل مع المنشأة: ({existing.name})" if is_arabic else f"Code is already used by plant: {existing.name}"
                raise serializers.ValidationError({"code": msg})

        # Check unique constraint for name per opco
        if name and opco:
            qs = Plant.objects.filter(opco=opco, name=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            existing = qs.first()
            if existing:
                msg = f"الاسم مكرر، توجد منشأة بنفس الاسم تم إنشاؤها مسبقاً بكود: ({existing.code})" if is_arabic else f"Name is already used by plant with code: {existing.code}"
                raise serializers.ValidationError({"name": msg})

        return attrs

class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'
        validators = []

    def validate(self, attrs):
        code = attrs.get('code', getattr(self.instance, 'code', None))
        name = attrs.get('name', getattr(self.instance, 'name', None))
        plant = attrs.get('plant', getattr(self.instance, 'plant', None))

        request = self.context.get('request')
        is_arabic = request and request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        
        if code and plant:
            qs = StorageLocation.objects.filter(plant=plant, code=code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            existing = qs.first()
            if existing:
                msg = f"الكود مكرر ومستخدم بالفعل مع موقع: ({existing.name})" if is_arabic else f"Code is already used by location: {existing.name}"
                raise serializers.ValidationError({"code": msg})

        if name and plant:
            qs = StorageLocation.objects.filter(plant=plant, name=name)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            existing = qs.first()
            if existing:
                msg = f"الاسم مكرر، يوجد موقع بنفس الاسم مسبقاً بكود: ({existing.code})" if is_arabic else f"Name is already used by location with code: {existing.code}"
                raise serializers.ValidationError({"name": msg})

        return attrs

class StorageBinSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageBin
        fields = '__all__'
        validators = []

    def validate(self, attrs):
        code = attrs.get('code', getattr(self.instance, 'code', None))
        storage_location = attrs.get('storage_location', getattr(self.instance, 'storage_location', None))

        request = self.context.get('request')
        is_arabic = request and request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        
        if code and storage_location:
            qs = StorageBin.objects.filter(storage_location=storage_location, code=code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                msg = f"الكود مكرر داخل هذا الموقع." if is_arabic else "Code is already used in this location."
                raise serializers.ValidationError({"code": msg})

        return attrs

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class CompanyUserSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    company_name = serializers.ReadOnlyField(source='company.name')
    
    class Meta:
        model = CompanyUser
        fields = ['id', 'user', 'user_details', 'company', 'company_name', 'role', 'is_active_session']