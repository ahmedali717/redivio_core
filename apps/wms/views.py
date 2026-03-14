from django.shortcuts import render
from django.views import View
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# استيراد الـ Mixin والـ Models والـ Serializers
from apps.core.mixins import OpcoAwareMixin 
from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove
from .serializers import (
    PlantSerializer, 
    StorageLocationSerializer, 
    StorageBinSerializer, 
    StockQuantSerializer, 
    StockMoveSerializer
)

# =========================================================
#  1. API Functions (الإحصائيات المخصصة للموديول)
# =========================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def wms_stats(request):
    """
    إحصائيات سريعة لموديول WMS بناءً على الشركة النشطة
    """
    active_opco_id = request.session.get('active_opco_id')
    
    # تحسين: إذا لم تكن هناك شركة نشطة، نعيد أصفار بدلاً من فلترة خاطئة
    if not active_opco_id:
        return Response({"plants": 0, "items": 0})
    
    plants_count = Plant.objects.filter(opco_id=active_opco_id).count()
    # تحسين: حساب إجمالي كميات المخزون المتوفرة
    items_count = StockQuant.objects.filter(opco_id=active_opco_id).count()
    
    return Response({
        "plants": plants_count,
        "items": items_count
    })

# =========================================================
#  2. WMS ViewSets (المنطق البرمجي للمخازن)
# =========================================================
# ملاحظة: الـ OpcoAwareMixin سيقوم تلقائياً بفلترة النتائج بناءً على الشركة

class PlantViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = Plant.objects.all()
    serializer_class = PlantSerializer

class StorageLocationViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StorageLocation.objects.all()
    serializer_class = StorageLocationSerializer

class StorageBinViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StorageBin.objects.all()
    serializer_class = StorageBinSerializer

class StockQuantViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    # تحسين: استخدام select_related لتقليل ضغط قواعد البيانات عند جلب الأسماء
    queryset = StockQuant.objects.select_related('material', 'storage_bin', 'plant').all()
    serializer_class = StockQuantSerializer

class StockMoveViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = StockMove.objects.all().order_by('-date')
    serializer_class = StockMoveSerializer

# =========================================================
#  3. Web Views (عرض الواجهات من داخل الموديول)
# =========================================================

class WMSHomeView(View):
    def get(self, request):
        # التأكد من أن المسار يشير إلى المجلد داخل التطبيق نفسه لتعزيز الاستقلالية
        return render(request, 'wms/dashboard.html')