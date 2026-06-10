from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin

from apps.vacancies.models import Complaint


@admin.register(Complaint)
class ComplaintAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "vacancy",
        "author",
        "reason",
        "created_at",
    )

    list_filter = (
        "reason",
        "created_at",
    )

    search_fields = (
        "id",
        "vacancy__title",
        "author__email",
        "details",
    )

    list_select_related = (
        "vacancy",
        "author",
    )

    raw_id_fields = (
        "vacancy",
        "author",
    )

    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Main info",
            {
                "fields": (
                    "id",
                    "vacancy",
                    "author",
                )
            },
        ),
        (
            "Details",
            {
                "fields": (
                    "reason",
                    "details",
                )
            },
        ),
        (
            "System info",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
                "classes": ("collapse",),
            },
        ),
    )
