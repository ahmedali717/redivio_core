# Generated manually for Odoo & ERPNext Vendor & Procurement Integration

from django.db import migrations, models
import django.db.models.deletion

def add_columns_safe(apps, schema_editor):
    table_name = 'item_master_material'
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if 'default_vendor_id' not in columns:
                cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "default_vendor_id" bigint NULL REFERENCES "procurement_vendor" ("id") DEFERRABLE INITIALLY DEFERRED')
            if 'vendor_part_number' not in columns:
                cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "vendor_part_number" varchar(100) NULL')
            if 'lead_time_days' not in columns:
                cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "lead_time_days" integer NOT NULL DEFAULT 1')
        else: # postgres / other
            for col, col_type in [
                ('default_vendor_id', 'bigint NULL REFERENCES "procurement_vendor" ("id") DEFERRABLE INITIALLY DEFERRED'),
                ('vendor_part_number', 'varchar(100) NULL'),
                ('lead_time_days', 'integer NOT NULL DEFAULT 1')
            ]:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name=%s AND column_name=%s", [table_name, col])
                if not cursor.fetchone():
                    cursor.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" {col_type}')

class Migration(migrations.Migration):

    dependencies = [
        ('item_master', '0012_material_allowed_terminals'),
        ('procurement', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_columns_safe, reverse_code=migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='material',
                    name='default_vendor',
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='supplied_materials',
                        to='procurement.vendor',
                        verbose_name='المورد الافتراضي (Default Supplier)'
                    ),
                ),
                migrations.AddField(
                    model_name='material',
                    name='vendor_part_number',
                    field=models.CharField(blank=True, max_length=100, null=True, verbose_name='كود الصنف عند المورد'),
                ),
                migrations.AddField(
                    model_name='material',
                    name='lead_time_days',
                    field=models.PositiveIntegerField(default=1, verbose_name='فترة التوريد بالأيام'),
                ),
            ]
        )
    ]
