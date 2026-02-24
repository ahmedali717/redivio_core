from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import transaction
from django.db.models import Sum
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.models import OpCo
from apps.wms.models import Plant, StorageLocation, StockQuant, StorageBin
from apps.item_master.models import Material
from apps.procurement.models import Vendor, PurchaseOrder
from apps.core.serializers import OpCoSerializer, PlantSerializer, StorageLocationSerializer, StorageBinSerializer

User = get_user_model()

# =========================================================
#  SECTION 1: HTML PAGE VIEWS
# =========================================================

@ensure_csrf_cookie
def landing_view(request):
    # إزالة الـ redirect التلقائي مؤقتاً لكسر الـ Loop
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

def modules_puzzle_view(request):
    return render(request, 'modules_puzzle.html')

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
    exists = User.objects.filter(email__iexact=email).exists()
    return Response({'exists': exists})

class CheckAuthAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            # جلب الشركة المرتبطة بالمستخدم فقط
            user_opco = OpCo.objects.filter(owner=request.user).first()
            company_name = user_opco.name if user_opco else "REDIVIO Inc."

            return Response({
                "authenticated": True,
                "user": request.user.username,
                "email": request.user.email,
                "company": company_name,
                "is_superuser": request.user.is_superuser,
                "role": 'Admin' if request.user.is_superuser else 'Manager'
            })
        return Response({"authenticated": False})

class LoginAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # دعم الإيميل أو اليوزرنيم في حقل 'username'
        email = request.data.get('username') or request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({"error": "Please provide both email and password"}, status=400)

        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # ✅ الإصلاح: ربط الشركة بالجلسة فوراً لكي لا يطردك الميدل وير
            user_opco = OpCo.objects.filter(owner=user).first()
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

class TenantSignupAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        company_name = data.get('company') or data.get('company_name')
        email = data.get('email')
        password = data.get('password')
        currency = data.get('currency', 'USD')

        if not (company_name and email):
            return Response({"error": "Missing required fields"}, status=400)

        try:
            with transaction.atomic():
                # 1. إنشاء المستخدم
                user, created = User.objects.get_or_create(
                    username=email,
                    defaults={'email': email, 'is_superuser': False, 'is_staff': True}
                )
                if created:
                    user.set_password(password if password else 'Admin@123')
                    user.save()
                
                # تسجيل الدخول تلقائياً
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                # 2. إنشاء الشركة وربطها بالمالك (Owner)
                import random, string
                random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                
                opco, created = OpCo.objects.get_or_create(
                    name=company_name,
                    defaults={
                        'code': random_code, 
                        'currency': currency,
                        'owner': user
                    }
                )
                
                # ✅ الإصلاح: ربط الشركة الجديدة بالجلسة فوراً
                request.session['active_opco_id'] = opco.id
                request.session.modified = True

                # 3. إنشاء الهيكل التنظيمي الأولي
                if created:
                    plant = Plant.objects.create(
                        opco=opco, 
                        code="MAIN", 
                        name=f"{company_name} HQ"
                    )
                    StorageLocation.objects.create(
                        plant=plant, 
                        code="IN-1", 
                        name="Receiving"
                    )

                return Response({
                    "success": True,
                    "message": "Workspace ready!",
                    "redirect_url": "/dashboard/"
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class DashboardDataViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        # جلب الشركات التي يملكها المستخدم الحالي
        user_opcos = OpCo.objects.filter(owner=request.user)
        
        # حساب إجمالي المخزون باستخدام حقل 'plant' (لحل مشكلة الـ FieldError السابقة)
        stock_qty = 0
        if user_opcos.exists():
            stock_qty = StockQuant.objects.filter(
                plant__opco__in=user_opcos
            ).aggregate(total=Sum('quantity'))['total'] or 0

        kpis = {
            'materials': Material.objects.filter(opco__in=user_opcos).count(),
            'vendors': Vendor.objects.filter(opco__in=user_opcos).count(),
            'pending_pos': PurchaseOrder.objects.filter(opco__in=user_opcos, status='DRAFT').count(),
            'stock_qty': stock_qty,
        }
        return Response({'kpis': kpis})
    
# =========================================================
#  SECTION 3: VIEWSETS (CRUD with Isolation)
# =========================================================

class OpCoViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = OpCoSerializer

    def get_queryset(self):
        return OpCo.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class PlantViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = PlantSerializer

    def get_queryset(self):
        return Plant.objects.filter(opco__owner=self.request.user)

class LocationViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = StorageLocationSerializer

    def get_queryset(self):
        return StorageLocation.objects.filter(plant__opco__owner=self.request.user)

class StorageBinViewSet(viewsets.ModelViewSet):
    authentication_classes = [SessionAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = StorageBinSerializer

    def get_queryset(self):
        return StorageBin.objects.filter(storage_location__plant__opco__owner=self.request.user)