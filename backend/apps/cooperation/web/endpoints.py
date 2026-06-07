from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from ninja import Router

router = Router(tags=["Cooperation Web"])


@router.get("/", include_in_schema=False)
def cooperation(request: HttpRequest) -> HttpResponse:
    return render(request, "cooperation/index.html")
