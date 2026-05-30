from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_opco_is_inventory_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan', models.CharField(choices=[('starter', 'Starter'), ('business', 'Business'), ('professional', 'Professional'), ('enterprise', 'Enterprise')], max_length=20)),
                ('payment_method', models.CharField(choices=[('stripe', 'Stripe (Credit Card)'), ('paymob', 'Paymob (Wallet/Fawry)')], max_length=20)),
                ('payment_status', models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('amount', models.FloatField(default=0.0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('opco', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscription_requests', to='core.opco')),
            ],
            options={
                'verbose_name': 'طلب اشتراك',
                'verbose_name_plural': 'طلبات الاشتراكات',
            },
        ),
    ]
