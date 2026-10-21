from django.db import transaction
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404

from redivio_project.utils.pdf import render_to_pdf

from .models import (
    Vendor, PurchaseOrder, PurchaseOrderLine, StockReceipt,
    PurchaseRequisition, RequestForQuotation, SupplierQuotation,
    QuotationComparison, PurchaseReturn
)
from .serializers import (
    VendorSerializer, PurchaseOrderSerializer, PurchaseOrderLineSerializer, StockReceiptSerializer,
    PurchaseRequisitionSerializer, RequestForQuotationSerializer, SupplierQuotationSerializer,
    QuotationComparisonSerializer, PurchaseReturnSerializer
)

from apps.wms.models import StorageBin


class OpcoAwareMixin:
    """
    ربط وتصفية السجلات للشركة النشطة فقط
    """
    def _get_opco_id(self):
        opco_id = (
            self.request.query_params.get('opco') or 
            self.request.query_params.get('opco_id') or
            (self.request.data.get('opco') if hasattr(self.request, 'data') and isinstance(self.request.data, dict) else None) or 
            (self.request.data.get('opco_id') if hasattr(self.request, 'data') and isinstance(self.request.data, dict) else None) or
            (self.request.tenant.id if hasattr(self.request, 'tenant') and self.request.tenant else None) or
            self.request.session.get('active_opco_id')
        )
        if opco_id and str(opco_id).lower() not in ['null', 'undefined', '', 'none', 'all']:
            try:
                return int(opco_id)
            except (ValueError, TypeError):
                return opco_id
        return None

    def get_queryset(self):
        queryset = super().get_queryset()
        opco_id = self._get_opco_id()
        if opco_id:
            try:
                queryset = queryset.filter(opco_id=int(opco_id))
            except (ValueError, TypeError):
                pass
        return queryset

    def perform_create(self, serializer):
        opco_id = self._get_opco_id()
        if opco_id:
            serializer.save(opco_id=int(opco_id))
        else:
            serializer.save()


class VendorViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة الموردين (Suppliers) - دمج Odoo & ERPNext """
    queryset = Vendor.objects.all().order_by('-id')
    serializer_class = VendorSerializer

    @action(detail=True, methods=['get'])
    def ledger(self, request, pk=None):
        vendor = self.get_object()
        pos = PurchaseOrder.objects.filter(vendor=vendor).order_by('-date')
        
        history = []
        for po in pos:
            history.append({
                'id': po.id,
                'date': po.date,
                'type': 'PURCHASE_ORDER',
                'number': po.po_number,
                'status': po.status,
                'amount': float(sum(line.quantity * line.unit_price for line in po.lines.all())),
                'doc_type': 'PO'
            })
            for receipt in po.receipts.all():
                history.append({
                    'id': receipt.id,
                    'date': receipt.date.date() if hasattr(receipt.date, 'date') else receipt.date,
                    'type': 'STOCK_RECEIPT',
                    'number': receipt.receipt_number,
                    'status': 'RECEIVED',
                    'amount': 0,
                    'doc_type': 'GRN'
                })

        # فواتير المشتريات (Purchase Invoices / Bills)
        try:
            from apps.accounting.models import PurchaseInvoice
            invoices = PurchaseInvoice.objects.filter(vendor=vendor).order_by('-posting_date')
            for inv in invoices:
                history.append({
                    'id': inv.id,
                    'date': inv.posting_date,
                    'type': 'PURCHASE_INVOICE',
                    'number': inv.invoice_number,
                    'status': inv.status,
                    'amount': float(inv.grand_total),
                    'doc_type': 'BILL'
                })
        except Exception:
            pass

        # سندات الصرف والدفع للمورد (Payment Entries)
        try:
            from apps.accounting.models import PaymentEntry
            payments = PaymentEntry.objects.filter(party_type='VENDOR', party_id=vendor.id).order_by('-posting_date')
            for pay in payments:
                history.append({
                    'id': pay.id,
                    'date': pay.posting_date,
                    'type': 'PAYMENT_ENTRY',
                    'number': pay.entry_number,
                    'status': pay.status,
                    'amount': float(pay.paid_amount),
                    'doc_type': 'PAYMENT'
                })
        except Exception:
            pass

        from apps.wms.models import StockMove
        import datetime
        moves = StockMove.objects.filter(vendor=vendor).order_by('-created_at')
        for move in moves:
            amount = move.quantity * move.unit_cost
            history.append({
                'id': move.id,
                'date': move.created_at.date() if move.created_at else None,
                'type': 'DIRECT_STOCK_MOVE_IN' if move.move_type == 'IN' else 'DIRECT_STOCK_MOVE_OUT',
                'number': move.reference or f"MOVE-{move.id}",
                'status': 'RECEIVED' if move.move_type == 'IN' else 'RETURNED',
                'amount': float(amount),
                'doc_type': 'DIRECT_GRN' if move.move_type == 'IN' else 'DIRECT_GDN'
            })
        
        history.sort(key=lambda x: x['date'] if x['date'] is not None else datetime.date.min, reverse=True)
        
        return Response({
            'vendor_name': vendor.name,
            'vendor_code': vendor.code,
            'balance': float(vendor.balance),
            'summary': {
                'total_pos': pos.count() + moves.count(),
                'received_pos': pos.filter(status='RECEIVED').count() + moves.filter(move_type='IN').count(),
            },
            'transactions': history
        })


class PurchaseRequisitionViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ طلبات الشراء الداخلية (PR) """
    queryset = PurchaseRequisition.objects.all().order_by('-created_at')
    serializer_class = PurchaseRequisitionSerializer

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        pr = self.get_object()
        pr.status = 'APPROVED'
        pr.save()
        return Response({'status': 'Approved', 'requisition_number': pr.requisition_number})

    @action(detail=True, methods=['post'])
    def convert_to_rfq(self, request, pk=None):
        pr = self.get_object()
        if pr.status not in ['APPROVED', 'SUBMITTED']:
            return Response({'error': 'يجب اعتماد طلب الشراء قبل التحويل لطلب أسعار'}, status=400)
        
        rfq = RequestForQuotation.objects.create(
            opco=pr.opco,
            pr=pr,
            notes=f"تم إنشاؤه بناءً على طلب الشراء {pr.requisition_number}"
        )
        for line in pr.lines.all():
            rfq.lines.create(material=line.material, quantity=line.quantity)

        pr.status = 'CONVERTED'
        pr.save()
        return Response({'status': 'Converted to RFQ', 'rfq_number': rfq.rfq_number, 'rfq_id': rfq.id})


class RequestForQuotationViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ طلبات عروض الأسعار للموردين (RFQ) """
    queryset = RequestForQuotation.objects.all().order_by('-created_at')
    serializer_class = RequestForQuotationSerializer


class SupplierQuotationViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ عروض أسعار الموردين (Supplier Quotations) """
    queryset = SupplierQuotation.objects.all().order_by('-id')
    serializer_class = SupplierQuotationSerializer


class QuotationComparisonViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ مصفوفة مقارنة عروض الأسعار (Evaluation Matrix) """
    queryset = QuotationComparison.objects.all().order_by('-id')
    serializer_class = QuotationComparisonSerializer

    @action(detail=True, methods=['post'])
    def approve_and_generate_po(self, request, pk=None):
        comp = self.get_object()
        winning_sq_id = request.data.get('winning_quotation_id')
        if winning_sq_id:
            try:
                sq = SupplierQuotation.objects.get(id=winning_sq_id)
                comp.winning_quotation = sq
                comp.winning_vendor = sq.vendor
                comp.status = 'APPROVED'
                comp.save()
            except SupplierQuotation.DoesNotExist:
                return Response({'error': 'عرض السعر غير موجود'}, status=404)

        po = comp.generate_purchase_order()
        if po:
            return Response({
                'status': 'PO Generated Successfully',
                'po_id': po.id,
                'po_number': po.po_number
            })
        return Response({'error': 'لم يتم العثور على عرض سعر فائز معتمد'}, status=400)


class PurchaseOrderViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ إدارة أوامر الشراء والتوريد (PO) """
    queryset = PurchaseOrder.objects.all().order_by('-created_at')
    serializer_class = PurchaseOrderSerializer

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        po = self.get_object()
        po.status = 'APPROVED'
        po.save()
        return Response({'status': 'Approved', 'po_number': po.po_number})

    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        po = self.get_object()
        bin_id = request.data.get('bin_id')
        items_data = request.data.get('items', None)

        if not bin_id:
            return Response({'error': 'معرف الرف (Storage Bin ID) مطلوب لإتمام الاستلام.'}, status=400)
        
        try:
            target_bin = StorageBin.objects.get(id=bin_id)
            po.receive_items(target_bin, items_data)
            return Response({
                'status': 'Success',
                'po_status': po.status,
                'po_number': po.po_number
            })
        except StorageBin.DoesNotExist:
            return Response({'error': 'الرف المحدد غير موجود'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class StockReceiptViewSet(viewsets.ModelViewSet):
    queryset = StockReceipt.objects.all().order_by('-date')
    serializer_class = StockReceiptSerializer

    def create(self, request, *args, **kwargs):
        so_id = request.data.get('so_id')
        move_type = 'OUT' if so_id else 'IN'
        request.data['move_type'] = move_type

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                receipt = serializer.save(created_by=request.user if request.user.is_authenticated else None)
                if receipt.po:
                    po = receipt.po
                    if all(line.received_quantity >= line.quantity for line in po.lines.all()):
                        po.status = 'RECEIVED'
                        po.save()

                if so_id:
                    from apps.sales.models import SalesOrder
                    try:
                        so = SalesOrder.objects.get(id=so_id)
                        so.status = 'DELIVERED'
                        so.save()
                    except SalesOrder.DoesNotExist:
                        pass

                return Response({
                    'id': receipt.id,
                    'receipt_no': receipt.receipt_number,
                    'move_type': move_type,
                    'status': 'success',
                    'print_url': f'/print/grn/{receipt.id}/'
                }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PurchaseReturnViewSet(OpcoAwareMixin, viewsets.ModelViewSet):
    """ مردودات المشتريات (RTV) """
    queryset = PurchaseReturn.objects.all().order_by('-id')
    serializer_class = PurchaseReturnSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=['post'])
    def process_return(self, request, pk=None):
        rtv = self.get_object()
        bin_id = request.data.get('bin_id')
        if not bin_id:
            return Response({'error': 'معرف الرف المصدر مطلوب لإتمام المرتجع'}, status=400)

        try:
            source_bin = StorageBin.objects.get(id=bin_id)
            rtv.process_return(source_bin)
            return Response({
                'status': 'Completed',
                'return_number': rtv.return_number,
                'total_amount': float(rtv.total_amount)
            })
        except StorageBin.DoesNotExist:
            return Response({'error': 'الرف المصدر غير موجود'}, status=404)


class PurchaseOrderLineViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrderLine.objects.all()
    serializer_class = PurchaseOrderLineSerializer


def print_po_pdf(request, pk):
    try:
        po = PurchaseOrder.objects.get(pk=pk)
        return render_to_pdf('procurement/print_po.html', {'po': po})
    except PurchaseOrder.DoesNotExist:
        return HttpResponse("أمر التوريد غير موجود", status=404)
    
def print_grn_pdf(request, pk):
    receipt = get_object_or_404(StockReceipt, pk=pk)
    return render_to_pdf('procurement/print_grn.html', {'receipt': receipt})
