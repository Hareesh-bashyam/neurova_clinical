from rest_framework.viewsets import ModelViewSet
from common.tenancy import OrgScopedQuerysetMixin
from common.permissions import IsStaff
from .models import Patient
from .serializers import PatientSerializer
from auditlogs.utils import log_event


class PatientViewSet(OrgScopedQuerysetMixin, ModelViewSet):
    serializer_class = PatientSerializer
    permission_classes = [IsStaff]
    queryset = Patient.objects.all()

    def perform_create(self, serializer):
        # IMPORTANT: delegate org injection to OrgScopedQuerysetMixin
        super().perform_create(serializer)

        patient = serializer.instance
        log_event(
            request=self.request,
            org=patient.organization,
            action="PATIENT_CREATED",
            entity_type="Patient",
            entity_id=patient.id,
        )
