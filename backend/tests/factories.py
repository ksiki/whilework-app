import uuid
from datetime import datetime
from typing import Final

import factory
from apps.accounts.models import User
from apps.sources.models import Source, SourceTopic
from apps.vacancies.models import Company, Contact, Location, Skill, Vacancy
from django.contrib.auth.hashers import make_password
from factory.django import DjangoModelFactory
from faker import Faker

fake = Faker("ru_RU")

UUID_1_ID: Final[uuid.UUID] = uuid.UUID("11111111-1111-1111-a111-111111111111")
UUID_2_ID: Final[uuid.UUID] = uuid.UUID("22222222-2222-2222-a222-222222222222")
UUID_3_ID: Final[uuid.UUID] = uuid.UUID("22232223-2223-2223-a333-222322232223")
UUID_4_ID: Final[uuid.UUID] = uuid.UUID("22242224-2224-2224-a444-222422242224")
UUID_5_ID: Final[uuid.UUID] = uuid.UUID("22252225-2225-2225-a555-222522252225")
UUID_6_ID: Final[uuid.UUID] = uuid.UUID("22262226-2226-2226-a666-222622262226")

INT_1_ID: Final[int] = 1
INT_2_ID: Final[int] = 2
INT_3_ID: Final[int] = 3
INT_4_ID: Final[int] = 4
INT_5_ID: Final[int] = 5


class SourceFactory(DjangoModelFactory):
    class Meta:
        model = Source

    name = factory.Faker("company")
    platform = "TLG"
    identifier = factory.Sequence(lambda n: f"tg_source_{n}")
    is_active = True
    error_count = 0


class SourceTopicFactory(DjangoModelFactory):
    class Meta:
        model = SourceTopic

    source = factory.SubFactory(SourceFactory)
    topic_id = factory.Sequence(lambda n: str(10000 + n))

    is_active = True
    error_count = 0


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Faker("company")
    slug = factory.Sequence(lambda n: f"company-{n}")


class SkillFactory(DjangoModelFactory):
    class Meta:
        model = Skill

    name = factory.Faker("skill")
    slug = factory.Sequence(lambda n: f"skill-{n}")


class LocationFactory(DjangoModelFactory):
    class Meta:
        model = Location

    region = "Europe"
    country = "Czech Republic"
    city = "Prague"


class ContactFactory(DjangoModelFactory):
    class Meta:
        model = Contact

    platform = "TG"
    details = "@example"


class VacancyFactory(DjangoModelFactory):
    class Meta:
        model = Vacancy

    title = factory.Faker("job")
    company = factory.SubFactory(CompanyFactory)
    location = factory.SubFactory(LocationFactory)
    source = factory.SubFactory(SourceFactory)
    published_at = datetime.now()

    @factory.post_generation
    def skills(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        for skill in extracted:
            self.skills.add(skill)


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker("email")
    password = factory.LazyFunction(lambda: make_password("password"))
    available_slots = 0

    @factory.post_generation
    def company_blacklist(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        for company in extracted:
            self.company_blacklist.add(company)
