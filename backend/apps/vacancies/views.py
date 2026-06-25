import os
import uuid

import cairosvg
from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from . import services
from .models import Vacancy


def generate_vacancy_og_image(request: HttpRequest, id: uuid.UUID) -> None:
    """
    Fallback-вьюха для Nginx.
    Срабатывает только GET-запросом, когда файла еще нет на диске.
    """
    if request.method != "GET":
        return Http404("Method not allowed")

    og_dir = os.path.join(settings.MEDIA_ROOT, "og")
    os.makedirs(og_dir, exist_ok=True)
    file_path = os.path.join(og_dir, f"vacancy_{id}.png")

    if not os.path.exists(file_path):
        vacancy = get_object_or_404(Vacancy, id=id)

        context = services.get_og_context(vacancy)
        svg_content = render_to_string("og_template.svg", context)

        cairosvg.svg2png(bytestring=svg_content.encode("utf-8"), write_to=file_path)

    return FileResponse(open(file_path, "rb"), content_type="image/png")
