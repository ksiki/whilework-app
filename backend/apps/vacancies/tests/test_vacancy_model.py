import pytest
from tests.factories import CompanyFactory, LocationFactory, VacancyFactory


@pytest.mark.parametrize(
    "salary_min, salary_max, expectation",
    [
        (None, 10_000, "10000 USD"),
        (5_000, None, "5000 USD"),
        (5_000, 10_000, "5000–10000 USD"),
        (None, None, ""),
    ],
)
@pytest.mark.django_db
def test_salary_string(
    salary_min: int, salary_max: int, expectation: str | None
) -> None:
    vacancy = VacancyFactory(
        salary_min=salary_min, salary_max=salary_max, currency="USD"
    )
    assert vacancy.salary_string == expectation


@pytest.mark.parametrize(
    "company_data, location_data, expectation",
    [
        (
            {"name": "Apple", "slug": "apple"},
            {"region": "Europe", "country": "Czech Republic", "city": "Prague"},
            "Apple | Europe | Czech Republic | Prague",
        ),
        (
            None,
            {"region": "Europe", "country": "Czech Republic", "city": "Prague"},
            "Europe | Czech Republic | Prague",
        ),
        (
            {"name": "Apple", "slug": "apple"},
            {"region": "Europe", "country": None, "city": "Prague"},
            "Apple | Europe | Prague",
        ),
        (
            None,
            None,
            None,
        ),
    ],
)
@pytest.mark.django_db
def test_meta_string(
    company_data: dict | None, location_data: dict | None, expectation: str | None
) -> None:
    company = CompanyFactory(**company_data) if company_data else None
    location = LocationFactory(**location_data) if location_data else None

    vacancy = VacancyFactory(company=company, location=location)
    assert vacancy.meta_string == expectation
