from django.db import migrations, models

def make_core_db_changes(apps, schema_editor):
    connection = schema_editor.connection
    
    # Check tables and columns safely
    table_names = connection.introspection.table_names()
    
    if 'core_opco' in table_names:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(core_opco)")
        columns = [row[1] for row in cursor.fetchall()]
        
        OpCo = apps.get_model('core', 'OpCo')
        
        if 'contact_name' not in columns:
            schema_editor.add_field(OpCo, OpCo._meta.get_field('contact_name'))
        if 'contact_phone' not in columns:
            schema_editor.add_field(OpCo, OpCo._meta.get_field('contact_phone'))
        if 'industry' not in columns:
            schema_editor.add_field(OpCo, OpCo._meta.get_field('industry'))
        if 'database_name' not in columns:
            schema_editor.add_field(OpCo, OpCo._meta.get_field('database_name'))
        if 'system_mode' not in columns:
            schema_editor.add_field(OpCo, OpCo._meta.get_field('system_mode'))
        if 'purchased_modules' not in columns:
            schema_editor.add_field(OpCo, OpCo._meta.get_field('purchased_modules'))
            
    if 'core_companyuser' in table_names:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(core_companyuser)")
        cu_columns = [row[1] for row in cursor.fetchall()]
        
        CompanyUser = apps.get_model('core', 'CompanyUser')
        if 'role' not in cu_columns:
            schema_editor.add_field(CompanyUser, CompanyUser._meta.get_field('role'))

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_opco_plan'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name='opco',
                    name='contact_name',
                    field=models.CharField(blank=True, max_length=150, null=True, verbose_name='اسم المشترك'),
                ),
                migrations.AddField(
                    model_name='opco',
                    name='contact_phone',
                    field=models.CharField(blank=True, max_length=20, null=True, verbose_name='رقم الهاتف'),
                ),
                migrations.AddField(
                    model_name='opco',
                    name='industry',
                    field=models.CharField(blank=True, max_length=100, null=True, verbose_name='النشاط'),
                ),
                migrations.AddField(
                    model_name='opco',
                    name='database_name',
                    field=models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='اسم قاعدة البيانات'),
                ),
                migrations.AddField(
                    model_name='opco',
                    name='system_mode',
                    field=models.CharField(choices=[('standalone', 'Stand Alone'), ('modular', 'Full Package')], default='modular', max_length=20, verbose_name='نوع النظام'),
                ),
                migrations.AddField(
                    model_name='opco',
                    name='purchased_modules',
                    field=models.JSONField(blank=True, default=list, verbose_name='الموديولات المشتراة'),
                ),
                migrations.AddField(
                    model_name='companyuser',
                    name='role',
                    field=models.CharField(choices=[('admin', 'Admin (كل الصلاحيات)'), ('cashier', 'Cashier (الكاشير)'), ('kitchen', 'Kitchen (المطبخ)'), ('warehouse', 'Warehouse (المخازن والتكاليف)'), ('manager', 'Manager (الإدارة والتقارير)')], default='admin', max_length=20),
                ),
            ],
            database_operations=[
                migrations.RunPython(make_core_db_changes),
            ]
        )
    ]
