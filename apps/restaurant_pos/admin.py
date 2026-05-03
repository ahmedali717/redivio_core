from django.contrib import admin
from .models import Recipe, RecipeItem, ModifierGroup, Modifier, POSSession, POSOrder, POSOrderLine

class RecipeItemInline(admin.TabularInline):
    model = RecipeItem
    extra = 1
    raw_id_fields = ['ingredient']

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'finished_good', 'opco', 'is_active', 'kitchen_station')
    list_filter = ('opco', 'is_active', 'kitchen_station')
    search_fields = ('name', 'finished_good__name')
    raw_id_fields = ['finished_good', 'opco']
    inlines = [RecipeItemInline]

class ModifierInline(admin.TabularInline):
    model = Modifier
    extra = 1
    raw_id_fields = ['linked_material']

@admin.register(ModifierGroup)
class ModifierGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'opco', 'is_required', 'min_choices', 'max_choices')
    list_filter = ('opco', 'is_required')
    raw_id_fields = ['opco']
    inlines = [ModifierInline]

class POSOrderLineInline(admin.TabularInline):
    model = POSOrderLine
    extra = 0
    raw_id_fields = ['material']
    readonly_fields = ['subtotal']

@admin.register(POSOrder)
class POSOrderAdmin(admin.ModelAdmin):
    list_display = ('order_ref', 'session', 'opco', 'order_type', 'total_amount', 'status', 'inventory_deducted')
    list_filter = ('status', 'opco', 'order_type', 'inventory_deducted')
    search_fields = ('order_ref', 'session__cashier_name')
    raw_id_fields = ['opco', 'session']
    readonly_fields = ['created_at']
    inlines = [POSOrderLineInline]

@admin.register(POSSession)
class POSSessionAdmin(admin.ModelAdmin):
    list_display = ('cashier_name', 'session_id', 'opco', 'start_time', 'end_time', 'is_closed')
    list_filter = ('is_closed', 'opco')
    search_fields = ('cashier_name', 'session_id')
    autocomplete_fields = ['opco']
    readonly_fields = ['session_id', 'start_time']
