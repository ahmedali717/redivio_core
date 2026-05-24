from django.db import migrations, models
import django.db.models.deletion

def make_item_master_db_changes(apps, schema_editor):
    connection = schema_editor.connection
    table_names = connection.introspection.table_names()
    
    # 1. Create SaleGroup table if not exists
    from apps.item_master.models import SaleGroup
    if 'item_master_salegroup' not in table_names:
        schema_editor.create_model(SaleGroup)
        
    # 2. Add fields to Material safely
    if 'item_master_material' in table_names:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(item_master_material)")
        columns = [row[1] for row in cursor.fetchall()]
        
        Material = apps.get_model('item_master', 'Material')
        if 'is_pos_item' not in columns:
            schema_editor.add_field(Material, Material._meta.get_field('is_pos_item'))
        if 'is_combo' not in columns:
            schema_editor.add_field(Material, Material._meta.get_field('is_combo'))
        if 'expiry_date' not in columns:
            schema_editor.add_field(Material, Material._meta.get_field('expiry_date'))
        if 'sale_group_id' not in columns:
            schema_editor.add_field(Material, Material._meta.get_field('sale_group'))
            
    # 3. Create ComboItem table if not exists
    from apps.item_master.models import ComboItem
    if 'item_master_comboitem' not in table_names:
        schema_editor.create_model(ComboItem)

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
        ('item_master', '0010_material_standard_price'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='SaleGroup',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('updated_at', models.DateTimeField(auto_now=True)),
                        ('name', models.CharField(max_length=100)),
                        ('image', models.ImageField(blank=True, null=True, upload_to='sale_groups/')),
                        ('color', models.CharField(default='#6366f1', max_length=20)),
                        ('opco', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(class)s_records', to='core.opco')),
                    ],
                    options={
                        'abstract': False,
                    },
                ),
                migrations.AddField(
                    model_name='material',
                    name='is_pos_item',
                    field=models.BooleanField(default=False, help_text='هل هذا الصنف متاح في قائمة البيع للمطعم؟'),
                ),
                migrations.AddField(
                    model_name='material',
                    name='is_combo',
                    field=models.BooleanField(default=False, help_text='هل هذا الصنف عبارة عن عرض (Combo)؟'),
                ),
                migrations.AddField(
                    model_name='material',
                    name='expiry_date',
                    field=models.DateField(blank=True, help_text='تاريخ انتهاء الصلاحية لهذا الصنف (اختياري)', null=True),
                ),
                migrations.AddField(
                    model_name='material',
                    name='sale_group',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='materials', to='item_master.salegroup'),
                ),
                migrations.CreateModel(
                    name='ComboItem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10)),
                        ('extra_price', models.DecimalField(decimal_places=2, default=0, help_text='سعر إضافي عند اختيار هذا الصنف في العرض', max_digits=10)),
                        ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='included_in_combos', to='item_master.material')),
                        ('parent_material', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='combo_items', to='item_master.material')),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunPython(make_item_master_db_changes),
            ]
        )
    ]
