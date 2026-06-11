from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "email",
        "is_active",
        "is_staff",
        "available_slots",
        "created_at",
    )

    list_display_links = ("short_id", "email")
    list_editable = ("available_slots",)

    search_fields = ("email", "id")
    list_filter = ("is_active", "is_staff", "is_superuser", "created_at")

    list_per_page = 50
    show_full_result_count = False

    autocomplete_fields = ("company_blacklist", "viewed_vacancies")

    autocomplete_fields = ("company_blacklist",)

    filter_horizontal = ("groups", "user_permissions")

    readonly_fields = (
        "id",
        "last_login",
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
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Slots and Restrictions",
            {
                "fields": ("available_slots", "company_blacklist"),
            },
        ),
        (
            "User Activity",
            {
                "fields": ("viewed_vacancies",),
            },
        ),
        (
            "System Data",
            {
                "fields": ("id", "last_login", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not change or "password" in form.changed_data:
            obj.set_password(obj.password)

        super().save_model(request, obj, form, change)
