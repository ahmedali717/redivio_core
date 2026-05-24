# Generated manually to align dependencies

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0004_stockmove_payment_method_stockmove_sales_price_and_more'),
        ('core', '0009_opco_contact_name_opco_contact_phone_and_more'),
        ('procurement', '0001_initial'),
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stockmove',
            name='date',
        ),
        migrations.AddField(
            model_name='stockmove',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='stockmove',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='stockmove',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='procurement.vendor'),
        ),
        migrations.AddField(
            model_name='stockmove',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.customer'),
        ),
    ]
