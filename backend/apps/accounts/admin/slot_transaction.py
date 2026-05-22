from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.accounts.models import SlotTransaction


@admin.register(SlotTransaction)
class SlotTransactionAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_select_related = ("user",)

    list_display = (
        "short_id",
        "user_link",
        "slots_badge",
        "status_badge",
        "created_at",
    )

    list_display_links = ("short_id",)

    list_filter = (
        "payment_status",
        "created_at",
    )

    search_fields = (
        "id",
        "user__email",
    )

    list_per_page = 50
    show_full_result_count = False

    autocomplete_fields = ("user",)

    readonly_fields = (
        "id",
        "user",
        "slots_added",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Main Info",
            {
                "fields": (
                    "payment_status",
                    "slots_added",
                    "user",
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

    @admin.display(description="User", ordering="user__email")
    def user_link(self, obj: SlotTransaction):
        if not obj.user_id:
            return "—"
        url = reverse("admin:accounts_user_change", args=[obj.user_id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)

    @admin.display(description="Slots", ordering="slots_added")
    def slots_badge(self, obj: SlotTransaction):
        return format_html(
            '<span style="color: #28a745; font-weight: bold;">+{}</span>',
            obj.slots_added,
        )

    @admin.display(description="Status", ordering="payment_status")
    def status_badge(self, obj: SlotTransaction):
        colors = {
            "SCS": "#28a745",
            "PND": "#ffc107",
            "CNC": "#dc3545",
        }
        color = colors.get(obj.payment_status, "#000000")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
            color,
            obj.get_payment_status_display(),
        )

    def has_delete_permission(self, request, obj=None):
        return False
