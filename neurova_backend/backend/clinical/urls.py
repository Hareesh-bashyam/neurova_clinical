from django.urls import path

from backend.clinical.views import (
    ClinicalOrderCreateView,
    StartSessionView,
    GetCurrentTestView,
    SubmitCurrentTestView,
    GenerateReportView,
    GetClinicalReportPDFView,
    ClinicalOrderStatusUpdateView,
)

urlpatterns = [
    # -------------------------------------------------
    # 6.1 CREATE ORDER
    # -------------------------------------------------
    path(
        "orders/",
        ClinicalOrderCreateView.as_view(),
        name="clinical-order-create",
    ),

    # -------------------------------------------------
    # ORDER STATUS UPDATE
    # -------------------------------------------------
    path(
        "orders/<uuid:order_id>/status/",
        ClinicalOrderStatusUpdateView.as_view(),
        name="clinical-order-status-update",
    ),

    # -------------------------------------------------
    # 6.2 START SESSION
    # -------------------------------------------------
    path(
        "sessions/<uuid:session_id>/start/",
        StartSessionView.as_view(),
        name="clinical-session-start",
    ),

    # -------------------------------------------------
    # 6.3 GET CURRENT TEST
    # -------------------------------------------------
    path(
        "sessions/<uuid:session_id>/current/",
        GetCurrentTestView.as_view(),
        name="clinical-current-test",
    ),

    # -------------------------------------------------
    # 6.4 SUBMIT CURRENT TEST
    # -------------------------------------------------
    path(
        "sessions/<uuid:session_id>/submit_current/",
        SubmitCurrentTestView.as_view(),
        name="clinical-submit-current-test",
    ),

    # -------------------------------------------------
    # 6.5 GENERATE REPORT (FREEZE JSON)
    # -------------------------------------------------
    path(
        "orders/<uuid:order_id>/generate_report/",
        GenerateReportView.as_view(),
        name="clinical-generate-report",
    ),

    # -------------------------------------------------
    # 6.6 GET REPORT PDF (READ-ONLY, NO RECOMPUTE)
    # -------------------------------------------------
    path(
        "orders/<uuid:order_id>/report/pdf/",
        GetClinicalReportPDFView.as_view(),
        name="clinical-report-pdf",
    ),
]
