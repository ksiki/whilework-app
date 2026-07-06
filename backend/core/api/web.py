from apps.accounts.web.endpoints import router as accounts_web_router
from apps.community.web.endpoints import router as community_web_router
from apps.navbar.web.endpoints import router as navbar_web_router
from apps.vacancies.web.endpoints import router as vacancies_web_router
from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

api = NinjaAPI(
    urls_namespace="web",
    docs=None,
    throttle=[AnonRateThrottle("150/m"), AuthRateThrottle("200/m")],
)

api.add_router("", vacancies_web_router)
api.add_router("/user/", accounts_web_router)
api.add_router("/community/", community_web_router)
api.add_router("/navbar/", navbar_web_router)
api.add_exception_handler
