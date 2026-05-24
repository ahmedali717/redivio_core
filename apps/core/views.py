from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import transaction
from django.db.models import Sum, Q
from django.views.decorators.csrf import ensure_csrf_cookie
from django.conf import settings

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.models import OpCo
from apps.wms.models import Plant, StorageLocation, StockQuant, StorageBin
from apps.item_master.models import Material
from apps.procurement.models import Vendor, PurchaseOrder
from apps.core.serializers import (
    OpCoSerializer, PlantSerializer, StorageLocationSerializer, 
    StorageBinSerializer, CompanyUserSerializer
)
from apps.core.models import CompanyUser

User = get_user_model()

# =========================================================
#  SECTION 1: HTML PAGE VIEWS
# =========================================================

@ensure_csrf_cookie
def landing_view(request):
    return render(request, 'landing.html') 

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('/') 

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_home')
    return render(request, 'signup.html')

from django.conf import settings
import json

def parse_csv_file(file):
    import csv
    content = file.read()
    try:
        decoded_content = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            decoded_content = content.decode('windows-1256')
        except UnicodeDecodeError:
            decoded_content = content.decode('utf-8', errors='ignore')
            
    lines = decoded_content.splitlines()
    reader = csv.DictReader(lines)
    fieldnames = [f.strip() for f in (reader.fieldnames or [])]
    rows = []
    for row in reader:
        cleaned_row = {}
        for k, v in row.items():
            if k is not None:
                cleaned_row[k.strip()] = v.strip() if v else ''
        rows.append(cleaned_row)
    return fieldnames, rows

def modules_puzzle_view(request):
    module_config = {
        'wms': {'id': 'wms', 'name': 'WMS', 'icon': 'fas fa-warehouse', 'color': '#f59e0b', 'desc': 'Inventory'},
        'sales': {'id': 'sales', 'name': 'SALES', 'icon': 'fas fa-chart-line', 'color': '#10b981', 'desc': 'CRM'},
        'procurement': {'id': 'procurement', 'name': 'SUPPLY', 'icon': 'fas fa-truck-fast', 'color': '#a855f7', 'desc': 'Procurement'},
        'teams': {'id': 'teams', 'name': 'TEAMS', 'icon': 'fas fa-users', 'color': '#3b82f6', 'desc': 'HR'},
        'restaurant_pos': {'id': 'restaurant_pos', 'name': 'POS', 'icon': 'fas fa-cash-register', 'color': '#ef4444', 'desc': 'Point of Sale System'},
        'item_master': {'id': 'item_master', 'name': 'CATALOG', 'icon': 'fas fa-box-open', 'color': '#14b8a6', 'desc': 'Item Master'},
    }
    
    # get installed business apps from settings
    installed_apps = [app.split('.')[-1] for app in settings.INSTALLED_APPS if app.startswith('apps.') and app != 'core']
    
    available_modules = []
    for app in installed_apps:
        if app in module_config:
            available_modules.append(module_config[app])
        else:
            available_modules.append({
                'id': app,
                'name': app.replace('_', ' ').upper(),
                'icon': 'fas fa-cubes',
                'color': '#94a3b8',
                'desc': 'Module'
            })
            
    return render(request, 'modules_puzzle.html', {'available_modules_json': json.dumps(available_modules)})

def otp_view(request):
    return render(request, 'otp.html')

def setup_view(request):
    return render(request, 'setup.html')

def dashboard_view(request):
    if not request.user.is_authenticated:
        return redirect('login_page')
    return render(request, 'index.html')


