from django.contrib import admin
from .models import Customer, SalesOrder, SalesOrderLine

class CustomerAdmin(admin.ModelAdmin):
    # قمنا بإزالة 'email' مؤقتاً لتجاوز الخطأ حتى نتأكد من تحديث الموديل
    list_display = ('name', 'code', 'opco') 
    search_fields = ('name', 'code')

class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 1

class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('so_number', 'customer', 'status', 'date')
    inlines = [SalesOrderLineInline]

admin.site.register(Customer, CustomerAdmin)
admin.site.register(SalesOrder, SalesOrderAdmin)