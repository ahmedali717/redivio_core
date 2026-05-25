import os
import sys
import django

# Set up Django environment
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "redivio_project.settings")
django.setup()

from apps.core.models import OpCo
from apps.core.serializers import OpCoSerializer
from django.http import QueryDict

# Create a mock QueryDict simulating the frontend form-data PATCH request
qd = QueryDict('', mutable=True)
qd['name'] = 'Test Company'
qd['is_holding'] = 'false'
qd['tax_id'] = '123456789'
qd['cr_number'] = '987654321'
qd['system_mode'] = 'modular'
qd['purchased_modules'] = '["wms", "sales"]'
qd['code'] = 'TEST'

# Let's get or create an OpCo to test PATCH
owner_model = django.contrib.auth.get_user_model()
owner, _ = owner_model.objects.get_or_create(username='testowner', defaults={'email':'test@example.com'})
opco, _ = OpCo.objects.get_or_create(code='TEST', defaults={'name': 'Test Company', 'owner': owner})

print("Testing with QueryDict:")
serializer = OpCoSerializer(opco, data=qd, partial=True)
if serializer.is_valid():
    print("Valid data:", serializer.validated_data)
else:
    print("Errors:", serializer.errors)
