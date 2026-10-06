from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Event, Registration
from .serializers import (EventSerializer, RegistrationInputSerializer,
                          RegistrationSerializer, SignupSerializer)

User = get_user_model()


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"username": user.username, "token": token.key},
                        status=status.HTTP_201_CREATED)


class StaffWritePermissionMixin:
    """Anyone can read; only staff (event organizers) can create/edit/delete."""

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [AllowAny()]
        return [IsAdminUser()]


class EventListCreateView(StaffWritePermissionMixin, generics.ListCreateAPIView):
    serializer_class = EventSerializer

    def get_queryset(self):
        qs = Event.objects.all()
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(title__icontains=search) | qs.filter(location__icontains=search)
        if self.request.query_params.get("upcoming") == "true":
            qs = qs.filter(start_time__gte=timezone.now())
        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EventDetailView(StaffWritePermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class EventRegistrationsView(generics.ListAPIView):
    """Organizer view: who registered for an event."""
    permission_classes = [IsAdminUser]
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return Registration.objects.filter(event_id=self.kwargs["pk"]).select_related("user", "event")


class RegisterForEventView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        form = RegistrationInputSerializer(data=request.data)
        form.is_valid(raise_exception=True)
        data = form.validated_data

        with transaction.atomic():
            event = get_object_or_404(Event.objects.select_for_update(), pk=pk)

            if event.start_time <= timezone.now():
                return Response({"error": "This event has already started."},
                                status=status.HTTP_400_BAD_REQUEST)

            reg = Registration.objects.filter(user=request.user, event=event).first()
            if reg and reg.status == Registration.CONFIRMED:
                return Response({"error": "You are already registered for this event."},
                                status=status.HTTP_409_CONFLICT)

            if event.spots_left <= 0:
                return Response({"error": "This event is full."},
                                status=status.HTTP_409_CONFLICT)

            if reg:  # re-registering after a cancellation
                reg.full_name = data["full_name"]
                reg.phone = data.get("phone", "")
                reg.notes = data.get("notes", "")
                reg.status = Registration.CONFIRMED
                reg.cancelled_at = None
                reg.save()
            else:
                reg = Registration.objects.create(
                    user=request.user, event=event, full_name=data["full_name"],
                    phone=data.get("phone", ""), notes=data.get("notes", ""),
                )
        return Response(RegistrationSerializer(reg).data, status=status.HTTP_201_CREATED)


class MyRegistrationsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        qs = Registration.objects.filter(user=self.request.user).select_related("event", "user")
        st = self.request.query_params.get("status")
        return qs.filter(status=st) if st else qs


class MyRegistrationDetailView(generics.RetrieveDestroyAPIView):
    """GET to view, DELETE to cancel (the record is kept with status=cancelled)."""
    permission_classes = [IsAuthenticated]
    serializer_class = RegistrationSerializer

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related("event", "user")

    def destroy(self, request, *args, **kwargs):
        reg = self.get_object()
        if reg.status == Registration.CANCELLED:
            return Response({"error": "Registration is already cancelled."},
                            status=status.HTTP_400_BAD_REQUEST)
        reg.status = Registration.CANCELLED
        reg.cancelled_at = timezone.now()
        reg.save()
        return Response(RegistrationSerializer(reg).data)
