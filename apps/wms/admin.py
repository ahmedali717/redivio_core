from django.contrib import admin
from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'opco', 'type')
    list_filter = ('opco', 'type')
    search_fields = ('code', 'name')

@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'plant')
    list_filter = ('plant__opco', 'plant')
    search_fields = ('code', 'name')

@admin.register(StorageBin)
class StorageBinAdmin(admin.ModelAdmin):
    # استخدام التسميات الصحيحة كما في الموديل
    list_display = ('code', 'storage_location', 'is_active')
    # الفلترة عبر المستويات: المصنع -> الموقع -> الرف
    list_filter = ('storage_location__plant', 'storage_location', 'is_active')
    search_fields = ('code',)

@admin.register(StockQuant)
class StockQuantAdmin(admin.ModelAdmin):
    # إظهار الشركة والكمية والموقع بالتفصيل
    list_display = ('material', 'storage_bin', 'quantity', 'opco')
    # تحسين الفلترة لتشمل المادة والموقع
    list_filter = ('opco', 'storage_bin__storage_location__plant', 'material')
    # تفعيل البحث عن الأصناف برقم الـ SKU أو الاسم
    search_fields = ('material__name', 'material__sku', 'storage_bin__code')

@admin.register(StockMove)
class StockMoveAdmin(admin.ModelAdmin):
    list_display = ('reference', 'move_type', 'material', 'quantity', 'date', 'opco')
    list_filter = ('opco', 'move_type', 'date')
    search_fields = ('reference', 'material__name')
    # جعل الحقول للقراءة فقط لضمان عدم التلاعب في سجل الحركات يدوياً
    readonly_fields = ('date',)