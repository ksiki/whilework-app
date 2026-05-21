from django.contrib import admin

from apps.vacancies.models import Skill

from .common.name_slug_admin_mixin import NameSlugAdminMixin


@admin.register(Skill)
class SkillAdmin(NameSlugAdminMixin, admin.ModelAdmin):
    pass
