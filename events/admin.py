from django.contrib import admin

from .models import Event, Registration


class RegistrationInline(admin.TabularInline):
    model = Registration
    extra = 0
    readonly_fields = ("created_at", "cancelled_at")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "location", "start_time", "capacity", "registered_count", "spots_left")
    search_fields = ("title", "location")
    list_filter = ("start_time",)
    inlines = [RegistrationInline]

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "event", "status", "created_at")
    list_filter = ("status", "event")
    search_fields = ("full_name", "user__username", "event__title")
