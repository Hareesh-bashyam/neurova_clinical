from rest_framework.viewsets import ReadOnlyModelViewSet
from common.tenancy import OrgScopedQuerysetMixin
from common.permissions import IsStaff
from .models import Panel
from .serializers import PanelSerializer


class PanelViewSet(OrgScopedQuerysetMixin, ReadOnlyModelViewSet):
    queryset = Panel.objects.all()
    serializer_class = PanelSerializer
    permission_classes = [IsStaff]
