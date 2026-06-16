from django.contrib import admin

from apps.community.models import ProductionLog


@admin.register(ProductionLog)
class ProductionLogAdmin(admin.ModelAdmin):
    list_display = (
        "get_type_display_styled",
        "short_description",
        "created_at",
    )
    list_display_links = (
        "get_type_display_styled",
        "short_description",
    )
    list_filter = (
        "type",
        "created_at",
    )
    search_fields = ("description",)
    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(description="Описание")
    def short_description(self, obj):
        limit = 100
        return (
            obj.description[:limit] + "..."
            if len(obj.description) > limit
            else obj.description
        )

    @admin.display(description="Тип", ordering="type")
    def get_type_display_styled(self, obj):
        emoji = {
            ProductionLog.Type.FEAT: "✨",
            ProductionLog.Type.FIX: "🐛",
            ProductionLog.Type.INIT: "🚀",
        }.get(obj.type, "")
        return f"{emoji} {obj.get_type_display()}"
