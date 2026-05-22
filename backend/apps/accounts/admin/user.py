from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin
from django.contrib.auth.hashers import make_password

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "email",
        "available_slots",
        "created_at",
    )

    list_display_links = ("short_id", "email")
    list_editable = ("available_slots",)

    search_fields = ("email", "id")
    list_filter = ("created_at",)

    list_per_page = 50
    show_full_result_count = False

    autocomplete_fields = ("company_blacklist",)

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Main Info",
            {
                "fields": ("email", "password"),
            },
        ),
        (
            "Slots and Restrictions",
            {
                "fields": ("available_slots", "company_blacklist"),
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

    def save_model(self, request, obj, form, change):
        """
        Password hashing on change
        """

        if not change or "password" in form.changed_data:
            obj.password = make_password(obj.password)
        super().save_model(request, obj, form, change)
