import csv # 👈 استيراد مكتبة قراءة الإكسيل
from rest_framework import viewsets, exceptions
from rest_framework.decorators import action # 👈 استيراد الـ action
from rest_framework.response import Response # 👈 استيراد الـ Response الخاص بـ DRF

from .models import Category, Material, SaleGroup
from .serializers import CategorySerializer, MaterialSerializer, SaleGroupSerializer

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

class SaleGroupViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة المجموعات البيعية (POS Groups) """
    queryset = SaleGroup.objects.all().order_by('name')
    serializer_class = SaleGroupSerializer
    
    def get_queryset(self):
        opco_id = self.request.query_params.get('opco') or self.request.session.get('active_opco_id')
        if opco_id:
            return SaleGroup.objects.filter(opco_id=opco_id).order_by('name')
        return SaleGroup.objects.all().order_by('name')


class MaterialViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة المواد والأصناف (Items) مع التصفية حسب الشركة """
    serializer_class = MaterialSerializer

    def get_queryset(self):
        opco_id = self.request.query_params.get('opco') or self.request.session.get('active_opco_id')
        if opco_id:
            return Material.objects.filter(opco_id=opco_id).order_by('-id')
        return Material.objects.all().order_by('-id')

    def perform_create(self, serializer):
        opco_id = self.request.data.get('opco') or self.request.session.get('active_opco_id')
        if not opco_id:
            raise exceptions.ValidationError({"detail": "Active company not found. / لم يتم العثور على شركة نشطة."})
            
        from apps.core.models import OpCo
        from django.db.models import Q
        try:
            opco = OpCo.all_objects.get(id=opco_id)
        except OpCo.DoesNotExist:
            raise exceptions.ValidationError({"detail": "Active company not found. / لم يتم العثور على شركة نشطة."})
            
        holding_opco = opco
        while holding_opco.parent:
            holding_opco = holding_opco.parent
            
        plan = holding_opco.plan
        if plan == 'business':
            sku_limit = 5000
        elif plan in ['professional', 'pro']:
            sku_limit = 99999
        elif plan == 'enterprise':
            sku_limit = 999999
        else:  # starter / free
            sku_limit = 50
            
        target_opcos = OpCo.all_objects.filter(Q(id=opco.id) | Q(parent_id=opco.id))
        current_count = Material.objects.filter(opco__in=target_opcos).count()
        
        if current_count >= sku_limit:
            raise exceptions.ValidationError({
                "detail": f"لقد وصلت للحد الأقصى المسموح به للأصناف في خطتك الحالية ({sku_limit} أصناف). يرجى ترقية الخطة. / You have reached the maximum allowed items for your current plan ({sku_limit} items). Please upgrade your plan."
            })
            
        serializer.save(opco_id=opco_id)

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