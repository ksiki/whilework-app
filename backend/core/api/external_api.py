from apps.accounts.api.external import router as accounts_router
from apps.analytics.api.external import router as analytics_router
from apps.community.api.external import router as community_router
from apps.navbar.api.external import router as navbar_router
from apps.system.endpoints import router as system_router
from apps.vacancies.api.external import router as vacancies_router
from ninja import NinjaAPI
from ninja.throttling import AnonRateThrottle, AuthRateThrottle

api = NinjaAPI(
    title="External API",
    urls_namespace="external-api-v1",
    version="v1",
    description="API for external communication",
    docs=None,
    throttle=[AnonRateThrottle("150/m"), AuthRateThrottle("200/m")],
)

api.add_router("/user/", accounts_router)
api.add_router("/navbar/", navbar_router)
api.add_router("/community/", community_router)
api.add_router("/vacancy/", vacancies_router)
api.add_router("/system/", system_router)
api.add_router("/analytics/", analytics_router)
api.add_exception_handler
