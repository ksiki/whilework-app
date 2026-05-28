from django.contrib import admin
from django.db.models import QuerySet
from django.utils.html import format_html

from .models import Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "platform",
        "identifier",
        "topic_id",
        "is_active",
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

    fieldsets = (
        (
            "Main Info",
            {
                "fields": (
                    "is_active",
                    "platform",
                    "name",
                    "identifier",
                    "topic_id",
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

    actions = ["reset_errors", "activate_sources"]

    @admin.display(description="Errors", ordering="error_count")
    def error_status_badge(self, obj: Source):
        """Displays a red badge if there are errors and a green badge if everything is OK"""
        if obj.error_count > 0:
            return format_html(
                '<span style="color: white; background-color: #dc3545; padding: 3px 8px; border-radius: 12px; font-weight: bold;">{}</span>',
                obj.error_count,
            )
        return format_html(
            '<span style="color: white; background-color: #28a745; padding: 3px 8px; border-radius: 12px;">{}</span>',
            "OK",
        )

    @admin.display(description="Last Parsed", ordering="last_parsed_id")
    def last_parsed_id_short(self, obj: Source):
        """Shortens the ID"""
        if obj.last_parsed_id and len(obj.last_parsed_id) > 15:
            return f"{obj.last_parsed_id[:15]}..."
        return obj.last_parsed_id or "—"

    @admin.display(description="Error Counter")
    def error_count_display(self, obj: Source):
        """Duplicate the field for read-only output in the card"""
        return obj.error_count

    @admin.action(description="Reset Error Counter")
    def reset_errors(self, request, queryset: QuerySet):
        updated = queryset.update(error_count=0, last_error_message=None)
        self.message_user(request, f"Error counter reset for {updated} sources")

    @admin.action(description="Activtae select sources")
    def activate_sources(self, request, queryset: QuerySet):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} sources")
