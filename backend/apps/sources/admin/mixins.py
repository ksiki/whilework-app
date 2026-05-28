from django.contrib import admin
from django.db.models import QuerySet
from django.utils.html import format_html

from apps.sources.models import SourceTopic


class ParserAdminMixin:
    """
    For UI elements and actions between Source and SourceTopic
    """

    @admin.display(description="Errors", ordering="error_count")
    def error_status_badge(self, obj):
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
    def last_parsed_id_short(self, obj):
        if obj.last_parsed_id and len(obj.last_parsed_id) > 15:
            return f"{obj.last_parsed_id[:15]}..."
        return obj.last_parsed_id or "—"

    @admin.display(description="Error Counter")
    def error_count_display(self, obj):
        """Duplicate the field for read-only output in the card"""
        return obj.error_count

    @admin.action(description="Reset Error Counter")
    def reset_errors(self, request, queryset: QuerySet):
        updated = queryset.update(error_count=0, last_error_message=None)
        self.message_user(request, f"Error counter reset for {updated} items")

    @admin.action(description="Activate selected items")
    def activate_items(self, request, queryset: QuerySet):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Activated {updated} items")


class SourceTopicInline(admin.TabularInline):
    model = SourceTopic
    extra = 0
    fields = ("topic_id", "is_active", "last_parsed_id", "error_count")
    readonly_fields = ("last_parsed_id", "error_count")
    show_change_link = True
