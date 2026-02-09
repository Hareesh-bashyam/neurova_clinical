from django.shortcuts import get_object_or_404 
from django.utils import timezone 
 
from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 
from rest_framework.throttling import AnonRateThrottle 
 
from apps.clinical_ops.models import AssessmentOrder
from apps.clinical_ops.battery_assessment_model import BatteryAssessment,Battery 
 
 
class PublicQuestionDisplay(APIView): 
    authentication_classes = [] 
    permission_classes = [] 
    throttle_classes = [AnonRateThrottle] 
 
    def get(self, request, token): 
        # Resolve order 
        order = get_object_or_404( 
            AssessmentOrder, 
            public_token=token, 
            deletion_status="ACTIVE" 
        ) 
 
        # Expiry check (optional but recommended) 
        if order.public_link_expires_at and timezone.now() > order.public_link_expires_at: 
            return Response( 
                {"success": False, "message": "Link expired"}, 
                status=status.HTTP_403_FORBIDDEN, 
            ) 
 
        # Resolve battery USING battery_code (IMPORTANT FIX) 
        battery = get_object_or_404( 
            Battery, 
            battery_code=order.battery_code, 
            is_active=True 
        ) 
 
        # Fetch ordered assessments via through table 
        battery_tests = ( 
            BatteryAssessment.objects 
            .filter( 
                battery=battery, 
                assessment__is_active=True 
            ) 
            .select_related("assessment") 
            .order_by("display_order") 
        ) 
 
        # Build test payload 
        tests_payload = [] 
        for bt in battery_tests: 
            assessment = bt.assessment 
            questions = assessment.questions_json.get("questions", []) 
 
            tests_payload.append({ 
                "test_code": assessment.test_code, 
                "title": assessment.title, 
                "version": assessment.version, 
                "description": assessment.description, 
                "questions": questions, 
            }) 
 
        # Final response 
        return Response( 
            { 
                "success": True, 
                "data": { 
                    "order_id": order.id, 
                    "battery": { 
                        "battery_code": battery.battery_code, 
                        "name": battery.name, 
                        "version": battery.version, 
                        "screening_label": battery.screening_label, 
                        "signoff_required": battery.signoff_required, 
                    }, 
                    "tests": tests_payload 
                } 
            }, 
            status=status.HTTP_200_OK 
        )