# =========================================================
#  SECTION 2: API ENDPOINTS
# =========================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def check_email_status(request):
    email = request.data.get('email')
    if not email: return Response({'exists': False})
    user = User.objects.filter(email__iexact=email).first()
    if user:
        # Check owned company first
        company = OpCo.all_objects.filter(owner=user).first()
        if not company:
            # Check company assignments if not owned directly
            company_user = CompanyUser.objects.filter(user=user).first()
            if company_user:
                company = company_user.company
        
        company_data = None
        if company:
            company_data = {
                'name': company.name,
                'code': company.code,
                'plan': company.get_plan_display(),
                'created_at': company.created_at.strftime('%Y-%m-%d') if company.created_at else None,
                'is_active': company.is_active,
                'owner_name': company.owner.username if company.owner else None,
            }
        return Response({
            'exists': True,
            'company': company_data
        })
    return Response({'exists': False})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def switch_active_company(request):
    company_id = request.data.get('company_id')
    if not company_id:
        return Response({"error": "Company ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    can_access = OpCo.all_objects.filter(id=company_id).filter(
        Q(owner=request.user) | Q(companyuser__user=request.user)
    ).exists()

    if can_access:
        request.session['active_opco_id'] = company_id
        request.session.modified = True
        return Response({"success": True, "message": "Company switched successfully"})
    
    return Response({"error": "Unauthorized access to this company"}, status=status.HTTP_403_FORBIDDEN)

class CheckAuthAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"authenticated": False})

        active_id = request.session.get('active_opco_id')
        user_all_opcos = OpCo.all_objects.filter(
            Q(owner=request.user) | Q(companyuser__user=request.user)
        ).distinct()

        user_opco = user_all_opcos.filter(id=active_id).first() if active_id else user_all_opcos.first()
        
        if user_opco and not active_id:
            request.session['active_opco_id'] = user_opco.id

        holding_opco = user_opco
        if user_opco:
            while holding_opco.parent:
                holding_opco = holding_opco.parent

        plan = holding_opco.plan if holding_opco else 'starter'
        if plan == 'business':
            days_limit = 9999
            sku_limit = 5000
        elif plan in ['professional', 'pro']:
            days_limit = 9999
            sku_limit = 99999
        elif plan == 'enterprise':
            days_limit = 9999
            sku_limit = 999999
        else: # starter / free
            days_limit = 9999
            sku_limit = 50

        days_remaining = days_limit
        if holding_opco and holding_opco.created_at:
            from django.utils import timezone
            diff = timezone.now() - holding_opco.created_at
            days_remaining = max(days_limit - diff.days, 0)

        target_opcos = OpCo.all_objects.filter(Q(id=user_opco.id) | Q(parent_id=user_opco.id)) if user_opco else OpCo.all_objects.none()
        sku_count = Material.objects.filter(opco__in=target_opcos).count() if user_opco else 0

        header_opcos = [
            {
                "id": op.id,
                "name": op.name,
                "code": op.code,
                "is_holding": op.is_holding
            } for op in user_all_opcos.order_by('-is_holding', 'name')
        ]

        # Get role for current active company
        current_role = 'admin' if request.user.is_superuser else 'manager'
        from apps.core.models import CompanyUser
        company_user = CompanyUser.objects.filter(user=request.user, company=user_opco).first()
        if company_user:
            current_role = company_user.role

        return Response({
            "authenticated": True,
            "user_id": request.user.id,
            "user": request.user.username,
            "company_id": user_opco.id if user_opco else None,
            "company_name": user_opco.name if user_opco else "REDIVIO",
            "currency": user_opco.currency if user_opco else "SAR",
            "holding_name": holding_opco.name if holding_opco else "REDIVIO Inc.",
            "days_remaining": days_remaining,
            "header_opcos": header_opcos,
            "is_superuser": request.user.is_superuser,
            "role": current_role,
            "system_mode": user_opco.system_mode if user_opco else 'modular',
            "purchased_modules": user_opco.purchased_modules if user_opco else [],
            "plan": plan,
            "sku_limit": sku_limit,
            "days_limit": days_limit,
            "sku_count": sku_count,
        })


class ChangePlanAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        active_id = request.session.get('active_opco_id')
        if not active_id:
            return Response({"error": "No active company found in session"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            opco = OpCo.all_objects.get(id=active_id)
        except OpCo.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Check permissions: only owner of the company or superuser can change plan
        if opco.owner != request.user and not request.user.is_superuser:
            return Response({"error": "Only the company owner can change the plan"}, status=status.HTTP_403_FORBIDDEN)
            
        plan = request.data.get('plan')
        # Normalize legacy plans for backwards compatibility
        if plan == 'free':
            plan = 'starter'
        elif plan == 'pro':
            plan = 'professional'

        if plan not in ['starter', 'business', 'professional', 'enterprise']:
            return Response({"error": f"Invalid plan choice: {plan}"}, status=status.HTTP_400_BAD_REQUEST)
            
        from django.utils import timezone
        opco.plan = plan
        opco.created_at = timezone.now()
        opco.save()
        
        return Response({
            "success": True,
            "message": f"Plan updated successfully to {plan}",
            "plan": plan
        })

class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({"error": "Please provide both email and password"}, status=400)

        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            user_opco = OpCo.all_objects.filter(owner=user).first()
            if user_opco:
                request.session['active_opco_id'] = user_opco.id
                request.session.modified = True
            
            return Response({
                "success": True,
                "message": "Success", 
                "redirect_url": "/dashboard/"
            })
        else:
            return Response({"error": "Invalid email or password"}, status=401)

from django.core.mail import send_mail

class TenantSignupAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        company_name = data.get('company') or data.get('company_name')
        email = data.get('email')
        password = data.get('password')
        
        # Check if email exists
        if User.objects.filter(email__iexact=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        currency = data.get('currency', 'USD')
        plan = data.get('plan', 'starter')
        if plan == 'free':
            plan = 'starter'
        elif plan == 'pro':
            plan = 'professional'
            
        if plan not in ['starter', 'business', 'professional', 'enterprise']:
            plan = 'starter'
        
        # New SaaS Fields
        contact_name = data.get('name', '')
        contact_phone = data.get('phone', '')
        industry = data.get('industry', '')
        database_name = data.get('database_name', '')
        system_mode = data.get('system_mode', 'modular')
        purchased_modules = data.get('modules', [])
        
        lang = data.get('lang', 'ar')
        from django.utils import translation
        translation.activate(lang)

        if not (company_name and email):
            return Response({"error": "Missing required fields"}, status=400)

        try:
            with transaction.atomic():
                user, created = User.objects.get_or_create(
                    username=email,
                    defaults={'email': email, 'is_superuser': False, 'is_staff': True}
                )
                if created:
                    user.set_password(password if password else 'Admin@123')
                    user.save()
                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                request.session['_language'] = lang
                request.session.modified = True

                import random, string
                random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                
                opco, created = OpCo.all_objects.get_or_create(
                    name=company_name,
                    defaults={
                        'code': random_code, 
                        'currency': currency,
                        'owner': user,
                        'is_holding': False,
                        'contact_name': contact_name,
                        'contact_phone': contact_phone,
                        'industry': industry,
                        'database_name': database_name,
                        'system_mode': system_mode,
                        'purchased_modules': purchased_modules,
                        'plan': plan
                    }
                )
                
                request.session['active_opco_id'] = opco.id
                request.session.modified = True

                if created:
                    plant = Plant.objects.create(opco=opco, code="MAIN", name=f"{company_name} HQ")
                    StorageLocation.objects.create(plant=plant, code="IN-1", name="Receiving")
                    
                    # إرسال بريد إلكتروني بالترحيب وبيانات التسجيل
                    try:
                        subject = f"Welcome to Redivio ERP - {company_name}"
                        message = f"""
                        Dear {contact_name},
                        
                        Welcome to Redivio ERP! Your workspace has been successfully created.
                        
                        Subscription Details:
                        --------------------
                        Company: {company_name}
                        Registration Code: {random_code}
                        System Mode: {system_mode}
                        Active Modules: {', '.join(purchased_modules) if purchased_modules else 'None'}
                        Login Email: {email}
                        
                        You can login to your dashboard directly.
                        
                        Best regards,
                        Redivio Support Team
                        """
                        send_mail(
                            subject,
                            message,
                            settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@redivio.com',
                            [email],
                            fail_silently=True,
                        )
                    except Exception as e:
                        # Log email error but don't stop the signup process
                        print(f"Failed to send email: {str(e)}")

                response = Response({
                    "success": True,
                    "message": "Workspace ready!",
                    "redirect_url": "/dashboard/"
                }, status=status.HTTP_201_CREATED)
                cookie_name = getattr(settings, 'LANGUAGE_COOKIE_NAME', 'django_language')
                response.set_cookie(cookie_name, lang)
                return response

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class DashboardDataViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        active_id = request.session.get('active_opco_id')
        if active_id:
            target_opcos = OpCo.all_objects.filter(Q(id=active_id) | Q(parent_id=active_id))
        else:
            target_opcos = OpCo.all_objects.filter(owner=request.user)

        stock_qty = 0
        if target_opcos.exists():
            stock_qty = StockQuant.objects.filter(
                plant__opco__in=target_opcos
            ).aggregate(total=Sum('quantity'))['total'] or 0

        kpis = {
            'materials': Material.objects.filter(opco__in=target_opcos).count(),
            'vendors': Vendor.objects.filter(opco__in=target_opcos).count(),
            'pending_pos': PurchaseOrder.objects.filter(opco__in=target_opcos, status='DRAFT').count(),
            'stock_qty': stock_qty,
        }
        return Response({'kpis': kpis})
    
# =========================================================
#  SECTION 3: VIEWSETS (Intelligent Hierarchy Filtering)
# =========================================================

class OpCoViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OpCoSerializer

    def get_queryset(self):
        # الكود الحالي للبحث (سليم)
        user_all_opcos = OpCo.all_objects.filter(
            Q(owner=self.request.user) | Q(companyuser__user=self.request.user)
        ).distinct()

        if self.request.query_params.get('all') == 'true':
            return user_all_opcos.order_by('-is_holding', 'name')

        active_id = self.request.session.get('active_opco_id')
        if not active_id:
            return user_all_opcos.order_by('-is_holding', 'name')

        active_opco = user_all_opcos.filter(id=active_id).first()
        
        if active_opco:
            if active_opco.is_holding:
                return user_all_opcos.filter(
                    Q(id=active_id) | Q(parent_id=active_id)
                ).order_by('-is_holding', 'name')
            
            return user_all_opcos.filter(id=active_id)

        return user_all_opcos.order_by('-is_holding', 'name')

    # 🚀 أضف هذه الدالة هنا لحل مشكلة الـ IntegrityError
    def perform_create(self, serializer):
        """
        عند إنشاء شركة جديدة، نقوم بربطها تلقائياً بالمستخدم الذي قام بالطلب
        ليكون هو الـ owner الخاص بها في قاعدة البيانات.
        """
        serializer.save(owner=self.request.user)
           
class PlantViewSet(viewsets.ModelViewSet):
    serializer_class = PlantSerializer
    def get_queryset(self):
        active_id = self.request.session.get('active_opco_id')
        if not active_id: return Plant.objects.none()
        
        active_opco = OpCo.all_objects.filter(id=active_id).first()
        
        if active_opco and active_opco.is_holding:
            return Plant.objects.filter(
                Q(opco_id=active_id) | Q(opco__parent_id=active_id)
            ).distinct()
        
        return Plant.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        if StockQuant.objects.filter(plant=instance, quantity__gt=0).exists():
            return Response(
                {"error": "لا يمكن حذف المنشأة لوجود رصيد بضاعة بها." if is_arabic else "Cannot delete plant because it has stock balance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='import')
    def import_plants(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        active_id = request.session.get('active_opco_id')
        if not active_id:
            return Response({"error": "No active company selected"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                headers, rows = parse_csv_file(file)
            else:
                try:
                    import pandas as pd
                    df = pd.read_excel(file)
                    headers = [str(c).strip() for c in df.columns]
                    rows = []
                    for _, r in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            val = r[col]
                            row_dict[str(col).strip()] = str(val).strip() if pd.notna(val) else ''
                        rows.append(row_dict)
                except ImportError:
                    return Response({"error": "Excel import is not supported because 'pandas' is not installed. Please save your file as CSV (.csv) and try again."}, status=status.HTTP_400_BAD_REQUEST)
                
            success_count = 0
            skipped_count = 0
            
            # Map Arabic and English headers
            code_col = 'الكود' if 'الكود' in headers else ('كود المنشأة' if 'كود المنشأة' in headers else ('Plant Code' if 'Plant Code' in headers else 'Code'))
            name_col = 'الاسم' if 'الاسم' in headers else ('اسم المنشأة' if 'اسم المنشأة' in headers else ('Plant Name' if 'Plant Name' in headers else 'Name'))
            
            if code_col not in headers or name_col not in headers:
                return Response({"error": f"Missing required columns. Ensure '{code_col}' and '{name_col}' exist."}, status=status.HTTP_400_BAD_REQUEST)

            active_opco = OpCo.all_objects.filter(id=active_id).first()
            
            with transaction.atomic():
                for row in rows:
                    code = str(row.get(code_col, '')).strip()
                    name = str(row.get(name_col, '')).strip()
                    
                    if not code or not name or str(code).lower() == 'nan' or str(name).lower() == 'nan':
                        continue
                        
                    # Check uniqueness
                    if Plant.objects.filter(opco=active_opco, code=code).exists() or Plant.objects.filter(opco=active_opco, name=name).exists():
                        skipped_count += 1
                        continue
                        
                    Plant.objects.create(
                        opco=active_opco,
                        code=code[:5],
                        name=name[:100]
                    )
                    success_count += 1
                    
            return Response({
                "message": "Import successful",
                "success_count": success_count,
                "skipped_count": skipped_count
            })
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = StorageLocationSerializer
    def get_queryset(self):
        active_id = self.request.session.get('active_opco_id')
        active_opco = OpCo.all_objects.filter(id=active_id).first()
        
        if active_opco and active_opco.is_holding:
            return StorageLocation.objects.filter(
                Q(plant__opco_id=active_id) | Q(plant__opco__parent_id=active_id)
            ).distinct()
        
        return StorageLocation.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        if StockQuant.objects.filter(storage_bin__storage_location=instance, quantity__gt=0).exists():
            return Response(
                {"error": "لا يمكن حذف موقع التخزين لوجود رصيد بضاعة به." if is_arabic else "Cannot delete storage location because it has stock balance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='import')
    def import_locations(self, request):
        file = request.FILES.get('file')
        if not file: return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        active_id = request.session.get('active_opco_id')
        if not active_id: return Response({"error": "No active company selected"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                headers, rows = parse_csv_file(file)
            else:
                try:
                    import pandas as pd
                    df = pd.read_excel(file)
                    headers = [str(c).strip() for c in df.columns]
                    rows = []
                    for _, r in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            val = r[col]
                            row_dict[str(col).strip()] = str(val).strip() if pd.notna(val) else ''
                        rows.append(row_dict)
                except ImportError:
                    return Response({"error": "Excel import is not supported because 'pandas' is not installed. Please save your file as CSV (.csv) and try again."}, status=status.HTTP_400_BAD_REQUEST)

            success_count, skipped_count = 0, 0
            
            pcode_col = 'كود المنشأة' if 'كود المنشأة' in headers else 'Plant Code'
            code_col = 'كود الموقع' if 'كود الموقع' in headers else 'Location Code'
            name_col = 'اسم الموقع' if 'اسم الموقع' in headers else 'Location Name'
            
            if not all(col in headers for col in [pcode_col, code_col, name_col]):
                return Response({"error": "Missing columns. Ensure Plant Code, Location Code, and Location Name exist."}, status=status.HTTP_400_BAD_REQUEST)

            active_opco = OpCo.all_objects.filter(id=active_id).first()
            
            with transaction.atomic():
                for row in rows:
                    pcode = str(row.get(pcode_col, '')).strip()
                    code = str(row.get(code_col, '')).strip()
                    name = str(row.get(name_col, '')).strip()
                    
                    if not pcode or not code or not name or str(code).lower() == 'nan': continue
                        
                    plant = Plant.objects.filter(opco=active_opco, code=pcode).first()
                    if not plant:
                        skipped_count += 1
                        continue
                        
                    if StorageLocation.objects.filter(plant=plant, code=code).exists() or StorageLocation.objects.filter(plant=plant, name=name).exists():
                        skipped_count += 1
                        continue
                        
                    StorageLocation.objects.create(plant=plant, code=code[:10], name=name[:100])
                    success_count += 1
                    
            return Response({"message": "Import successful", "success_count": success_count, "skipped_count": skipped_count})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class StorageBinViewSet(viewsets.ModelViewSet):
    serializer_class = StorageBinSerializer
    def get_queryset(self):
        active_id = self.request.session.get('active_opco_id')
        active_opco = OpCo.all_objects.filter(id=active_id).first()
        
        if active_opco and active_opco.is_holding:
            return StorageBin.objects.filter(
                Q(storage_location__plant__opco_id=active_id) | 
                Q(storage_location__plant__opco__parent_id=active_id)
            ).distinct()
            
        return StorageBin.objects.all()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        is_arabic = request.LANGUAGE_CODE and request.LANGUAGE_CODE.startswith('ar')
        if StockQuant.objects.filter(storage_bin=instance, quantity__gt=0).exists():
            return Response(
                {"error": "لا يمكن حذف الرف لوجود رصيد بضاعة به." if is_arabic else "Cannot delete bin because it has stock balance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='import')
    def import_bins(self, request):
        file = request.FILES.get('file')
        if not file: return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        active_id = request.session.get('active_opco_id')
        if not active_id: return Response({"error": "No active company selected"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            if file.name.endswith('.csv'):
                headers, rows = parse_csv_file(file)
            else:
                try:
                    import pandas as pd
                    df = pd.read_excel(file)
                    headers = [str(c).strip() for c in df.columns]
                    rows = []
                    for _, r in df.iterrows():
                        row_dict = {}
                        for col in df.columns:
                            val = r[col]
                            row_dict[str(col).strip()] = str(val).strip() if pd.notna(val) else ''
                        rows.append(row_dict)
                except ImportError:
                    return Response({"error": "Excel import is not supported because 'pandas' is not installed. Please save your file as CSV (.csv) and try again."}, status=status.HTTP_400_BAD_REQUEST)

            success_count, skipped_count = 0, 0
            
            lcode_col = 'كود الموقع' if 'كود الموقع' in headers else 'Location Code'
            code_col = 'كود الرف' if 'كود الرف' in headers else 'Bin Code'
            
            if not all(col in headers for col in [lcode_col, code_col]):
                return Response({"error": "Missing columns. Ensure Location Code and Bin Code exist."}, status=status.HTTP_400_BAD_REQUEST)

            active_opco = OpCo.all_objects.filter(id=active_id).first()
            
            with transaction.atomic():
                for row in rows:
                    lcode = str(row.get(lcode_col, '')).strip()
                    code = str(row.get(code_col, '')).strip()
                    
                    if not lcode or not code or str(code).lower() == 'nan': continue
                        
                    loc = StorageLocation.objects.filter(plant__opco=active_opco, code=lcode).first()
                    if not loc:
                        skipped_count += 1
                        continue
                        
                    if StorageBin.objects.filter(storage_location=loc, code=code).exists():
                        skipped_count += 1
                        continue
                        
                    StorageBin.objects.create(storage_location=loc, code=code[:20])
                    success_count += 1
                    
            return Response({"message": "Import successful", "success_count": success_count, "skipped_count": skipped_count})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
class CompanyUserViewSet(viewsets.ModelViewSet):
    serializer_class = CompanyUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        active_id = self.request.session.get('active_opco_id')
        if not active_id:
            return CompanyUser.objects.none()
        
        active_opco = OpCo.all_objects.filter(id=active_id).first()
        if not active_opco:
            return CompanyUser.objects.none()

        # base queryset
        if active_opco.is_holding:
            qs = CompanyUser.objects.filter(
                Q(company_id=active_id) | Q(company__parent_id=active_id)
            )
        else:
            qs = CompanyUser.objects.filter(company_id=active_id)
        
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data

        # Add owner if not present
        active_id = request.query_params.get('opco')
        if active_id:
            active_opco = OpCo.all_objects.filter(id=active_id).first()
            if active_opco and active_opco.owner:
                owner_email = active_opco.owner.email or active_opco.owner.username
                is_owner_in_list = any(u['user_details']['email'] == owner_email or u['user_details']['username'] == owner_email for u in data)
                
                if not is_owner_in_list:
                    data.insert(0, {
                        'id': 'OWNER',
                        'role': 'ADMINISTRATOR',
                        'company_name': active_opco.name,
                        'company': active_opco.id,
                        'user_details': {
                            'id': active_opco.owner.id,
                            'username': active_opco.owner.username,
                            'email': active_opco.owner.email or active_opco.owner.username,
                        }
                    })
        
        return Response(data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        role = request.data.get('role', 'cashier')
        password = request.data.get('password')
        company_id = request.data.get('company') or request.session.get('active_opco_id')
        
        if not email or not company_id:
            return Response({"error": "Email and Company are required"}, status=400)
            
        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'is_staff': True}
        )
        # تعيين كلمة المرور سواء كان مستخدم جديد أو تحديث لكلمة المرور
        if password:
            user.set_password(password)
        elif created:
            user.set_password('Admin@123')
        
        user.save()
            
        company_user, cu_created = CompanyUser.objects.get_or_create(
            user=user,
            company_id=company_id,
            defaults={'role': role}
        )
        
        if not cu_created:
            company_user.role = role
            company_user.save()
            
        return Response(CompanyUserSerializer(company_user).data)

    @action(detail=False, methods=['post'])
    def verify_password(self, request):
        user_id = request.data.get('user_id')
        password = request.data.get('password')
        
        if not user_id or not password:
            return Response({"error": "User ID and password are required"}, status=400)
            
        try:
            if user_id == 'OWNER':
                active_id = request.session.get('active_opco_id')
                opco = OpCo.all_objects.get(id=active_id)
                user = opco.owner
            else:
                cu = CompanyUser.objects.get(id=user_id)
                user = cu.user
                
            if user.check_password(password):
                return Response({"success": True})
            else:
                return Response({"success": False, "error": "Invalid password"}, status=401)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        email = request.data.get('email')
        role = request.data.get('role')
        password = request.data.get('password')
        company_id = request.data.get('company')

        if email:
            user = instance.user
            user.username = email
            user.email = email
            if password:
                user.set_password(password)
            user.save()

        if role:
            instance.role = role
        if company_id:
            instance.company_id = company_id
        
        instance.save()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_debug_logs(request):
    import os
    log_path = "/var/log/ahmedali717.pythonanywhere.com.error.log"
    if not os.path.exists(log_path):
        return Response({"error": f"Log file not found at {log_path}"})
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-200:]
            return Response({"logs": "".join(lines)})
    except Exception as e:
        return Response({"error": str(e)})
