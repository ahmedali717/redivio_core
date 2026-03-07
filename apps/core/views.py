from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import transaction
from django.db.models import Sum, Q
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

        days_remaining = 15
        if holding_opco and holding_opco.created_at:
            from django.utils import timezone
            diff = timezone.now() - holding_opco.created_at
            days_remaining = max(15 - diff.days, 0)

        header_opcos = [
            {
                "id": op.id,
                "name": op.name,
                "code": op.code,
                "is_holding": op.is_holding
            } for op in user_all_opcos.order_by('-is_holding', 'name')
        ]

        return Response({
            "authenticated": True,
            "user": request.user.username,
            "company_id": user_opco.id if user_opco else None,
            "holding_name": holding_opco.name if holding_opco else "REDIVIO Inc.",
            "days_remaining": days_remaining,
            "header_opcos": header_opcos,
            "is_superuser": request.user.is_superuser,
            "role": 'Admin' if request.user.is_superuser else 'Manager'
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
                user, created = User.objects.get_or_create(
                    username=email,
                    defaults={'email': email, 'is_superuser': False, 'is_staff': True}
                )
                if created:
                    user.set_password(password if password else 'Admin@123')
                    user.save()
                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')

                import random, string
                random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                
                opco, created = OpCo.all_objects.get_or_create(
                    name=company_name,
                    defaults={
                        'code': random_code, 
                        'currency': currency,
                        'owner': user,
                        'is_holding': True 
                    }
                )
                
                request.session['active_opco_id'] = opco.id
                request.session.modified = True

                if created:
                    plant = Plant.objects.create(opco=opco, code="MAIN", name=f"{company_name} HQ")
                    StorageLocation.objects.create(plant=plant, code="IN-1", name="Receiving")

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