from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from apps.vacancies.models import Vacancy


@admin.register(Vacancy)
class VacancyAdmin(ShortIdAdminMixin, admin.ModelAdmin):
    list_select_related = ("company", "location")

    list_display = (
        "short_id",
        "title",
        "company_link",
        "salary_display",
        "grade",
        "experience_from",
        "status_badge",
        "status",
        "published_at",
    )

    list_display_links = ("short_id", "title")
    list_editable = ("status",)

    list_filter = (
        "status",
        "grade",
        "experience_from",
        "employment_type",
        "english_level",
        "published_at",
    )

    search_fields = (
        "title",
        "company__name",
        "content_hash",
    )

    list_per_page = 50
    show_full_result_count = False

    autocomplete_fields = (
        "company",
        "location",
        "source",
        "author",
        "skills",
        "contact",
    )

    readonly_fields = (
        "id",
        "content_hash",
        "views_count",
        "contacts_opened_count",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Main Info",
            {
                "fields": (
                    "status",
                    "title",
                    "company",
                    "description",
                )
            },
        ),
        (
            "Requirements and Conditions",
            {
                "fields": (
                    (
                        "grade",
                        "experience_from",
                        "work_format",
                        "employment_type",
                        "english_level",
                    ),
                    "skills",
                )
            },
        ),
        (
            "Finance",
            {
                "fields": (
                    ("salary_min", "salary_max", "currency"),
                    "usd_salary_min",
                )
            },
        ),
        (
            "Location and Contacts",
            {"fields": ("location", "contact")},
        ),
        (
            "Metrics",
            {
                "fields": (("views_count", "contacts_opened_count"),),
                "classes": ("collapse",),
            },
        ),
        (
            "System Data",
            {
                "fields": (
                    "id",
                    ("source", "author"),
                    "content_hash",
                    ("published_at", "created_at", "updated_at"),
                ),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Salary", ordering="usd_salary_min")
    def salary_display(self, obj: Vacancy):
        if not obj.salary_min and not obj.salary_max:
            return "Not specified"

        curr = obj.currency or ""

        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min:,} - {obj.salary_max:,} {curr}".replace(",", " ")
        elif obj.salary_min:
            return f"From {obj.salary_min:,} {curr}".replace(",", " ")
        elif obj.salary_max:
            return f"To {obj.salary_max:,} {curr}".replace(",", " ")

    @admin.display(description="Company", ordering="company__name")
    def company_link(self, obj: Vacancy):
        if not obj.company_id:
            return "—"
        url = reverse("admin:vacancies_company_change", args=[obj.company_id])
        return format_html('<a href="{}">{}</a>', url, obj.company.name)

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj: Vacancy):
        colors = {
            "ACT": "#28a745",
            "CLS": "#ffc107",
            "ARC": "#6c757d",
        }
        color = colors.get(obj.status, "#000000")
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 12px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display(),
        )
