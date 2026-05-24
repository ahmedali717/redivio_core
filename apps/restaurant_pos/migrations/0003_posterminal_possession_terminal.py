# Generated manually

from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('restaurant_pos', '0002_restaurantfloor_restauranttable'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='POSTerminal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='اسم جهاز نقطة البيع', max_length=100)),
                ('code', models.CharField(help_text='كود نقطة البيع', max_length=20)),
                ('terminal_type', models.CharField(choices=[('DIRECT', 'Direct Sales (مبيعات مباشرة)'), ('RESTAURANT', 'Restaurant (مطعم)')], default='DIRECT', help_text='طبيعة التشغيل', max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('opco', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pos_terminals', to='core.opco')),
            ],
            options={
                'unique_together': {('opco', 'code')},
            },
        ),
        migrations.AddField(
            model_name='possession',
            name='terminal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='restaurant_pos.posterminal'),
        ),
    ]
