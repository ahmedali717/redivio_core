from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant_pos', '0005_add_promo_codes_and_discount_fields'),
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='posorder',
            name='customer_name',
            field=models.CharField(blank=True, help_text='اسم عميل التوصيل', max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='customer_phone',
            field=models.CharField(blank=True, help_text='رقم تليفون العميل', max_length=30, null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='customer_address',
            field=models.TextField(blank=True, help_text='عنوان التوصيل', null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='delivery_notes',
            field=models.TextField(blank=True, help_text='ملاحظات التوصيل', null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='sales_customer',
            field=models.ForeignKey(
                blank=True,
                help_text='العميل المرتبط في موديول المبيعات',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='pos_delivery_orders',
                to='sales.customer',
            ),
        ),
    ]
