from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.permissions import IsOrgAdmin
from .importer import import_catalog
from auditlogs.utils import log_event


class CatalogImportView(APIView):
    permission_classes = [IsAuthenticated, IsOrgAdmin]

    def post(self, request):
        org = request.user.profile.organization
        data = request.data

        import_catalog(org, data)

        log_event(
            request=request,
            org=org,
            action="CATALOG_IMPORTED",
            entity_type="Catalog",
            entity_id="bulk",
            meta={
                "instruments": len(data.get("instruments", [])),
                "tests": len(data.get("tests", [])),
                "panels": len(data.get("panels", [])),
            },
        )

        return Response({"status": "imported"})
