import json

from django.contrib import admin
from django.db.models import QuerySet
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.html import format_html

from .models import ParserRawMessage


@admin.register(ParserRawMessage)
class ParserRawMessageAdmin(admin.ModelAdmin):
    list_select_related = ("source",)

    list_display = (
        "short_id",
        "source_link",
        "external_msg_id",
        "status_badge",
        "short_raw_text",
        "created_at",
    )

    list_display_links = ("short_id", "external_msg_id")
    list_filter = ("status", "created_at")

    search_fields = ("external_msg_id", "raw_text", "id")

    list_per_page = 50
    show_full_result_count = False

    autocomplete_fields = ("source",)

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "pretty_metadata",
    )

    fieldsets = (
        (
            "Status",
            {"fields": ("status", "id", "source", "external_msg_id")},
        ),
        (
            "Raw Data",
            {
                "fields": ("raw_text", "pretty_metadata"),
            },
        ),
        (
            "System Dates",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    exclude = ("metadata",)

    actions = ["mark_as_pending"]

    @admin.display(description="Источник", ordering="source__name")
    def source_link(self, obj: ParserRawMessage):
        """
        Converts a ForeignKey into a clickable link to the source card
        """
        if not obj.source_id:
            return "—"
        url = reverse("admin:sources_source_change", args=[obj.source_id])
        return format_html('<a href="{}">{}</a>', url, obj.source.name)

    @admin.display(description="Метаданные (JSON)")
    def pretty_metadata(self, obj: ParserRawMessage):
        """
        Format metadata
        """

        if not obj.metadata:
            return "Empty"

        formatted_json = json.dumps(
            obj.metadata,
            indent=4,
            ensure_ascii=False,
        )
        return format_html(
            '<pre style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 13px;">{}</pre>',
            formatted_json,
        )

    @admin.display(description="Message Text")
    def short_raw_text(self, obj: ParserRawMessage):
        return truncatechars(obj.raw_text, 60)

    @admin.display(description="ID")
    def short_id(self, obj: ParserRawMessage):
        return str(obj.id)[:8]

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj: ParserRawMessage):
        colors = {
            "PND": "#6c757d",
            "PRC": "#28a745",
            "FLD": "#dc3545",
        }
        color = colors.get(obj.status, "#000000")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.action(description="Restart validation")
    def mark_as_pending(self, request, queryset: QuerySet):
        updated = queryset.update(status="PND")
        self.message_user(request, f"{updated} messages mark as pending")
