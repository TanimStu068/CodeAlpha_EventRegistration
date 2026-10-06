from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event


class Command(BaseCommand):
    help = "Create a few sample events for testing."

    def handle(self, *args, **options):
        now = timezone.now()
        samples = [
            ("Intro to Backend Development", "Hands-on APIs workshop.", "Online", 7, 100),
            ("Django Meetup", "Talks and networking for Django developers.", "Chattogram", 14, 30),
            ("Hackathon 2026", "24-hour build challenge.", "Dhaka", 30, 5),
        ]
        for title, desc, loc, days, cap in samples:
            Event.objects.get_or_create(
                title=title,
                defaults=dict(description=desc, location=loc, capacity=cap,
                              start_time=now + timedelta(days=days)),
            )
        self.stdout.write(self.style.SUCCESS("Sample events created."))
