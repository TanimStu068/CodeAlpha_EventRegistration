from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path("auth/signup/", views.SignupView.as_view()),
    path("auth/login/", obtain_auth_token),

    path("events/", views.EventListCreateView.as_view()),
    path("events/<int:pk>/", views.EventDetailView.as_view()),
    path("events/<int:pk>/register/", views.RegisterForEventView.as_view()),
    path("events/<int:pk>/registrations/", views.EventRegistrationsView.as_view()),

    path("registrations/", views.MyRegistrationsView.as_view()),
    path("registrations/<int:pk>/", views.MyRegistrationDetailView.as_view()),
]
