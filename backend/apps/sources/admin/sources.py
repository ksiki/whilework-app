from django.contrib import admin
from django.utils.html import format_html

from apps.sources.models import Source

from .mixins import ParserAdminMixin, SourceTopicInline


@admin.register(Source)
class SourceAdmin(ParserAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "platform",
        "identifier",
        "is_active",
        "topics_count",
        "error_status_badge",
        "last_parsed_id_short",
        "created_at",
    )

    list_editable = ("is_active",)
    list_display_links = ("name",)

    list_filter = (
        "is_active",
        "platform",
        "created_at",
    )

    search_fields = ("name", "identifier", "last_error_message")
    list_per_page = 50
    show_full_result_count = False

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "error_count_display",
    )

    inlines = [SourceTopicInline]

    fieldsets = (
        (
            "Main Info",
            {
                "fields": (
                    "is_active",
                    "platform",
                    "name",
                    "identifier",
                )
            },
        ),
        (
            "Parser Condition (For Channels Without Topics)",
            {
                "fields": ("last_parsed_id",),
                "description": "Auto update. Used only if this channel has no individual topics",
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

    @admin.display(description="Topics")
    def topics_count(self, obj: Source):
        count = obj.topics.filter(is_active=True).count()
        if count > 0:
            return format_html("<b>{}</b>", count)
        return "—"
