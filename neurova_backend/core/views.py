from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsOrgAdmin
from .models import Organization
from .serializers import OrganizationSerializer, UserCreateSerializer
from auditlogs.utils import log_event

class OrganizationCreateView(CreateAPIView):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOrgAdmin]

    def perform_create(self, serializer):
        org = serializer.save()
        log_event(self.request, org, "CREATE_ORG", "Organization", org.id)

class UserCreateView(CreateAPIView):
    serializer_class = UserCreateSerializer
    permission_classes = [IsAuthenticated, IsOrgAdmin]

    def perform_create(self, serializer):
        user = serializer.save()
        org = user.profile.organization
        log_event(self.request, org, "CREATE_USER", "User", user.id)
