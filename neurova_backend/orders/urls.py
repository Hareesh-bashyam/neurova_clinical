# orders/urls.py
from django.urls import path
from .views import OrderCreateView, StartSessionView

urlpatterns = [
    path("orders/", OrderCreateView.as_view()),
    path("orders/<int:order_id>/start-session/", StartSessionView.as_view()),
]
