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

class StorageLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageLocation
        fields = '__all__'

class StorageBinSerializer(serializers.ModelSerializer):
    class Meta:
        model = StorageBin
        fields = '__all__'

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