# Generated manually to prevent database errors safely

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

def make_wms_db_changes(apps, schema_editor):
    connection = schema_editor.connection
    table_names = connection.introspection.table_names()
    
    if 'wms_stockmove' in table_names:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(wms_stockmove)")
        columns = [row[1] for row in cursor.fetchall()]
        
        StockMove = apps.get_model('wms', 'StockMove')
        
        # Remove date if exists
        if 'date' in columns:
            schema_editor.remove_field(StockMove, StockMove._meta.get_field('date'))
            
        # Add created_at if doesn't exist
        if 'created_at' not in columns:
            schema_editor.add_field(StockMove, StockMove._meta.get_field('created_at'))
            
        # Add updated_at if doesn't exist
        if 'updated_at' not in columns:
            schema_editor.add_field(StockMove, StockMove._meta.get_field('updated_at'))
            
        # Add vendor if doesn't exist
        if 'vendor_id' not in columns:
            schema_editor.add_field(StockMove, StockMove._meta.get_field('vendor'))
            
        # Add customer if doesn't exist
        if 'customer_id' not in columns:
            schema_editor.add_field(StockMove, StockMove._meta.get_field('customer'))

class Migration(migrations.Migration):

    dependencies = [
        ('wms', '0004_stockmove_payment_method_stockmove_sales_price_and_more'),
        ('core', '0009_opco_contact_name_opco_contact_phone_and_more'),
        ('procurement', '0001_initial'),
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='stockmove',
                    name='date',
                ),
                migrations.AddField(
                    model_name='stockmove',
                    name='created_at',
                    field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name='stockmove',
                    name='updated_at',
                    field=models.DateTimeField(auto_now=True),
                ),
                migrations.AddField(
                    model_name='stockmove',
                    name='vendor',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='procurement.vendor'),
                ),
                migrations.AddField(
                    model_name='stockmove',
                    name='customer',
                    field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='sales.customer'),
                ),
            ],
            database_operations=[
                migrations.RunPython(make_wms_db_changes),
            ]
        )
    ]
