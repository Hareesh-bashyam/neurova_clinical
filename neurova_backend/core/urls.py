from django.urls import path
from .views import OrganizationCreateView, UserCreateView

urlpatterns = [
    path("orgs/", OrganizationCreateView.as_view()),
    path("users/", UserCreateView.as_view()),
]
