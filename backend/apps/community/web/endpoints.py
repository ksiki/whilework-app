from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from ninja import Router

router = Router(tags=["Community Web"])


@router.get("/", include_in_schema=False)
def community(request: HttpRequest) -> HttpResponse:
    return render(request, "community/index.html")
