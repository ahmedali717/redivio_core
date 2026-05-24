# Generated manually to prevent database errors

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

def make_sales_db_changes(apps, schema_editor):
    connection = schema_editor.connection
    table_names = connection.introspection.table_names()
    
    # 1. Update sales_salesorder safely
    if 'sales_salesorder' in table_names:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(sales_salesorder)")
        columns = [row[1] for row in cursor.fetchall()]
        
        SalesOrder = apps.get_model('sales', 'SalesOrder')
        
        # Remove fields if they exist
        if 'address' in columns:
            schema_editor.remove_field(SalesOrder, SalesOrder._meta.get_field('address'))
        if 'email' in columns:
            schema_editor.remove_field(SalesOrder, SalesOrder._meta.get_field('email'))
        if 'phone' in columns:
            schema_editor.remove_field(SalesOrder, SalesOrder._meta.get_field('phone'))
            
        # Add fields if they don't exist
        if 'grand_total' not in columns:
            schema_editor.add_field(SalesOrder, SalesOrder._meta.get_field('grand_total'))
        if 'notes' not in columns:
            schema_editor.add_field(SalesOrder, SalesOrder._meta.get_field('notes'))
        if 'tax_amount' not in columns:
            schema_editor.add_field(SalesOrder, SalesOrder._meta.get_field('tax_amount'))
        if 'total_amount' not in columns:
            schema_editor.add_field(SalesOrder, SalesOrder._meta.get_field('total_amount'))
            
    # 2. Update sales_customer safely
    if 'sales_customer' in table_names:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(sales_customer)")
        columns = [row[1] for row in cursor.fetchall()]
        
        Customer = apps.get_model('sales', 'Customer')
        if 'address' not in columns:
            schema_editor.add_field(Customer, Customer._meta.get_field('address'))
        if 'balance' not in columns:
            schema_editor.add_field(Customer, Customer._meta.get_field('balance'))
        if 'email' not in columns:
            schema_editor.add_field(Customer, Customer._meta.get_field('email'))
        if 'phone' not in columns:
            schema_editor.add_field(Customer, Customer._meta.get_field('phone'))
            
    # 3. Update sales_salesorderline safely
    if 'sales_salesorderline' in table_names:
        cursor = connection.cursor()
        cursor.execute("PRAGMA table_info(sales_salesorderline)")
        columns = [row[1] for row in cursor.fetchall()]
        
        SalesOrderLine = apps.get_model('sales', 'SalesOrderLine')
        if 'billed_quantity' not in columns:
            schema_editor.add_field(SalesOrderLine, SalesOrderLine._meta.get_field('billed_quantity'))
        if 'shipped_quantity' not in columns:
            schema_editor.add_field(SalesOrderLine, SalesOrderLine._meta.get_field('shipped_quantity'))
        if 'total' not in columns:
            schema_editor.add_field(SalesOrderLine, SalesOrderLine._meta.get_field('total'))

    # 4. Create new models/tables if they don't exist
    from apps.sales.models import SalesInvoice, CustomerPayment, StockDelivery, StockDeliveryLine
    
    if 'sales_salesinvoice' not in table_names:
        schema_editor.create_model(SalesInvoice)
        
    if 'sales_customerpayment' not in table_names:
        schema_editor.create_model(CustomerPayment)
        
    if 'sales_stockdelivery' not in table_names:
        schema_editor.create_model(StockDelivery)
        
    if 'sales_stockdeliveryline' not in table_names:
        schema_editor.create_model(StockDeliveryLine)

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_opco_contact_name_opco_contact_phone_and_more"),
        ("item_master", "0011_salegroup_material_is_pos_item_and_more"),
        ("sales", "0001_initial"),
        ("wms", "0005_remove_stockmove_date_stockmove_created_at_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name="salesorder",
                    name="address",
                ),
                migrations.RemoveField(
                    model_name="salesorder",
                    name="email",
                ),
                migrations.RemoveField(
                    model_name="salesorder",
                    name="phone",
                ),
                migrations.AddField(
                    model_name="customer",
                    name="address",
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="customer",
                    name="balance",
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=15),
                ),
                migrations.AddField(
                    model_name="customer",
                    name="email",
                    field=models.EmailField(blank=True, max_length=254, null=True),
                ),
                migrations.AddField(
                    model_name="customer",
                    name="phone",
                    field=models.CharField(blank=True, max_length=20, null=True),
                ),
                migrations.AddField(
                    model_name="salesorder",
                    name="grand_total",
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                migrations.AddField(
                    model_name="salesorder",
                    name="notes",
                    field=models.TextField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="salesorder",
                    name="tax_amount",
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                migrations.AddField(
                    model_name="salesorder",
                    name="total_amount",
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                migrations.AddField(
                    model_name="salesorderline",
                    name="billed_quantity",
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                migrations.AddField(
                    model_name="salesorderline",
                    name="shipped_quantity",
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                migrations.AddField(
                    model_name="salesorderline",
                    name="total",
                    field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
                ),
                migrations.AlterField(
                    model_name="salesorder",
                    name="customer",
                    field=models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="orders",
                        to="sales.customer",
                    ),
                ),
                migrations.AlterField(
                    model_name="salesorder",
                    name="status",
                    field=models.CharField(
                        choices=[
                            ("DRAFT", "Draft"),
                            ("CONFIRMED", "Confirmed"),
                            ("SHIPPED", "Shipped"),
                            ("DELIVERED", "Delivered"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="DRAFT",
                        max_length=20,
                    ),
                ),
                migrations.CreateModel(
                    name="SalesInvoice",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("invoice_number", models.CharField(max_length=50, unique=True)),
                        ("date", models.DateField(auto_now_add=True)),
                        ("due_date", models.DateField()),
                        ("total_amount", models.DecimalField(decimal_places=2, max_digits=12)),
                        (
                            "paid_amount",
                            models.DecimalField(decimal_places=2, default=0, max_digits=12),
                        ),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("UNPAID", "Unpaid"),
                                    ("PARTIAL", "Partial"),
                                    ("PAID", "Paid"),
                                ],
                                default="UNPAID",
                                max_length=20,
                            ),
                        ),
                        (
                            "customer",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE, to="sales.customer"
                            ),
                        ),
                        (
                            "opco",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE, to="core.opco"
                            ),
                        ),
                        (
                            "sales_order",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to="sales.salesorder",
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    name="CustomerPayment",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("payment_number", models.CharField(max_length=50, unique=True)),
                        ("date", models.DateField(auto_now_add=True)),
                        ("amount", models.DecimalField(decimal_places=2, max_digits=12)),
                        (
                            "method",
                            models.CharField(
                                choices=[
                                    ("CASH", "Cash"),
                                    ("BANK", "Bank Transfer"),
                                    ("CHECK", "Check"),
                                ],
                                default="CASH",
                                max_length=20,
                            ),
                        ),
                        ("reference", models.CharField(blank=True, max_length=100, null=True)),
                        (
                            "customer",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE, to="sales.customer"
                            ),
                        ),
                        (
                            "opco",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE, to="core.opco"
                            ),
                        ),
                        (
                            "invoice",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to="sales.salesinvoice",
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    name="StockDelivery",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "delivery_number",
                            models.CharField(blank=True, max_length=50, unique=True),
                        ),
                        ("date", models.DateTimeField(auto_now_add=True)),
                        (
                            "created_by",
                            models.ForeignKey(
                                null=True,
                                on_delete=django.db.models.deletion.SET_NULL,
                                to=settings.AUTH_USER_MODEL,
                            ),
                        ),
                        (
                            "opco",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE, to="core.opco"
                            ),
                        ),
                        (
                            "so",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="deliveries",
                                to="sales.salesorder",
                            ),
                        ),
                    ],
                ),
                migrations.CreateModel(
                    name="StockDeliveryLine",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("quantity", models.DecimalField(decimal_places=2, max_digits=12)),
                        (
                            "delivery",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                related_name="items",
                                to="sales.stockdelivery",
                            ),
                        ),
                        (
                            "material",
                            models.ForeignKey(
                                on_delete=django.db.models.deletion.CASCADE,
                                to="item_master.material",
                            ),
                        ),
                        (
                            "storage_bin",
                            models.ForeignKey(
                                blank=True,
                                null=True,
                                on_delete=django.db.models.deletion.CASCADE,
                                to="wms.storagebin",
                            ),
                        ),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunPython(make_sales_db_changes),
            ]
        )
    ]
