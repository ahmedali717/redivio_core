from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_opco_brand_color'),
    ]

    operations = [
        migrations.AlterField(
            model_name='opco',
            name='plan',
            field=models.CharField(
                choices=[
                    ('starter', 'Starter'),
                    ('business', 'Business'),
                    ('professional', 'Professional'),
                    ('enterprise', 'Enterprise'),
                    ('free', 'Free'),
                    ('pro', 'Pro'),
                ],
                default='starter',
                max_length=20
            ),
        ),
    ]
