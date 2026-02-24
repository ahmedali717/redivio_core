from django.contrib import admin
from .models import OpCo

@admin.register(OpCo)
class OpCoAdmin(admin.ModelAdmin):
    # نعرض فقط الحقول الموجودة فعلياً في الموديل الجديد
    list_display = ('code', 'name', 'currency', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('currency',)