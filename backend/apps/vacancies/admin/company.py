from core.admin_mixins import ShortIdAdminMixin  # Исправлена опечатка в mexins
from django.contrib import admin

from apps.vacancies.models import Company


@admin.register(Company)
class CompanyAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "name",
        "normalized_name",
        "created_at",
    )

    list_display_links = ("short_id",)

    list_editable = (
        "name",
        "normalized_name",
    )

    list_filter = ("created_at",)

    search_fields = ("name", "normalized_name")

    list_per_page = 50
    show_full_result_count = False

    prepopulated_fields = {"normalized_name": ("name",)}

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
                    "name",
                    "normalized_name",
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
