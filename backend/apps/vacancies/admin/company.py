from core.admin_mixins import ShortIdAdminMixin
from django.contrib import admin

from apps.vacancies.models import Company

from .common.name_slug_admin_mixin import NameSlugAdminMixin


@admin.register(Company)
class CompanyAdmin(ShortIdAdminMixin, NameSlugAdminMixin, admin.ModelAdmin):
    list_display = (
        "short_id",
        "name",
        "slug",
        "created_at",
    )

    list_display_links = ("short_id",)

    list_editable = ("name",)
