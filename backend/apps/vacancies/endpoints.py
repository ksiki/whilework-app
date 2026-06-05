from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from ninja import Query, Router

from apps.sources import services as sources_services

from . import services
from .exceptions import UnknownModeError, UnknownSortingError
from .schemas import VacancyQuerySchema

router = Router(tags=["Web Vacancies"])


@router.get("/", include_in_schema=False)
def vacancies_list(
    request: HttpRequest, query: VacancyQuerySchema = Query(...)
) -> HttpResponse:
    vacancies = services.get_active_vacancies()

    if query.filters:
        try:
            vacancies = services.apply_filters(queryset=vacancies, params=query.filters)
        except (UnknownSortingError, UnknownModeError) as e:
            return HttpResponse(
                f"Bad Request: filtering params error e:{e}", status=400
            )

    page = services.get_page(queryset=vacancies, page_number=query.page)

    context = services.make_context_for_vacancies_list()
    context["sources"] = sources_services.get_source_types()
    context["vacancies"] = page.object_list
    context["has_next"] = page.has_next()

    template = "vacancies/list.html"
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        template = "vacancies/includes/_job_card.html"

    return render(request, template, context)
