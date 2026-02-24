from .models import OpCo 

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if not request.user.is_authenticated:
            return self.get_response(request)

        tenant_id = request.session.get("active_opco_id")

        tenant = None

        if tenant_id:
            tenant = OpCo.objects.filter(
                id=tenant_id,
                owner=request.user,
                is_active=True
            ).first()

        if not tenant:
            tenant = OpCo.objects.filter(
                owner=request.user,
                is_active=True
            ).first()

            if tenant:
                request.session["active_opco_id"] = tenant.id

        request.tenant = tenant

        return self.get_response(request)