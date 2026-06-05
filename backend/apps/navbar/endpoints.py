from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from ninja import Router

router = Router(tags=["Accounts Web"])


@router.get("/faq/", include_in_schema=False)
def faq(request: HttpRequest) -> HttpResponse:
    return render(request, "faq/index.html")


@router.get("/cooperation/", include_in_schema=False)
def cooperation(request: HttpRequest) -> HttpResponse:
    return render(request, "cooperation/index.html")
