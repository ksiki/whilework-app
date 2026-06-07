from apps.accounts.api.endpoints import router as accounts_api_router
from apps.accounts.web.endpoints import router as accounts_web_router
from apps.cooperation.api.endpoints import router as cooperation_api_router
from apps.cooperation.web.endpoints import router as cooperation_web_router
from apps.navbar.endpoints import router as navbar_router
from apps.vacancies.endpoints import router as vacancies_router
from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

web_app = NinjaAPI(
    urls_namespace="web",
    docs=None,
    throttle=[AnonRateThrottle("10/m"), AuthRateThrottle("100/m")],
)

web_app.add_router("", vacancies_router)
web_app.add_router("", accounts_web_router)
web_app.add_router("/cooperation/", cooperation_web_router)
web_app.add_router("/navbar/", navbar_router)
web_app.add_router("/api/", accounts_api_router)
web_app.add_router("/api/", cooperation_api_router)
web_app.add_exception_handler
