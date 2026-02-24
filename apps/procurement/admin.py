from django.contrib import admin
from .models import Vendor, PurchaseOrder, PurchaseOrderLine

class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'opco')
    search_fields = ('name', 'code')

class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1

class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor', 'status', 'date')
    inlines = [PurchaseOrderLineInline]

admin.site.register(Vendor, VendorAdmin)
admin.site.register(PurchaseOrder, PurchaseOrderAdmin)
# admin.site.register(PurchaseOrderLine) # اختياري لأننا عرضناه داخل الـ Order