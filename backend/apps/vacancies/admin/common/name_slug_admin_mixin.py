class NameSlugAdminMixin:
    list_display = (
        "id",
        "name",
        "slug",
        "created_at",
    )

    list_display_links = (
        "id",
        "name",
    )

    search_fields = ("name", "slug")

    list_filter = ("created_at",)

    list_per_page = 50
    show_full_result_count = False

    prepopulated_fields = {"slug": ("name",)}

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
                    "slug",
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
