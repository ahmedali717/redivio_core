# Generated manually

from django.db import migrations, models
from django.conf import settings

class Migration(migrations.Migration):

    dependencies = [
        ('restaurant_pos', '0003_posterminal_possession_terminal'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='posterminal',
            name='allowed_users',
            field=models.ManyToManyField(
                blank=True,
                help_text='المستخدمون المسموح لهم بفتح نقطة البيع هذه',
                related_name='allowed_pos_terminals',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
