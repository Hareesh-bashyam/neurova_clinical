import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from apps.clinical_ops.models import AssessmentOrder, Org
from apps.clinical_ops.services.data_exporter import export_order_data
from apps.clinical_ops.audit.logger import log_event


logger = logging.getLogger(__name__)


class ExportOrderJSON(APIView):
    def get(self, request):
        try:
            org_id = request.query_params.get("org_id")
            order_id = request.query_params.get("order_id")
            org = get_object_or_404(Org, id=org_id, is_active=True)
            order = get_object_or_404(AssessmentOrder, id=order_id, org=org)

            data = export_order_data(order)

            log_event(
                org_id=order.org_id,
                event_type="DATA_EXPORT",
                entity_type="AssessmentOrder",
                entity_id=order.id,
                actor_user_id=str(request.user.id) if request.user and request.user.is_authenticated else None,
                actor_role="Staff",
                details={}
            )

            resp = HttpResponse(data, content_type="application/json")
            resp["Content-Disposition"] = f'attachment; filename="order_{order.id}_export.json"'
            return resp
        except Exception as e:
            logger.error(f"Error exporting order JSON: {str(e)}", exc_info=True)
            return Response(
                {
                    "success": False,
                    "message": "An unexpected error occurred while exporting data.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        
