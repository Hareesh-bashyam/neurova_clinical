# reports/urls.py
from django.urls import path
from .views import ReportCreateView, ReportSignView, ReportReleaseView, ReportPDFView, MarkReportReviewedView, CreateReportCorrectionView

urlpatterns = [
    path(
        "sessions/<int:session_id>/report/",
        ReportCreateView.as_view(),
    ),
    path("reports/<int:report_id>/sign/", ReportSignView.as_view()),
    path("reports/<int:report_id>/release/", ReportReleaseView.as_view()),
    path("reports/<int:report_id>/pdf/", ReportPDFView.as_view()),
    path("reports/<int:report_id>/mark-reviewed/", MarkReportReviewedView.as_view()),
    path("reports/<int:report_id>/create-correction/", CreateReportCorrectionView.as_view()),
]
