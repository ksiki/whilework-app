from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin

from apps.community.models import Suggest


@admin.register(Suggest)
class SuggestAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "title",
        "status",
        "likes",
        "author",
        "created_at",
    )

    list_display_links = (
        "short_id",
        "title",
    )

    list_editable = ("status",)

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "title",
        "description",
        "author__username",
        "author__email",
    )

    raw_id_fields = ("author", "liked_by")

    readonly_fields = ("id", "created_at", "updated_at")

    fieldsets = (
        ("Main info", {"fields": ("id", "title", "description", "author")}),
        ("Moderation and Metrics", {"fields": ("status", "likes", "liked_by")}),
        (
            "System info",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    actions = ["mark_as_planned", "mark_as_archived"]

    @admin.action(description="Change status to: Planned")
    def mark_as_planned(self, request, queryset):
        updated = queryset.update(status=Suggest.Status.PLANNED)
        self.message_user(request, f"Suggest update: {updated}")

    @admin.action(description="Change status to: Archive")
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(status=Suggest.Status.ARCHIVED)
        self.message_user(request, f"Move to archive: {updated}")
