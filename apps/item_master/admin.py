from django.contrib import admin
# لاحظ: نستدعي الموديلات من models.py ولا نكتبها هنا
from .models import Material, Category, FieldDefinition

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'opco')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

@admin.register(FieldDefinition)
class FieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_model', 'field_type')