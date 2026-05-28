import json

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from . import services
from .exceptions import UnknownModeError, UnknownSortingError


def vacancies_list(request: HttpRequest) -> HttpResponse:
    vacancies = services.get_active_vacancies()

    filters_json = request.GET.get("filters")
    if filters_json:
        try:
            filters = json.loads(filters_json)
            vacancies = services.apply_filters(queryset=vacancies, params=filters)
        except json.JSONDecodeError:
            pass
        except (UnknownSortingError, UnknownModeError) as e:
            return HttpResponse(
                {"error": "Unknown sorting or mode", "e": f"{e}"},
            )

    page_number = request.GET.get("page", 1)
    page = services.get_page(queryset=vacancies, page_number=page_number)

    context = services.make_context_for_vacancies_list()
    context["vacancies"] = page.object_list
    context["has_next"] = page.has_next()

    template = "vacancies/list.html"
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        template = "vacancies/includes/_job_card.html"
    return render(
        request=request,
        template_name=template,
        context=context,
    )
