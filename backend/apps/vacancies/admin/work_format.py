from django.contrib import admin

from apps.vacancies.models import WorkFormat

from .common.name_slug_admin_mixin import NameSlugAdminMixin


@admin.register(WorkFormat)
class WorkFormatAdmin(NameSlugAdminMixin, admin.ModelAdmin):
    pass
