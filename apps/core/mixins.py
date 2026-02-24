# core/mixins.py

from rest_framework import exceptions


class OpcoAwareMixin:
    """
    يفرض ربط أي سجل بالـ Tenant الحالي فقط.
    لا يسمح بتمرير opco من الـ request لحماية العزل.
    """

    def get_active_opco(self):
        opco = getattr(self.request, "tenant", None) or getattr(self.request, "active_opco", None)

        if not opco:
            raise exceptions.PermissionDenied(
                "No active company selected."
            )

        if not opco.is_active:
            raise exceptions.PermissionDenied(
                "This company is suspended."
            )

        return opco

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(opco=self.get_active_opco())

    def perform_create(self, serializer):
        serializer.save(opco=self.get_active_opco())
