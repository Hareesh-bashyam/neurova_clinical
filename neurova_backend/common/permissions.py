from rest_framework.permissions import BasePermission

def _role(user):
    return getattr(getattr(user, "profile", None), "role", None)

class IsOrgAdmin(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) == "ORG_ADMIN"

class IsClinician(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) in ["CLINICIAN", "ORG_ADMIN"]

class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) in ["STAFF", "CLINICIAN", "ORG_ADMIN"]

class IsAuditor(BasePermission):
    def has_permission(self, request, view):
        return _role(request.user) in ["AUDITOR", "ORG_ADMIN"]

