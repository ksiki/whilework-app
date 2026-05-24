from pytest_factoryboy import register
from tests.factories import (
    CompanyFactory,
    LocationFactory,
    SourceFactory,
    VacancyFactory,
)

register(SourceFactory)
register(CompanyFactory)
register(LocationFactory)
register(VacancyFactory)
