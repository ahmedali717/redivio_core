from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction

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
    """Reads active opco from query param ?opco= first, then falls back to session."""
    
    def _get_opco_id(self):
        return self.request.query_params.get('opco') or self.request.session.get('active_opco_id')

    def get_queryset(self):
        opco_id = self._get_opco_id()
        if opco_id:
            return self.queryset.filter(opco_id=opco_id)
        return self.queryset

    def perform_create(self, serializer):
        opco_id = self._get_opco_id()
        if opco_id:
            serializer.save(opco_id=opco_id)
        else:
            serializer.save()

# =========================================================
#  2. Sales ViewSets
# =========================================================

class CustomerViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('name')
    serializer_class = CustomerSerializer

class SalesOrderViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all().order_by('-created_at')
    serializer_class = SalesOrderSerializer

    def create(self, request, *args, **kwargs):
        """Create SO with lines atomically."""
        lines_data = request.data.pop('lines', []) if isinstance(request.data, dict) else []
        opco_id = self._get_opco_id() or request.data.get('opco')

        with transaction.atomic():
            # Build the payload dict to avoid mutating request.data directly
            data = {**request.data, 'opco': opco_id} if opco_id else dict(request.data)
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            so = serializer.save()

            # Create lines
            total = 0
            for line in lines_data:
                if not line.get('material'):
                    continue
                qty = float(line.get('quantity', 1))
                price = float(line.get('unit_price', 0))
                line_total = qty * price
                total += line_total
                SalesOrderLine.objects.create(
                    so=so,
                    material_id=line['material'],
                    quantity=qty,
                    unit_price=price,
                    total=line_total
                )
            
            # Update totals
            tax = total * 0.15
            so.total_amount = total
            so.tax_amount = tax
            so.grand_total = total + tax
            so.save()

        return Response(SalesOrderSerializer(so).data, status=status.HTTP_201_CREATED)

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