from django.urls import path
from .views import SessionScoreCreateView

urlpatterns = [
    path(
        "sessions/<int:session_id>/score/",
        SessionScoreCreateView.as_view(),
    ),
]
