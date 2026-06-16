from django.contrib import admin

from apps.system.models import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = (
        "iso",
        "currency_rate",
        "created_at",
        "updated_at",
    )

    list_editable = ("currency_rate",)

    search_fields = ("iso",)

    list_filter = (
        "created_at",
        "updated_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)
