from django.contrib import admin

from apps.vacancies.models import Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "location_title",
        "region",
        "country",
        "city",
    )

    list_display_links = ("id", "location_title")

    list_editable = (
        "region",
        "country",
        "city",
    )

    list_filter = (
        "region",
        "country",
    )

    search_fields = ("region", "country", "city")

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
                    "region",
                    "country",
                    "city",
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

    @admin.display(description="Full location")
    def location_title(self, obj: Location):
        return str(obj)
