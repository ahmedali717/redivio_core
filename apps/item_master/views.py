import csv # 👈 استيراد مكتبة قراءة الإكسيل
from rest_framework import viewsets, exceptions
from rest_framework.decorators import action # 👈 استيراد الـ action
from rest_framework.response import Response # 👈 استيراد الـ Response الخاص بـ DRF

from .models import Category, Material
from .serializers import CategorySerializer, MaterialSerializer

# =========================================================
#  1. Mixins (لإعادة الاستخدام)
# =========================================================
class OpcoAwareMixin:
    """
    يقوم تلقائياً بربط السجل بالشركة (OPCO) عند الإنشاء
    """
    def perform_create(self, serializer):
        opco_id = self.request.data.get('opco')
        if opco_id:
            serializer.save(opco_id=opco_id)
            return

        active_opco_id = self.request.session.get('active_opco_id')
        if active_opco_id:
            serializer.save(opco_id=active_opco_id)
            return

        serializer.save()

# =========================================================
#  2. Item Master ViewSets
# =========================================================

class CategoryViewSet(viewsets.ModelViewSet):
    """ إدارة مجموعات الأصناف (Groups) """
    queryset = Category.objects.all().order_by('code')
    serializer_class = CategorySerializer


class MaterialViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة المواد والأصناف (Items) مع التصفية حسب الشركة """
    serializer_class = MaterialSerializer

    def get_queryset(self):
        active_opco_id = self.request.session.get('active_opco_id')
        if active_opco_id:
            return Material.objects.filter(opco_id=active_opco_id).order_by('-id')
        return Material.objects.filter(opco_id=active_opco_id).order_by('-id')

    # =========================================================
    # 🚀 3. دالة الاستيراد الجديدة (تعمل على مسار /api/materials/import/)
    # =========================================================
    @action(detail=False, methods=['post'], url_path='import')
    def import_data(self, request):
        csv_file = request.FILES.get('file')
        opco_id = request.data.get('opco_id') # في DRF بنستخدم request.data

        if not csv_file or not csv_file.name.endswith('.csv'):
            return Response({'error': 'الرجاء رفع ملف بصيغة CSV صالح'}, status=400)

        try:
            # قراءة الملف وفك التشفير
            file_data = csv_file.read().decode('utf-8-sig').splitlines()
            reader = csv.reader(file_data)
            
            # تخطي أول سطر (أسماء الأعمدة)
            headers = next(reader, None)

            count = 0
            for row in reader:
                # لو السطر فاضي أو مفيهوش SKU أو اسم نتخطاه
                if len(row) < 2 or not row[0].strip() or not row[1].strip():
                    continue 

                sku_val = row[0].strip()
                name_val = row[1].strip()
                category_val = row[2].strip() if len(row) > 2 else ''
                uom_val = row[3].strip() if len(row) > 3 else 'PCS'
                barcode_val = row[4].strip() if len(row) > 4 else ''
                tracking_val = row[5].strip() if len(row) > 5 else 'none'

                # تجهيز البيانات
                defaults = {
                    'name': name_val,
                    # 'category': category_val, # لاحظ: لو category في الموديل Foreign Key هتحتاج تعمل Category.objects.get_or_create هنا الأول
                    'base_uom': uom_val,
                    'barcode': barcode_val,
                    'tracking': tracking_val,
                }
                
                # ربط الصنف بالشركة إذا كانت مبعوثة
                if opco_id:
                    defaults['opco_id'] = opco_id

                # تحديث الصنف لو موجود (تطابق الـ SKU) أو إنشاء واحد جديد
                material, created = Material.objects.update_or_create(
                    sku=sku_val, 
                    defaults=defaults
                )
                
                count += 1

            return Response({'success': True, 'count': count})
            
        except Exception as e:
            return Response({'error': f'حدث خطأ أثناء معالجة الملف: {str(e)}'}, status=500)