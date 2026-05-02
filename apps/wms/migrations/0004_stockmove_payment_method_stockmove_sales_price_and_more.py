from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0003_alter_storagebin_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockmove',
            name='payment_method',
            field=models.CharField(default='CASH', max_length=50),
        ),
        migrations.AddField(
            model_name='stockmove',
            name='sales_price',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name='stockmove',
            name='tax_rate',
            field=models.DecimalField(decimal_places=2, default=15, max_digits=5),
        ),
    ]
