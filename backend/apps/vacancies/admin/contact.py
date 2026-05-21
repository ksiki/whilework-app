from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin
from django.utils.html import format_html

from apps.vacancies.models import Contact


@admin.register(Contact)
class ContactAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "platform",
        "clickable_details",
        "created_at",
    )

    list_editable = ("platform",)

    list_display_links = ("short_id",)

    list_filter = (
        "platform",
        "created_at",
    )

    search_fields = ("details",)

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
                    "platform",
                    "details",
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

    @admin.display(description="Contact link", ordering="details")
    def clickable_details(self, obj: Contact):
        """
        Turns a contact into a clickable link, depending on the platform.
        Opens in a new tab (target="_blank").
        """
        if not obj.details:
            return "—"

        if obj.platform == Contact.Platform.TELEGRAM:
            clean_tg = obj.details.lstrip("@")
            url = f"https://t.me/{clean_tg}"
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.details)

        elif obj.platform == Contact.Platform.EMAIL:
            url = f"mailto:{obj.details}"
            return format_html('<a href="{}">{}</a>', url, obj.details)

        return obj.details
