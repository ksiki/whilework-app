from typing import Any, Dict, Optional

from ninja import Schema
from pydantic import Json


class VacancyQuerySchema(Schema):
    filters: Optional[Json[Dict[str, Any]]] = None
    page: int = 1
