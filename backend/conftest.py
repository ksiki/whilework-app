from pytest_factoryboy import register
from tests.factories import (
    CompanyFactory,
    ContactFactory,
    LocationFactory,
    SkillFactory,
    SourceFactory,
    UserFactory,
    VacancyFactory,
)

register(SourceFactory)
register(CompanyFactory)
register(LocationFactory)
register(VacancyFactory)
register(UserFactory)
register(ContactFactory)
register(SkillFactory)
