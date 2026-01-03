from rest_framework.exceptions import NotFound

class OrgScopedQuerysetMixin:
    """
    Enforce organization scoping automatically for every ViewSet.
    Models MUST have `organization` FK field.
    """
    org_field = "organization"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not hasattr(user, "profile") or not user.profile.organization_id:
            return qs.none()
        return qs.filter(**{f"{self.org_field}_id": user.profile.organization_id})

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, "profile") or not user.profile.organization_id:
            raise NotFound("Organization not found.")
        serializer.save(**{self.org_field: user.profile.organization})

