from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Event, Registration

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class EventSerializer(serializers.ModelSerializer):
    registered_count = serializers.IntegerField(read_only=True)
    spots_left = serializers.IntegerField(read_only=True)

    class Meta:
        model = Event
        fields = ["id", "title", "description", "location", "start_time",
                  "capacity", "registered_count", "spots_left"]


class RegistrationInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)


class RegistrationSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Registration
        fields = ["id", "user", "event", "full_name", "phone", "notes",
                  "status", "created_at", "cancelled_at"]
