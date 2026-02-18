from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from rest_framework.exceptions import PermissionDenied

from common.encryption_decorators import encrypt_response

from apps.clinical_ops.services.public_token_validator import validate_and_rotate_url_token


class PublicOrderBootstrap(APIView):
    authentication_classes = []
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    @encrypt_response
    def get(self, request, token):


        try:
            # Secure validation + rotation
            order, new_token = validate_and_rotate_url_token(token, request)

            # Mark started if not started
            if order.status == order.STATUS_IN_PROGRESS:
                order.mark_started()

            response = Response(
                {
                    "success": True,
                    "message": "Order initialized successfully",
                    "data": {
                        "org_id": order.org.id,
                        "order_id": order.id,
                        "patient_id": order.patient.id,
                        "patient_name": order.patient.full_name,
                        "patient_age": order.patient.age,
                        "patient_gender": order.patient.sex,
                        "battery_code": order.battery_code,
                        "battery_version": order.battery_version,
                        "status": order.status,
                        "public_token": new_token,
                    },
                },
                status=status.HTTP_200_OK,
            )

            # Return rotated token
            response["X-Public-Token"] = new_token

            return response

        except PermissionDenied as e:
            return Response(
                {
                    "success": False,
                    "message": str(e),
                    "data": None,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        except Exception:
            return Response(
                {
                    "success": False,
                    "message": "Unable to initialize order.",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
