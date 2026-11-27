import csv
import re
import io
from decimal import Decimal, InvalidOperation
from rest_framework import viewsets, exceptions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q

from .models import Category, Material, SaleGroup
from .serializers import CategorySerializer, MaterialSerializer, SaleGroupSerializer
from apps.core.models import OpCo


# =========================================================
#  Helper Functions
# =========================================================
def safe_decimal(val, default=Decimal('0.00')):
    """ تحويل آمن للأرقام العشرية مع تجريد رموز العملات والنصوص الغريبة """
    if val is None:
        return default
    s = str(val).strip()
    if not s or s.lower() in ['nan', 'none', 'null', 'unit', '-', 'n/a']:
        return default
    # استخراج الأرقام مع النقطة العشرية والإشارة السالبة فقط
    cleaned = re.sub(r'[^\d.-]', '', s)
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError, TypeError):
        return default


def normalize_header(header_str):
    """ تنظيف اسم العمود لمطابقته بمرونة مع الكلمات المفتاحية """
    if not header_str:
        return ''
    return re.sub(r'[^a-zA-Z0-9\u0621-\u064A]', '', str(header_str)).lower()


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
    queryset = Material.objects.none()
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
    # 🚀 3. دالة الاستيراد الشاملة والمطورة (تدعم CSV و Excel وقوالب النظام المتنوعة)
    # =========================================================
    @action(detail=False, methods=['post'], url_path='import')
    def import_data(self, request):
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({'error': 'الرجاء اختيار ملف للرفع / Please upload a file'}, status=status.HTTP_400_BAD_REQUEST)

        # تحديد الشركة المستهدفة
        opco_id = (
            request.data.get('opco_id') or 
            request.data.get('opco') or 
            request.query_params.get('opco') or 
            request.session.get('active_opco_id')
        )
        if not opco_id and hasattr(request, 'user') and request.user.is_authenticated:
            cu = getattr(request.user, 'companyuser_set', None)
            first_cu = cu.first() if cu else None
            if first_cu:
                opco_id = first_cu.opco_id

        target_opco = OpCo.all_objects.filter(id=opco_id).first() if opco_id else None

        filename = uploaded_file.name.lower()
        rows_data = []

        try:
            # 1. قراءة الملف سواء كان CSV أو Excel
            if filename.endswith('.csv'):
                content = uploaded_file.read()
                decoded_str = None
                for encoding in ['utf-8-sig', 'utf-8', 'windows-1256', 'latin-1']:
                    try:
                        decoded_str = content.decode(encoding)
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                
                if decoded_str is None:
                    decoded_str = content.decode('utf-8', errors='replace')

                lines = decoded_str.splitlines()
                if not lines:
                    return Response({'error': 'الملف المرفوع فارغ / Uploaded file is empty'}, status=status.HTTP_400_BAD_REQUEST)

                reader = csv.DictReader(lines)
                raw_headers = reader.fieldnames or []
                for r in reader:
                    cleaned_row = {str(k).strip(): (str(v).strip() if v is not None else '') for k, v in r.items() if k is not None}
                    rows_data.append(cleaned_row)

            elif filename.endswith(('.xlsx', '.xls')):
                try:
                    import pandas as pd
                    df = pd.read_excel(uploaded_file)
                    raw_headers = [str(c).strip() for c in df.columns]
                    for _, r in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            val = r[col]
                            row_dict[str(col).strip()] = str(val).strip() if pd.notna(val) else ''
                        rows_data.append(row_dict)
                except ImportError:
                    return Response({
                        'error': "استيراد ملفات Excel غير مدعوم على السيرفر لعدم توفر مكتبة pandas. يرجى حفظ الملف كـ CSV (.csv) وإعادة المحاولة."
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'صيغة الملف غير مدعومة. يرجى رفع ملف بصيغة CSV أو Excel (.xlsx)'}, status=status.HTTP_400_BAD_REQUEST)

            if not rows_data:
                return Response({'error': 'لا توجد بيانات صالحة للقراءة داخل الملف'}, status=status.HTTP_400_BAD_REQUEST)

            # 2. بناء خريطة الأعمدة المرنة (Flexible Header Mapping)
            header_map = {}
            for raw_h in raw_headers:
                norm_h = normalize_header(raw_h)
                header_map[norm_h] = raw_h

            def find_col(aliases):
                for alias in aliases:
                    norm_alias = normalize_header(alias)
                    if norm_alias in header_map:
                        return header_map[norm_alias]
                return None

            col_sku = find_col(['sku', 'code', 'item_code', 'كود', 'رمز', 'رمز_الصنف', 'كود_الصنف', 'رقم_الصنف'])
            col_name = find_col(['name', 'item_name', 'product_name', 'اسم', 'اسم_الصنف', 'اسم_المنتج', 'الاسم', 'اسم_المادة'])
            col_category = find_col(['category_code', 'category', 'cat', 'group', 'فئة', 'الفئة', 'تصنيف', 'التصنيف', 'كود_التصنيف', 'كود_الفئة', 'مجموعة'])
            col_uom = find_col(['base_uom', 'uom', 'unit', 'وحدة', 'الوحدة', 'وحدة_القياس', 'الوحدة_الأساسية'])
            col_sales_price = find_col(['sales_price', 'sale_price', 'price', 'سعر_البيع', 'سعر_التجزئة', 'سعر', 'السعر'])
            col_cost_price = find_col(['cost_price', 'standard_price', 'cost', 'سعر_التكلفة', 'التكلفة', 'سعر_الشراء'])
            col_barcode = find_col(['barcode', 'bar_code', 'باركود', 'الباركود'])
            col_reorder = find_col(['reorder_level', 'reorder_point', 'min_level', 'حد_إعادة_الطلب', 'الحد_الأدنى', 'حد_الطلب'])
            col_desc = find_col(['description', 'desc', 'وصف', 'الوصف', 'بيان'])
            col_tracking = find_col(['tracking', 'tracking_type', 'تتبع', 'نوع_التتبع'])
            col_alt_uom = find_col(['alternate_uom', 'alt_uom', 'وحدة_بديلة', 'الوحدة_البديلة'])
            col_conv = find_col(['uom_conversion_factor', 'conversion_factor', 'conversion_ratio', 'معامل_التحويل', 'نسبة_التحويل'])
            col_active = find_col(['is_active', 'active', 'status', 'نشط', 'الحالة'])

            created_count = 0
            updated_count = 0
            skipped_count = 0

            # 3. معالجة الصفوف في عملية قاعدة بيانات ذرية (Atomic Transaction)
            with transaction.atomic():
                for idx, row in enumerate(rows_data):
                    # استخراج SKU والاسم
                    sku_val = ''
                    name_val = ''

                    if col_sku:
                        sku_val = str(row.get(col_sku, '')).strip()
                    if col_name:
                        name_val = str(row.get(col_name, '')).strip()

                    # إذا لم توجد ترويسات، نستخدم الموقع الترتيبي (Fallback)
                    if not sku_val and len(raw_headers) >= 2:
                        raw_vals = list(row.values())
                        if len(raw_vals) >= 2:
                            sku_val = str(raw_vals[0]).strip()
                            name_val = str(raw_vals[1]).strip()

                    # تخطي الصفوف الفارغة أو رؤوس الأعمدة المتكررة
                    if not sku_val or str(sku_val).lower() in ['nan', 'none', 'null', 'sku', 'كود']:
                        skipped_count += 1
                        continue

                    if not name_val:
                        name_val = sku_val # استخدام الـ SKU كاسم إذا كان الاسم فارغاً

                    # الفئة / التصنيف
                    cat_val = str(row.get(col_category, '')).strip() if col_category else ''
                    category_obj = None
                    if cat_val and cat_val.lower() not in ['nan', 'none', 'null', '']:
                        category_obj = Category.objects.filter(
                            Q(code__iexact=cat_val) | Q(name__iexact=cat_val)
                        ).first()
                        if not category_obj:
                            # إنشاء الفئة تلقائياً إذا لم تكن موجودة
                            category_obj = Category.objects.create(
                                code=cat_val[:50],
                                name=cat_val[:100]
                            )

                    # وحدة القياس
                    uom_val = str(row.get(col_uom, '')).strip() if col_uom else ''
                    if not uom_val or uom_val.lower() in ['nan', 'none', 'null']:
                        uom_val = 'PCS'

                    # الأسعار والحدود (تحويل رقمي آمن)
                    sales_price = safe_decimal(row.get(col_sales_price)) if col_sales_price else Decimal('0.00')
                    cost_price = safe_decimal(row.get(col_cost_price)) if col_cost_price else Decimal('0.00')
                    reorder_lvl = safe_decimal(row.get(col_reorder)) if col_reorder else Decimal('0.00')

                    # الباركود
                    barcode_val = str(row.get(col_barcode, '')).strip() if col_barcode else ''
                    if barcode_val.lower() in ['nan', 'none', 'null']:
                        barcode_val = ''

                    # التتبع
                    tracking_val = str(row.get(col_tracking, '')).strip().lower() if col_tracking else 'none'
                    if tracking_val not in ['serial', 'lot']:
                        tracking_val = 'none'

                    # الحقول التفصيلية
                    desc_val = str(row.get(col_desc, '')).strip() if col_desc else ''
                    if desc_val.lower() in ['nan', 'none', 'null']:
                        desc_val = ''

                    alt_uom_val = str(row.get(col_alt_uom, '')).strip() if col_alt_uom else ''
                    if alt_uom_val.lower() in ['nan', 'none', 'null']:
                        alt_uom_val = ''

                    conv_ratio = safe_decimal(row.get(col_conv), default=Decimal('1.0000')) if col_conv else Decimal('1.0000')

                    is_active = True
                    if col_active:
                        act_val = str(row.get(col_active, '')).strip().lower()
                        if act_val in ['0', 'false', 'no', 'إيقاف', 'معطل', 'غير نشط']:
                            is_active = False

                    defaults = {
                        'name': name_val,
                        'base_uom': uom_val,
                        'sales_price': sales_price,
                        'standard_price': cost_price,
                        'reorder_level': reorder_lvl,
                        'barcode': barcode_val or None,
                        'tracking': tracking_val,
                        'description': desc_val,
                        'alternate_uom': alt_uom_val or None,
                        'uom_conversion_factor': conv_ratio,
                        'is_active': is_active,
                    }

                    if category_obj:
                        defaults['category'] = category_obj

                    if target_opco:
                        defaults['opco'] = target_opco

                    # إنشاء أو تحديث الصنف مع مراعاة الشركة (Multi-Tenant Isolation)
                    lookup_kwargs = {'sku': sku_val}
                    if target_opco:
                        lookup_kwargs['opco'] = target_opco

                    material, created = Material.all_objects.update_or_create(
                        defaults=defaults,
                        **lookup_kwargs
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            total_processed = created_count + updated_count
            return Response({
                'success': True,
                'count': total_processed,
                'created_count': created_count,
                'updated_count': updated_count,
                'skipped_count': skipped_count,
                'message': f"تم استيراد {created_count} صنف جديد وتحديث {updated_count} صنف بنجاح."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': f'حدث خطأ أثناء معالجة الملف: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
