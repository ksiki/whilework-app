from django.contrib import admin

from .models import Report404


@admin.register(Report404)
class Report404Admin(admin.ModelAdmin):
    list_display = (
        "id",
        "url",
        "created_at",
    )

    list_filter = ("created_at",)

    search_fields = ("url",)

    readonly_fields = (
        "url",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Main info",
            {"fields": ("url",)},
        ),
        (
            "System info",
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
