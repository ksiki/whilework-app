from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from ninja import Router
from ninja.security import django_auth

from apps.accounts import services
from apps.vacancies import services as vacancies_services

router = Router(tags=["Accounts Web"])


@router.get("/login/", include_in_schema=False)
def login_register_page(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("/profile/")

    return render(request, "auth/login_register.html")


@router.get("/profile/", auth=django_auth, include_in_schema=False)
def profile(request: HttpRequest) -> HttpResponse:
    context = services.get_profile_data(email=request.user.email)
    context["vacancies_created"] = list(
        vacancies_services.vacancies_by_owner(owner_id=context["user_id"])
    )
    return render(request, "profile/detail.html", context)
