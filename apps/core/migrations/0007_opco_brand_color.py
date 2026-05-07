from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_opco_is_system_root_putawayrule'),
    ]

    operations = [
        migrations.AddField(
            model_name='opco',
            name='brand_color',
            field=models.CharField(default='#6366f1', max_length=20, verbose_name='لون العلامة التجارية'),
        ),
    ]
