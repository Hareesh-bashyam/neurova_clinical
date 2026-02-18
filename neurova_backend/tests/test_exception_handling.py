
import logging
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate
from unittest.mock import patch
from rest_framework import status
from apps.clinical_ops.api.v1.inbox_views import ClinicalInboxView
from apps.clinical_ops.api.v1.views import CreateOrder
from apps.clinical_ops.api.v1.display_questions import PublicQuestionDisplay
from apps.clinical_ops.models import AssessmentOrder
from django.contrib.auth.models import User
from core.models import Organization, UserProfile

# Configure logging to capture output for verification
logging.basicConfig(level=logging.ERROR)

class TestExceptionHandling(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        
        # Create Organization
        self.org = Organization.objects.create(
            name="Test Org",
            code="TEST_ORG",
            org_type="HOSPITAL"
        )
        
        # Create User
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        
        # Create UserProfile
        self.profile = UserProfile.objects.create(
            user=self.user,
            organization=self.org,
            role="STAFF"
        )

    @patch('apps.clinical_ops.api.v1.inbox_views.AssessmentOrder.objects.filter')
    def test_clinical_inbox_view_exception(self, mock_filter):
        """Test that ClinicalInboxView handles exceptions gracefully."""
        # Arrange
        mock_filter.side_effect = Exception("Database error")
        request = self.factory.get('/api/clinical_ops/v1/staff/inbox')
        force_authenticate(request, user=self.user)
        
        view = ClinicalInboxView.as_view()

        # Act
        response = view(request)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['message'], "An unexpected error occurred while fetching the inbox.")

    @patch('apps.clinical_ops.api.v1.views.AssessmentOrder.objects.filter')
    def test_clinic_queue_view_exception(self, mock_filter):
        """Test that ClinicQueue handles exceptions gracefully."""
        # Arrange
        mock_filter.side_effect = Exception("Queue error")
        request = self.factory.get('/api/clinical_ops/v1/staff/queue')
        force_authenticate(request, user=self.user)
        
        from apps.clinical_ops.api.v1.views import ClinicQueue
        view = ClinicQueue.as_view()

        # Act
        response = view(request)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("An unexpected error occurred", response.data['message'])

    @patch('apps.clinical_ops.api.v1.patient_acceptance_views.get_object_or_404')
    def test_patient_accept_reject_order_exception(self, mock_get):
        """Test that PatientAcceptRejectOrder handles exceptions gracefully and accepts order_id."""
        # Arrange
        mock_get.side_effect = Exception("Accept/Reject error")
        request = self.factory.post('/api/clinical_ops/v1/staff/order/123/accept-reject', data={}, format='json')
        force_authenticate(request, user=self.user)
        
        # Mocking decrypted_data as the decorator might fail otherwise or we need to mock it
        request.decrypted_data = {"action": "ACCEPT"} 
        
        # We need to mock the decorators or ensure they don't crash before our try/except.
        # But for the TypeError "unexpected keyword argument 'order_id'", that happens at the call to the decorated function.
        # So just calling it with order_id is enough to verify the signature.
        
        from apps.clinical_ops.api.v1.patient_acceptance_views import PatientAcceptRejectOrder
        view = PatientAcceptRejectOrder.as_view()

        # Act
        # We must pass order_id to the view
        response = view(request, order_id=123)

        # Assert
        # If the TypeError persists, this test will error out (not fail, but error).
        # We expect 500 because we forced an exception in get_object_or_404
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['message'], "Unable to process your request at this time.")

    @patch('apps.clinical_ops.api.v1.display_questions.validate_and_rotate_url_token')
    def test_public_question_display_exception(self, mock_validator):
        """Test that PublicQuestionDisplay handles exceptions gracefully."""
        # Arrange
        mock_validator.side_effect = Exception("Token error")
        request = self.factory.get('/api/clinical_ops/v1/public/order/TESTTOKEN/questions')
        
        view = PublicQuestionDisplay.as_view()

        # Act
        response = view(request, token="TESTTOKEN")

        # Assert
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['message'], "Unable to retrieve questions at this time.")

