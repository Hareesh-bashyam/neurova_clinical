from django.urls import path
from apps.clinical_ops.api.v1.views import CreatePatient, CreateOrder, ClinicQueue
from apps.clinical_ops.api.v1.public_views import PublicOrderBootstrap
from apps.clinical_ops.api.v1.delivery_views import SetDeliveryAndMarkDelivered
from apps.clinical_ops.api.v1.export_views import ExportOrderJSON
from apps.clinical_ops.api.v1.public_submit_views import PublicOrderSubmit
from apps.clinical_ops.api.v1.report_views import GenerateReportPDF
from apps.clinical_ops.api.v1.report_download_views import StaffDownloadReport, PublicDownloadReport
from apps.clinical_ops.api.v1.signoff_views import OverrideReportSignoff
from apps.clinical_ops.api.v1.consent_views import PublicGetConsent, PublicSubmitConsent
from apps.clinical_ops.api.v1.public_access_code_views import PublicRequestReportCode
from apps.clinical_ops.api.v1.deletion_views import AdminApproveDeletion
from apps.clinical_ops.api.v1.inbox_views import ClinicalInboxView
from apps.clinical_ops.api.v1.clinical_review import ClinicalReviewDetailView
from apps.clinical_ops.api.v1.display_questions import PublicQuestionDisplay


urlpatterns = [
    path("staff/patients/create", CreatePatient.as_view()),
    path("staff/orders/create", CreateOrder.as_view()),
    path("staff/queue", ClinicQueue.as_view()),
    path("public/order", PublicOrderBootstrap.as_view()),
    
    path("staff/order/<int:order_id>/export", ExportOrderJSON.as_view()),
    path("public/order/<str:token>/consent", PublicGetConsent.as_view()),
    path("public/order/<str:token>/consent/submit", PublicSubmitConsent.as_view()),
    path("public/order/<str:token>/questions", PublicQuestionDisplay.as_view()),
    path("public/order/<str:token>/submit", PublicOrderSubmit.as_view()),
    path("staff/reports/generate", GenerateReportPDF.as_view()),
    path("staff/reports/download", StaffDownloadReport.as_view()),

    path("staff/inbox", ClinicalInboxView.as_view()),
    path("staff/order/<int:order_id>/review", ClinicalReviewDetailView.as_view()),

    path("staff/orders/deliver", SetDeliveryAndMarkDelivered.as_view()),
    path("public/order/<str:token>/report.pdf", PublicDownloadReport.as_view()),
    path("staff/reports/signoff/override", OverrideReportSignoff.as_view()),

    path("public/order/<str:token>/report/access-code", PublicRequestReportCode.as_view()),
    path("admin/data-deletion/approve", AdminApproveDeletion.as_view()),
    

]

