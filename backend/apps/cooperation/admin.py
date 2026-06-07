from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "email",
        "name",
        "created_at",
    )
    list_filter = ("created_at",)

    search_fields = ("email", "name", "text")

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Contact data", {"fields": ("name", "email")}),
        ("Content", {"fields": ("text",)}),
        (
            "System info",
            {
                "fields": ("id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    show_full_result_count = False
