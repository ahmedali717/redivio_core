from rest_framework import viewsets, exceptions
from .models import Category, Material, FieldDefinition
from .serializers import CategorySerializer, MaterialSerializer, FieldDefinitionSerializer

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
        # (يفترض وجود Middleware يضيف هذا، أو يمكن جلبه من الـ session)
        active_opco_id = self.request.session.get('active_opco_id')
        
        if active_opco_id:
            serializer.save(opco_id=active_opco_id)
            return

        # 3. إذا فشل كل شيء (يسمح بالحفظ بدون opco إذا كان الحقل null=True في الموديل، وإلا سيرمي خطأ من قاعدة البيانات)
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
            return Material.objects.filter(opco_id=active_opco_id).order_by('-created_at')
        
        # إذا لم تكن هناك شركة مختارة (أو مستخدم superuser يريد رؤية الكل)
        # يمكنك إرجاع فارغ أو كل الأصناف حسب رغبتك
        return Material.objects.all().order_by('-created_at')

class FieldDefinitionViewSet(viewsets.ModelViewSet):
    """ 
    إدارة الحقول المخصصة (Customize Forms)
    هذا هو الجزء الذي كان ناقصاً
    """
    queryset = FieldDefinition.objects.all()
    serializer_class = FieldDefinitionSerializer