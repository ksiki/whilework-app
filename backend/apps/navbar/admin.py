from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin

from .models import SupportMessage


@admin.register(SupportMessage)
class SupportMessageAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "title",
        "author",
        "created_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "id",
        "title",
        "message",
        "author__email",
        "author__username",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    raw_id_fields = ("author",)

    date_hierarchy = "created_at"

    fieldsets = (
        ("Main info", {"fields": ("id", "author", "title", "message")}),
        (
            "System info",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
