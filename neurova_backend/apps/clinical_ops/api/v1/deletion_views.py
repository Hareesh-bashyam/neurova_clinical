from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.clinical_ops.models_deletion import DeletionRequest
from apps.clinical_ops.services.deletion_executor import execute_deletion
from apps.clinical_ops.audit.logger import log_event

class AdminApproveDeletion(APIView):
    def post(self, request):
        dr_id = request.data.get("deletion_request_id")
        action = request.data.get("action")  # APPROVE / REJECT

        if not dr_id or action not in ["APPROVE", "REJECT"]:
            return Response({"error":"invalid_payload"}, status=400)

        dr = get_object_or_404(DeletionRequest, id=dr_id)

        if action == "REJECT":
            dr.status = "REJECTED"
            dr.save(update_fields=["status"])
            return Response({"ok": True, "status":"REJECTED"})

        # APPROVE → EXECUTE
        dr.status = "APPROVED"
        dr.save(update_fields=["status"])
        execute_deletion(dr)

        return Response({
            "success": True,
            "message": "Deletion approved successfully",
            "data":{
                "status":"EXECUTED"
            }
        }, status=status.HTTP_200_OK)
