# reports/urls.py
from django.urls import path
from .views import ReportCreateView, ReportSignView, ReportReleaseView

urlpatterns = [
    path(
        "sessions/<int:session_id>/report/",
        ReportCreateView.as_view(),
    ),
    path("reports/<int:report_id>/sign/", ReportSignView.as_view()),
    path("reports/<int:report_id>/release/", ReportReleaseView.as_view()),
]
