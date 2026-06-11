import hashlib
import os
import random
from datetime import timedelta

# 1. Инициализация Django
# Укажи правильный путь к твоим настройкам, если он отличается от core.settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()

# Импорты твоих моделей (предполагаются названия приложений: accounts, sources, vacancies)
from apps.accounts.models import User
from apps.sources.models import Source, SourceTopic
from apps.vacancies.models import Company, Contact, Location, Skill, Vacancy
from django.utils import timezone
from faker import Faker

fake = Faker("ru_RU")

# Списки для реалистичных IT-данных
IT_SKILLS = [
    "Python",
    "Django",
    "FastAPI",
    "PostgreSQL",
    "Redis",
    "Docker",
    "Apache Airflow",
    "Celery",
    "Taskiq",
    "Git",
]
CITIES = ["Минск", "Москва", "Санкт-Петербург", "Алматы", "Астана", "Тбилиси", "Ереван"]
REGIONS = ["СНГ", "Europe", "Asia"]
COUNTRIES = ["Беларусь", "Россия", "Казахстан", "Грузия", "Армения"]


def generate_users(n=10):
    print(f"Создание {n} пользователей...")
    users = []
    for _ in range(n):
        email = fake.unique.email()
        user = User.objects.create_user(
            email=email,
            password="testpassword123",
            is_active=True,
            available_slots=random.randint(0, 5),
        )
        users.append(user)
    return users


def generate_sources(n=5):
    print(f"Создание {n} источников и топиков...")
    sources = []
    for _ in range(n):
        source = Source.objects.create(
            platform=random.choice(Source.Platform.values),
            name=fake.company(),
            identifier=str(fake.unique.random_number(digits=10)),
            is_active=True,
        )
        sources.append(source)

        # Создаем 1-3 топика для каждого источника
        for _ in range(random.randint(1, 3)):
            SourceTopic.objects.create(
                source=source,
                topic_id=str(fake.unique.random_number(digits=8)),
                is_active=True,
            )
    return sources


def generate_dependencies():
    print("Создание компаний, локаций, скиллов и контактов...")
    companies = [Company.objects.create(name=fake.company()) for _ in range(15)]

    locations = [
        Location.objects.create(
            region=random.choice(REGIONS),
            country=random.choice(COUNTRIES),
            city=random.choice(CITIES),
        )
        for _ in range(10)
    ]

    skills = [Skill.objects.create(name=skill) for skill in IT_SKILLS]

    contacts = [
        Contact.objects.create(
            platform=random.choice(Contact.Platform.values),
            details=f"@{fake.user_name()}"
            if random.choice([True, False])
            else fake.email(),
        )
        for _ in range(20)
    ]

    return companies, locations, skills, contacts


def generate_vacancies(
    n=30,
    users=None,
    sources=None,
    companies=None,
    locations=None,
    skills=None,
    contacts=None,
):
    print(f"Создание {n} вакансий...")

    for _ in range(n):
        salary_min = random.randint(500, 3000)
        salary_max = salary_min + random.randint(500, 2000)
        content_raw = fake.text(max_nb_chars=500)

        vacancy = Vacancy.objects.create(
            source=random.choice(sources) if sources else None,
            author=random.choice(users) if users else None,
            company=random.choice(companies) if companies else None,
            location=random.choice(locations) if locations else None,
            title=f"{random.choice(['Backend', 'Frontend', 'Data Engineer', 'DevOps'])} Developer",
            description=content_raw,
            salary_min=salary_min,
            usd_salary_min=salary_min,
            salary_max=salary_max,
            currency="USD",
            status=random.choice(Vacancy.Status.values),
            grade=random.choice(Vacancy.Grade.values),
            experience_from=random.randint(1, 6),
            employment_type=random.choice(Vacancy.EmploymentType.values),
            english_level=random.choice(Vacancy.EnglishLevel.values),
            work_format=random.choice(Vacancy.WorkFormat.values),
            content_hash=hashlib.sha256(content_raw.encode()).hexdigest(),
            published_at=timezone.now() - timedelta(days=random.randint(0, 30)),
        )

        # Добавляем M2M связи (скиллы и контакты)
        vacancy.skills.add(*random.sample(skills, random.randint(2, 5)))
        vacancy.contact.add(*random.sample(contacts, random.randint(1, 2)))


def main():
    print("Начинаем заполнение базы данных тестовыми данными...")

    users = generate_users(10)
    sources = generate_sources(5)
    companies, locations, skills, contacts = generate_dependencies()

    generate_vacancies(
        n=50,
        users=users,
        sources=sources,
        companies=companies,
        locations=locations,
        skills=skills,
        contacts=contacts,
    )

    print("Готово! База данных успешно заполнена.")


if __name__ == "__main__":
    main()
