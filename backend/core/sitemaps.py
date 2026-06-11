from apps.vacancies.services import get_active_vacancies
from django.contrib.sitemaps import Sitemap


class VacancySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8

    def items(self):
        return get_active_vacancies()

    def lastmod(self, obj):
        return obj.updated_at


class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return [
            "/",
            "/cooperation/",
            "/navbar/help/",
        ]

    def location(self, item):
        return item
