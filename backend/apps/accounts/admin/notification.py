from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin

from apps.accounts.models import Notification, UserNotification


class UserNotificationInline(admin.TabularInline):
    model = UserNotification
    autocomplete_fields = ("user",)

    extra = 0
    readonly_fields = ("read_at",)
    fields = ("user", "is_read", "read_at")


@admin.register(Notification)
class NotificationAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    inlines = [UserNotificationInline]

    list_display = (
        "short_id",
        "title",
        "created_at",
    )

    list_display_links = ("short_id", "title")
    search_fields = ("title", "message")
    list_filter = ("created_at",)

    list_per_page = 50
    show_full_result_count = False

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Main Info",
            {
                "fields": (
                    "title",
                    "message",
                )
            },
        ),
        (
            "System Data",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
