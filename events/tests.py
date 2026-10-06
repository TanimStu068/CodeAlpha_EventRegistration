from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Event, Registration

User = get_user_model()
FORM = {"full_name": "Test User", "phone": "123"}


class EventApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("alice", password="pass12345")
        self.other = User.objects.create_user("bob", password="pass12345")
        self.staff = User.objects.create_user("admin", password="pass12345", is_staff=True)
        self.event = Event.objects.create(
            title="Meetup", location="Online", capacity=1,
            start_time=timezone.now() + timedelta(days=3),
        )

    def test_signup_and_login(self):
        r = self.client.post("/api/auth/signup/", {"username": "new", "password": "longpass123"})
        self.assertEqual(r.status_code, 201)
        self.assertIn("token", r.json())
        r = self.client.post("/api/auth/login/", {"username": "new", "password": "longpass123"})
        self.assertEqual(r.status_code, 200)

    def test_public_event_list_and_detail(self):
        r = self.client.get("/api/events/")
        self.assertEqual(r.json()["count"], 1)
        r = self.client.get(f"/api/events/{self.event.id}/")
        self.assertEqual(r.json()["spots_left"], 1)

    def test_register_requires_login(self):
        r = self.client.post(f"/api/events/{self.event.id}/register/", FORM)
        self.assertEqual(r.status_code, 401)

    def test_register_and_duplicate(self):
        self.client.force_authenticate(self.user)
        r = self.client.post(f"/api/events/{self.event.id}/register/", FORM)
        self.assertEqual(r.status_code, 201)
        r = self.client.post(f"/api/events/{self.event.id}/register/", FORM)
        self.assertEqual(r.status_code, 409)

    def test_capacity_enforced(self):
        self.client.force_authenticate(self.user)
        self.client.post(f"/api/events/{self.event.id}/register/", FORM)
        self.client.force_authenticate(self.other)
        r = self.client.post(f"/api/events/{self.event.id}/register/", FORM)
        self.assertEqual(r.status_code, 409)
        self.assertIn("full", r.json()["error"])

    def test_cancel_frees_spot_and_allows_reregister(self):
        self.client.force_authenticate(self.user)
        reg_id = self.client.post(f"/api/events/{self.event.id}/register/", FORM).json()["id"]
        r = self.client.delete(f"/api/registrations/{reg_id}/")
        self.assertEqual(r.json()["status"], "cancelled")
        self.assertEqual(self.event.spots_left, 1)
        r = self.client.post(f"/api/events/{self.event.id}/register/", FORM)
        self.assertEqual(r.status_code, 201)

    def test_cannot_touch_other_users_registration(self):
        reg = Registration.objects.create(user=self.other, event=self.event, full_name="Bob")
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(f"/api/registrations/{reg.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/registrations/{reg.id}/").status_code, 404)

    def test_my_registrations_only_lists_own(self):
        Registration.objects.create(user=self.other, event=self.event, full_name="Bob")
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get("/api/registrations/").json()["count"], 0)

    def test_past_event_rejected(self):
        past = Event.objects.create(title="Old", location="X",
                                    start_time=timezone.now() - timedelta(days=1))
        self.client.force_authenticate(self.user)
        r = self.client.post(f"/api/events/{past.id}/register/", FORM)
        self.assertEqual(r.status_code, 400)

    def test_only_staff_can_create_events(self):
        body = {"title": "New", "location": "HQ", "capacity": 10,
                "start_time": (timezone.now() + timedelta(days=5)).isoformat()}
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post("/api/events/", body).status_code, 403)
        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.post("/api/events/", body).status_code, 201)

    def test_organizer_sees_attendees(self):
        Registration.objects.create(user=self.user, event=self.event, full_name="Alice")
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(f"/api/events/{self.event.id}/registrations/").status_code, 403)
        self.client.force_authenticate(self.staff)
        r = self.client.get(f"/api/events/{self.event.id}/registrations/")
        self.assertEqual(r.json()["count"], 1)
