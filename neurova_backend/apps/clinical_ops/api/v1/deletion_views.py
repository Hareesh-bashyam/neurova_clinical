from django.shortcuts import get_object_or_404
from django.db import transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.clinical_ops.models_deletion import DeletionRequest
from apps.clinical_ops.services.deletion_executor import execute_deletion
from apps.clinical_ops.audit.logger import log_event


class AdminApproveDeletion(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        dr_id = request.data.get("deletion_request_id")
        action = request.data.get("action")  # APPROVE / REJECT

        if not dr_id or action not in ["APPROVE", "REJECT"]:
            return Response(
                {"success": False, "message": "invalid payload", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Org isolation
        org = request.user.profile.organization

        dr = get_object_or_404(
            DeletionRequest,
            id=dr_id,
            org=org,
        )

        # State guard
        if dr.status != "REQUESTED":
            return Response(
                {
                    "success": False,
                    "message": f"Deletion request already {dr.status}",
                    "data": None
                },
                status=status.HTTP_409_CONFLICT,
            )

        # REJECT
        if action == "REJECT":
            dr.status = "REJECTED"
            dr.save(update_fields=["status"])

            log_event(
                org_id=org.id,
                event_type="DELETION_REJECTED",
                entity_type="DeletionRequest",
                entity_id=dr.id,
                actor_user_id=str(request.user.id),
                actor_role="ADMIN",
                details={"reason": "Admin rejected deletion"},
            )

            return Response(
                {
                    "success": True,
                    "message": "Deletion request rejected successfully",
                    "data": {"status": "REJECTED"},
                },
                status=status.HTTP_200_OK,
            )

        # APPROVE → EXECUTE
        dr.status = "APPROVED"
        dr.save(update_fields=["status"])

        execute_deletion(dr)

        log_event(
            org_id=org.id,
            event_type="DELETION_EXECUTED",
            entity_type="DeletionRequest",
            entity_id=dr.id,
            actor_user_id=str(request.user.id),
            actor_role="ADMIN",
            details={"method": "SYSTEM_EXECUTION"},
        )

        return Response(
            {
                "success": True,
                "message": "Deletion approved and executed successfully",
                "data": {
                    "status": "EXECUTED",
                },
            },
            status=status.HTTP_200_OK,
        )
