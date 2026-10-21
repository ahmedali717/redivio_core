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
            'plan', 'tax_id', 'cr_number', 'logo', 'brand_color', 'parent', 'currency',
            'system_mode', 'purchased_modules'
        ]


    def validate(self, attrs):
        system_mode = attrs.get('system_mode', getattr(self.instance, 'system_mode', 'modular') if self.instance else 'modular')
        purchased_modules = attrs.get('purchased_modules', getattr(self.instance, 'purchased_modules', []) if self.instance else [])
        
        # Safely parse JSON string if sent from FormData
        if isinstance(purchased_modules, str):
            import json
            try:
                purchased_modules = json.loads(purchased_modules)
                attrs['purchased_modules'] = purchased_modules
            except Exception:
                purchased_modules = []
                attrs['purchased_modules'] = []

        # Determine effective plan (inherit from holding company if subsidiary)
        holding_opco = None
        if self.instance:
            if self.instance.is_holding or not self.instance.parent:
                holding_opco = self.instance
            else:
                curr = self.instance
                while curr.parent:
                    curr = curr.parent
                holding_opco = curr
        
        plan = (holding_opco.plan if holding_opco and holding_opco.plan else getattr(self.instance, 'plan', 'enterprise') if self.instance else 'enterprise')
        if not plan:
            plan = 'enterprise'
        plan = str(plan).lower()

        request = self.context.get('request')
        is_arabic = request and request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        is_superuser = request and request.user and getattr(request.user, 'is_superuser', False)

        if not is_superuser and plan not in ['enterprise', 'pro', 'professional']:
            if plan in ['starter', 'free']:
                if system_mode == 'modular':
                    raise serializers.ValidationError({
                        "system_mode": "خطة المبتدئ تدعم فقط نمط موديول مستقل." if is_arabic else "Starter plan supports Stand Alone mode only."
                    })
                if isinstance(purchased_modules, list) and len(purchased_modules) > 1:
                    raise serializers.ValidationError({
                        "purchased_modules": "خطة المبتدئ تسمح بموديول واحد فقط." if is_arabic else "Starter plan supports only one active module."
                    })
            elif plan == 'business':
                if isinstance(purchased_modules, list) and len(purchased_modules) > 3:
                    raise serializers.ValidationError({
                        "purchased_modules": "خطة الأعمال تسمح بحد أقصى 3 موديولات." if is_arabic else "Business plan supports up to 3 active modules."
                    })

        return attrs

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
    plant = serializers.PrimaryKeyRelatedField(queryset=Plant.objects.all(), required=False, allow_null=True)
    code = serializers.CharField(required=False)

    class Meta:
        model = StorageBin
        fields = '__all__'
        validators = []

    def validate(self, attrs):
        code = attrs.get('code', getattr(self.instance, 'code', None))
        plant = attrs.get('plant', getattr(self.instance, 'plant', None))

        request = self.context.get('request')
        is_arabic = request and request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        
        if code and plant:
            qs = StorageBin.objects.filter(plant=plant, code=code)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                msg = f"الكود مكرر داخل هذه المنشأة." if is_arabic else "Code is already used in this plant."
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


# --- Odoo Chatter & Activities Serializers ---
from apps.core.models import ChatterMessage, ActivitySchedule
from django.contrib.contenttypes.models import ContentType

class ChatterMessageSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.username', read_only=True)
    created_at_formatted = serializers.DateTimeField(source='created_at', format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = ChatterMessage
        fields = [
            'id', 'opco', 'author', 'author_name', 'author_username', 
            'content_type', 'object_id', 'message_type', 'body', 
            'metadata', 'created_at', 'created_at_formatted'
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['author'] = request.user
            if not validated_data.get('author_name'):
                validated_data['author_name'] = request.user.get_full_name() or request.user.username
        return super().create(validated_data)


class ActivityScheduleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)

    class Meta:
        model = ActivitySchedule
        fields = [
            'id', 'opco', 'created_by', 'created_by_name', 'assigned_to', 'assigned_to_name',
            'content_type', 'object_id', 'activity_type', 'summary', 'note', 
            'due_date', 'status', 'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'created_at']