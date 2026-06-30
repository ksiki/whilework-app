import uuid

from django.core.paginator import Page
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from ninja import Query, Router

from apps.sources import services as sources_services
from apps.vacancies import services
from apps.vacancies.exceptions import UnknownModeError, UnknownSortingError
from apps.vacancies.models import Vacancy

from .schemas import VacancyQuerySchema

router = Router(tags=["Vacancies Web"])


def _get_filtered_vacancies_page(
    request: HttpRequest, query: VacancyQuerySchema
) -> Page:
    """Хелпер для получения отфильтрованной страницы вакансий."""
    vacancies = services.get_active_vacancies()

    if query.filters:
        blacklist = None
        if request.user.is_authenticated:
            blacklist = request.user.company_blacklist.values_list("id", flat=True)

        vacancies = services.apply_filters(
            queryset=vacancies,
            blacklist_companies=blacklist,
            params=query.filters,
        )

    return services.get_page(queryset=vacancies, page_number=query.page)


@router.get("/", include_in_schema=False)
def vacancies_list(
    request: HttpRequest, query: VacancyQuerySchema = Query(...)
) -> HttpResponse:
    """Отрабатывает при первой загрузке страницы."""
    try:
        page = _get_filtered_vacancies_page(request, query)
    except (UnknownSortingError, UnknownModeError) as e:
        return HttpResponse(f"Bad Request: filtering params error e:{e}", status=400)

    context = services.make_context_for_vacancies_list()
    context.update(
        {
            "sources": sources_services.get_source_types(),
            "vacancies": page.object_list,
            "count_filtered_vacancies": page.paginator.count,
        }
    )

    if request.user.is_authenticated:
        context["viewed_vacancies"] = request.user.viewed_vacancies.values_list(
            "id", flat=True
        )

    return render(request, "vacancies/list.html", context)


@router.get("/cards/", include_in_schema=False)
def vacancies_cards_ajax(
    request: HttpRequest, query: VacancyQuerySchema = Query(...)
) -> HttpResponse:
    """Легковесный эндпоинт для бесконечного скролла и фильтрации (AJAX)."""
    try:
        page = _get_filtered_vacancies_page(request, query)
    except (UnknownSortingError, UnknownModeError) as e:
        return HttpResponse(f"Bad Request: filtering params error e:{e}", status=400)

    if query.page and int(query.page) > page.paginator.num_pages:
        return HttpResponse("")

    context = {
        "vacancies": page.object_list,
        "count_filtered_vacancies": page.paginator.count,
    }

    if request.user.is_authenticated:
        context["viewed_vacancies"] = request.user.viewed_vacancies.values_list(
            "id", flat=True
        )

    return render(request, "vacancies/includes/_job_card.html", context)


@router.get("/detail/{id}/{slug}/", include_in_schema=False)
def vacancy_detail(request: HttpRequest, id: uuid.UUID, slug: str) -> HttpResponse:
    vacancy = get_object_or_404(
        Vacancy.objects.select_related(
            "source", "author", "company", "location"
        ).prefetch_related("contact"),
        id=id,
    )
    services.update_views(vacancy=vacancy)

    is_auth = request.user.is_authenticated
    context = {
        "vacancy": vacancy,
        "is_auth": is_auth,
        "contacts": vacancy.contact.all() if is_auth else [],
        "similar_vacancies": services.get_similar_vacancies(vacancy_id=vacancy.id),
    }

    if vacancy.status != "ACT":
        return render(request, "vacancies/archived.html", context)
    return render(request, "vacancies/detail.html", context)
