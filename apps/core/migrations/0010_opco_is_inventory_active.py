from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_opco_contact_name_opco_contact_phone_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='opco',
            name='is_inventory_active',
            field=models.BooleanField(
                default=False,
                help_text="تفعيل هذا الخيار يجمد كافة حركات المخزون والمبيعات حتى إتمام الجرد",
                verbose_name="جرد مخزني نشط؟"
            ),
        ),
    ]
