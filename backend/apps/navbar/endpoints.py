from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from ninja import Router

router = Router(tags=["Navbar"])


@router.get("/faq/", include_in_schema=False)
def faq(request: HttpRequest) -> HttpResponse:
    context = {"is_auth": request.user.is_authenticated}
    return render(request, "faq/index.html", context)
