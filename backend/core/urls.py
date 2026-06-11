"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path

from .api.internal import internal_api
from .api.web import web_app
from .sitemaps import StaticSitemap, VacancySitemap

sitemaps = {
    "vacancies": VacancySitemap,
    "static": StaticSitemap,
}
urlpatterns = [
    path("admin/", admin.site.urls),
    #
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", web_app.urls),
    path("api/internal/v1/", internal_api.urls),
]

handler404 = "apps.system.endpoints.global_404_handler"
