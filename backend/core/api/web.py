from apps.vacancies.endpoints import router as vacancies_router
from ninja import NinjaAPI

web_app = NinjaAPI(urls_namespace="web", docs=None)

web_app.add_router("", vacancies_router)
