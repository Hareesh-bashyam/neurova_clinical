from django.urls import path
from .views import SessionEventCreateView, SessionConsentCreateView

urlpatterns = [
    path("<int:session_id>/events/", SessionEventCreateView.as_view()),
    path("<int:session_id>/consent/", SessionConsentCreateView.as_view()),
]
