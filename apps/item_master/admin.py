from django.contrib import admin
from .models import Material, Category

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'opco')

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')

# قمنا بإيقاف هذا الجزء مؤقتاً حتى لا يسبب خطأ
# @admin.register(FieldDefinition)
# class FieldDefinitionAdmin(admin.ModelAdmin):
#     list_display = ('name', 'target_model', 'field_type')