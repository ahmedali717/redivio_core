from django.shortcuts import render
from django.views import View
from django.db import transaction  # <--- ضروري جداً لمنع وقوع السيرفر
from django.http import JsonResponse # <--- ضروري جداً
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

# استيراد الـ Mixin والـ Models
from apps.core.mixins import OpcoAwareMixin 
from apps.procurement.models import PurchaseOrder  # <--- تأكد من صحة هذا المسار
from .models import Plant, StorageLocation, StorageBin, StockQuant, StockMove
from .serializers import (
    PlantSerializer, StorageLocationSerializer, 
    StorageBinSerializer, StockQuantSerializer, StockMoveSerializer
)

# ... (اترك الدوال القديمة wms_stats والـ ViewSets كما هي) ...

# 1. الـ API الذي يستلم البيانات من زرار "تأكيد الاستلام"
class StockReceiptAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        po_id = data.get('po_id')
        items = data.get('items', [])
        active_opco_id = request.session.get('active_opco_id')

        if not po_id:
            return Response({"error": "PO ID is required"}, status=400)

        try:
            with transaction.atomic(): # <--- لن تسبب خطأ الآن بسبب الـ Import
                po = PurchaseOrder.objects.get(id=po_id)
                
                for item in items:
                    # تحديث الرصيد في الرف المختار
                    quant, created = StockQuant.objects.get_or_create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        storage_bin_id=item['bin_id'],
                        defaults={'quantity': 0}
                    )
                    quant.quantity += float(item['quantity'])
                    quant.save()

                    # تسجيل حركة مخزنية
                    StockMove.objects.create(
                        opco_id=active_opco_id,
                        material_id=item['material_id'],
                        quantity=item['quantity'],
                        move_type='RECEIPT',
                        reference=f"PO Receipt: {po.po_number}",
                        storage_bin_id=item['bin_id']
                    )

                # تحديث حالة أمر التوريد
                po.status = 'RECEIVED'
                po.save()

                return Response({"success": True}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# 2. الـ API الذي يعرض تفاصيل الـ PO في الجدول
def get_purchase_order_details(request, po_id):
    try:
        # تأكد أن العلاقة في موديل PurchaseOrder تسمى 'items'
        po = PurchaseOrder.objects.get(id=po_id)
        items_list = []
        
        # افتراض أن PurchaseOrder لديه علاقة items (Related Name)
        for item in po.items.all():
            items_list.append({
                'material_id': item.material.id,
                'material_name': item.material.name,
                'sku': item.material.sku or item.material.code,
                'ordered_qty': item.quantity,
                'received_qty': item.quantity,
            })
        
        return JsonResponse({'items': items_list})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)