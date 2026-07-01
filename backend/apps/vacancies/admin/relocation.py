from django.contrib import admin

from apps.vacancies.models import Relocation


@admin.register(Relocation)
class RelocationAdmin(admin.ModelAdmin):
    list_display = ("id", "country", "created_at", "updated_at")

    list_display_links = ("id", "country")

    search_fields = ("country",)

    list_filter = ("created_at", "updated_at")

    readonly_fields = ("id", "created_at", "updated_at")

    empty_value_display = "- Не указано -"

    fieldsets = (
        (
            "Main Info",
            {
                "fields": ("id", "country"),
                "description": "Базовая информация о стране для релокации.",
            },
        ),
        (
            "System Info",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )
