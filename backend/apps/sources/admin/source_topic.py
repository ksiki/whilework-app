from django.contrib import admin

from apps.sources.models import SourceTopic

from .mixins import ParserAdminMixin


@admin.register(SourceTopic)
class SourceTopicAdmin(ParserAdminMixin, admin.ModelAdmin):
    list_display = (
        "topic_id",
        "source",
        "is_active",
        "error_status_badge",
        "last_parsed_id_short",
    )

    list_editable = ("is_active",)
    list_display_links = ("topic_id",)

    list_filter = (
        "is_active",
        "source__platform",
        "created_at",
    )

    search_fields = (
        "topic_id",
        "name",
        "source__name",
        "source__identifier",
        "last_error_message",
    )

    list_per_page = 50

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "error_count_display",
    )

    fieldsets = (
        (
            "Topic Info",
            {
                "fields": (
                    "is_active",
                    "source",
                    "topic_id",
                    "name",
                )
            },
        ),
        (
            "Parser Condition",
            {
                "fields": ("last_parsed_id",),
                "description": "Auto update. Do not touch",
            },
        ),
        (
            "Errors Monitor",
            {
                "fields": ("error_count_display", "last_error_message"),
                "classes": ("collapse",),
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

    actions = ["reset_errors", "activate_items"]
