# Generated manually

from django.db import migrations, models

def create_m2m_table_safe(apps, schema_editor):
    db_table = 'item_master_material_allowed_terminals'
    
    # Check if table exists
    with schema_editor.connection.cursor() as cursor:
        if schema_editor.connection.vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=%s", [db_table])
            exists = bool(cursor.fetchone())
        else: # postgres
            cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = %s)", [db_table])
            exists = cursor.fetchone()[0]
            
    if not exists:
        # Manually create M2M table using raw SQL depending on vendor
        with schema_editor.connection.cursor() as cursor:
            if schema_editor.connection.vendor == 'sqlite':
                cursor.execute("""
                    CREATE TABLE "item_master_material_allowed_terminals" (
                        "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "material_id" bigint NOT NULL REFERENCES "item_master_material" ("id") DEFERRABLE INITIALLY DEFERRED,
                        "posterminal_id" bigint NOT NULL REFERENCES "restaurant_pos_posterminal" ("id") DEFERRABLE INITIALLY DEFERRED
                    )
                """)
                cursor.execute("""
                    CREATE UNIQUE INDEX "item_master_material_al_material_id_posterminal__796f6004_uniq" 
                    ON "item_master_material_allowed_terminals" ("material_id", "posterminal_id")
                """)
            else: # postgres / other
                cursor.execute("""
                    CREATE TABLE "item_master_material_allowed_terminals" (
                        "id" bigserial NOT NULL PRIMARY KEY,
                        "material_id" bigint NOT NULL REFERENCES "item_master_material" ("id") DEFERRABLE INITIALLY DEFERRED,
                        "posterminal_id" bigint NOT NULL REFERENCES "restaurant_pos_posterminal" ("id") DEFERRABLE INITIALLY DEFERRED
                    )
                """)
                cursor.execute("""
                    CREATE UNIQUE INDEX "item_master_material_al_material_id_posterminal__796f6004_uniq" 
                    ON "item_master_material_allowed_terminals" ("material_id", "posterminal_id")
                """)

class Migration(migrations.Migration):

    dependencies = [
        ('item_master', '0011_salegroup_material_is_pos_item_and_more'),
        ('restaurant_pos', '0004_posterminal_allowed_users'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(create_m2m_table_safe, reverse_code=migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='material',
                    name='allowed_terminals',
                    field=models.ManyToManyField(
                        blank=True,
                        help_text='نقاط البيع المسموح بظهور هذا الصنف فيها',
                        related_name='materials',
                        to='restaurant_pos.POSTerminal'
                    ),
                ),
            ]
        )
    ]
