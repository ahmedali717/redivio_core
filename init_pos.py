import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'redivio_project.settings')
django.setup()

from apps.restaurant_pos.models import POSSession
from apps.core.models import OpCo

def init_pos():
    opco = OpCo.objects.first()
    if opco:
        session, created = POSSession.objects.get_or_create(
            id=1,
            defaults={
                'opco': opco,
                'cashier_name': 'Admin Cashier',
                'is_closed': False
            }
        )
        if created:
            print("POS Session 1 created for testing.")
        else:
            print("POS Session 1 already exists.")
    else:
        print("No OpCo found. Please create a company first.")

if __name__ == "__main__":
    init_pos()
