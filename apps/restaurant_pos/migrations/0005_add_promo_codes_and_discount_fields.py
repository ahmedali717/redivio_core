from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant_pos', '0004_posterminal_allowed_users'),
        ('core', '0001_initial'),
    ]

    operations = [
        # 1. إنشاء جدول PromoCode
        migrations.CreateModel(
            name='PromoCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='كود العرض (مثال: WELCOME10)', max_length=50)),
                ('description', models.CharField(blank=True, help_text='وصف العرض', max_length=200, null=True)),
                ('discount_type', models.CharField(
                    choices=[('percentage', 'نسبة مئوية (%)'), ('fixed', 'قيمة ثابتة (Fixed Amount)')],
                    default='percentage',
                    max_length=20
                )),
                ('discount_value', models.DecimalField(decimal_places=2, help_text='قيمة الخصم (نسبة أو مبلغ)', max_digits=10)),
                ('min_order_amount', models.DecimalField(decimal_places=2, default=0.0, help_text='الحد الأدنى للطلب لتطبيق الكود', max_digits=10)),
                ('max_uses', models.IntegerField(default=0, help_text='أقصى عدد مرات الاستخدام (0 = غير محدود)')),
                ('used_count', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('expires_at', models.DateTimeField(blank=True, help_text='تاريخ انتهاء العرض (اختياري)', null=True)),
                ('opco', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='promo_codes',
                    to='core.opco'
                )),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='promocode',
            unique_together={('opco', 'code')},
        ),

        # 2. إضافة حقول الخصم لـ POSOrder
        migrations.AddField(
            model_name='posorder',
            name='discount_type',
            field=models.CharField(
                choices=[('none', 'بدون خصم'), ('percentage', 'نسبة مئوية (%)'), ('fixed', 'قيمة ثابتة (Fixed Amount)')],
                default='none',
                max_length=20
            ),
        ),
        migrations.AddField(
            model_name='posorder',
            name='discount_value',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='قيمة الخصم (% أو مبلغ)', max_digits=10),
        ),
        migrations.AddField(
            model_name='posorder',
            name='discount_amount',
            field=models.DecimalField(decimal_places=2, default=0.0, help_text='قيمة الخصم الفعلية بالجنيه', max_digits=10),
        ),
        migrations.AddField(
            model_name='posorder',
            name='promo_code',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='orders',
                to='restaurant_pos.promocode'
            ),
        ),
        migrations.AddField(
            model_name='posorder',
            name='promo_code_text',
            field=models.CharField(blank=True, help_text='نص كود العرض المستخدم', max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='posorder',
            name='discount_approved_by',
            field=models.CharField(blank=True, help_text='اسم من وافق على الخصم', max_length=100, null=True),
        ),
    ]
