from rest_framework import viewsets, exceptions
# 👈 1. مسحنا FieldDefinition من السطر التالي
from .models import Category, Material
# 👈 2. مسحنا FieldDefinitionSerializer من السطر التالي
from .serializers import CategorySerializer, MaterialSerializer

# =========================================================
#  1. Mixins (لإعادة الاستخدام)
# =========================================================
class OpcoAwareMixin:
    """
    يقوم تلقائياً بربط السجل بالشركة (OPCO) عند الإنشاء
    """
    def perform_create(self, serializer):
        # 1. الأولوية: هل الـ opco مرسل صراحة في البيانات؟
        opco_id = self.request.data.get('opco')
        
        if opco_id:
            serializer.save(opco_id=opco_id)
            return

        # 2. الخيار الثاني: هل هناك active_opco في الجلسة/الطلب؟
        active_opco_id = self.request.session.get('active_opco_id')
        
        if active_opco_id:
            serializer.save(opco_id=active_opco_id)
            return

        # 3. إذا فشل كل شيء
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
        # جلب الـ opco النشط من الجلسة
        active_opco_id = self.request.session.get('active_opco_id')
        
        # إذا كان هناك شركة مختارة، أظهر أصنافها فقط
        if active_opco_id:
            return Material.objects.filter(opco_id=active_opco_id).order_by('-id')
        
        return Material.objects.filter(opco_id=active_opco_id).order_by('-id')

# =========================================================
# ⛔ 3. قمنا بتعطيل FieldDefinitionViewSet مؤقتاً
# =========================================================
# class FieldDefinitionViewSet(viewsets.ModelViewSet):
#     """ 
#     إدارة الحقول المخصصة (Customize Forms)
#     """
#     queryset = FieldDefinition.objects.all()
#     serializer_class = FieldDefinitionSerializer