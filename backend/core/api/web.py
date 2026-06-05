from apps.accounts.api.endpoints import router as accounts_api_router
from apps.accounts.web.endpoints import router as accounts_web_router
from apps.navbar.endpoints import router as navbar_router
from apps.vacancies.endpoints import router as vacancies_router
from ninja import NinjaAPI

web_app = NinjaAPI(urls_namespace="web", docs=None)

web_app.add_router("", vacancies_router)
web_app.add_router("", accounts_web_router)
web_app.add_router("/navbar/", navbar_router)
web_app.add_router("/api/", accounts_api_router)
web_app.add_exception_handler
