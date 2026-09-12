from rest_framework import permissions
from django.core.exceptions import PermissionDenied

class IsEnterpriseEnabled(permissions.BasePermission):
    """
    تحقق DRF Permission تضمن أن الشركة الحالية تعمل في وضع النظام الكامل Enterprise / Modular
    """
    message = "هذه الميزة متاحة فقط للنظام المؤسسي الكامل (Enterprise Mode)."

    def has_permission(self, request, view):
        opco = getattr(request, 'opco', None)
        if not opco and hasattr(request, 'session'):
            opco_id = request.session.get('active_opco_id')
            if opco_id:
                from apps.core.models import OpCo
                opco = OpCo.objects.filter(id=opco_id).first()
        
        if not opco and request.user.is_authenticated:
            # Fallback to user's company
            cu = request.user.company_assignments.filter(company__is_active=True).first()
            if cu:
                opco = cu.company

        if opco:
            return opco.system_mode in ['modular', 'enterprise', 'full']
        
        return True


class EnterpriseRequiredMixin:
    """
    Mixin للـ Views و ViewSets للتحقق من وضع Enterprise قبل إتمام العملية
    """
    def dispatch(self, request, *args, **kwargs):
        opco_id = (request.query_params.get('opco') or 
                   (request.data.get('opco') if hasattr(request, 'data') and isinstance(request.data, dict) else None) or 
                   request.session.get('active_opco_id'))
        
        if opco_id:
            from apps.core.models import OpCo
            opco = OpCo.objects.filter(id=opco_id).first()
            if opco and opco.system_mode == 'standalone':
                raise PermissionDenied("هذه الشاشة متاحة فقط في الوضع المؤسسي (Enterprise Mode).")
                
        return super().dispatch(request, *args, **kwargs)
