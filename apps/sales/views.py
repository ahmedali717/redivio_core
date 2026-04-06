from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

# Models & Serializers
from .models import Customer, SalesOrder, SalesOrderLine, SalesInvoice, CustomerPayment
from .serializers import (
    CustomerSerializer, SalesOrderSerializer, SalesOrderLineSerializer,
    SalesInvoiceSerializer, CustomerPaymentSerializer
)

from apps.wms.models import StorageBin

# =========================================================
#  1. Helper Mixin
# =========================================================
class OpcoAwareMixin:
    def get_queryset(self):
        active_opco_id = self.request.session.get('active_opco_id')
        if active_opco_id:
            return self.queryset.filter(opco_id=active_opco_id)
        return self.queryset

    def perform_create(self, serializer):
        active_opco_id = self.request.session.get('active_opco_id')
        if active_opco_id:
            serializer.save(opco_id=active_opco_id)
        else:
            serializer.save()

# =========================================================
#  2. Sales ViewSets
# =========================================================

class CustomerViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

class SalesOrderViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all().order_by('-created_at')
    serializer_class = SalesOrderSerializer

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        so = self.get_object()
        bin_id = request.data.get('bin_id')
        if not bin_id:
            return Response({'error': 'Source Bin ID is required for delivery.'}, status=400)
        
        try:
            source_bin = StorageBin.objects.get(id=bin_id)
            so.deliver_items(source_bin)
            return Response({'status': 'Delivered', 'so_number': so.so_number})
        except StorageBin.DoesNotExist:
            return Response({'error': 'Invalid Source Bin ID'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class SalesOrderLineViewSet(viewsets.ModelViewSet):
    queryset = SalesOrderLine.objects.all()
    serializer_class = SalesOrderLineSerializer

class SalesInvoiceViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = SalesInvoice.objects.all().order_by('-date')
    serializer_class = SalesInvoiceSerializer

class CustomerPaymentViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = CustomerPayment.objects.all().order_by('-date')
    serializer_class = CustomerPaymentSerializer