import os
import random
import sys

import django
from faker import Faker

# Настройка окружения Django для запуска скрипта из папки scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "core.settings"
)  # Уточни, если настройки называются иначе
django.setup()

# Импорты моделей (пути зависят от того, как зарегистрированы аппы, предполагаю стандартный импорт)
from apps.accounts.models import Notification, SlotTransaction, User
from apps.community.models import ProductionLog, Suggest
from apps.inbox.models import ParserRawMessage
from apps.navbar.models import SupportMessage
from apps.sources.models import Source, SourceTopic
from apps.system.models import Report404
from apps.vacancies.models import Company, Complaint, Contact, Location, Skill, Vacancy

fake = Faker(["ru_RU", "en_US"])

# Константы для количества генерируемых данных
USERS_COUNT = 20
COMPANIES_COUNT = 15
LOCATIONS_COUNT = 10
SKILLS_COUNT = 30
VACANCIES_COUNT = 50


def clear_old_data():
    print("Очистка старых данных...")
    # Удаляем в правильном порядке, чтобы избежать конфликтов внешних ключей,
    # хотя CASCADE в большинстве случаев сделает это за нас.
    Complaint.objects.all().delete()
    Suggest.objects.all().delete()
    ParserRawMessage.objects.all().delete()
    Vacancy.objects.all().delete()
    SourceTopic.objects.all().delete()
    Source.objects.all().delete()
    Company.objects.all().delete()
    Location.objects.all().delete()
    Skill.objects.all().delete()
    Contact.objects.all().delete()
    User.objects.all().delete()
    print("База данных очищена.\n")


def generate_users():
    print("Генерация пользователей...")
    users = []
    # Создаем суперюзера для удобства
    if not User.objects.filter(email="admin@whilework.local").exists():
        admin = User.objects.create_superuser("admin@whilework.local", "adminpass")
        users.append(admin)

    for _ in range(USERS_COUNT):
        user = User.objects.create_user(
            email=fake.unique.email(),
            password="password123",
            is_active=True,
            available_slots=random.randint(0, 5),
        )
        users.append(user)
    return users


def generate_base_entities():
    print("Генерация базовых сущностей (Компании, Локации, Навыки, Контакты)...")

    companies = [Company(name=fake.company()) for _ in range(COMPANIES_COUNT)]
    for c in companies:
        c.save()  # save() для вызова генерации slug

    locations = [
        Location.objects.create(
            region=random.choice(["CIS", "Europe", "Asia", "North America"]),
            country=fake.country(),
            city=fake.city(),
        )
        for _ in range(LOCATIONS_COUNT)
    ]

    skills = [
        Skill(name=skill_name)
        for skill_name in [
            "Python",
            "Django",
            "FastAPI",
            "Airflow",
            "Docker",
            "PostgreSQL",
            "Celery",
            "Redis",
            "Linux",
            "Nginx",
            "React",
            "Vue",
            "Go",
            "AWS",
            "CI/CD",
        ]
    ]
    for s in skills:
        s.save()  # save() для вызова генерации slug

    contacts = [
        Contact.objects.create(
            platform=random.choice(Contact.Platform.values),
            details=fake.user_name() if random.choice([True, False]) else fake.email(),
        )
        for _ in range(30)
    ]

    return companies, locations, skills, contacts


def generate_sources():
    print("Генерация источников (Sources)...")
    sources = []
    for _ in range(5):
        source = Source.objects.create(
            platform=random.choice(Source.Platform.values),
            name=fake.word().capitalize() + " Jobs",
            identifier=fake.unique.bothify(text="id_########"),
            is_active=True,
        )
        sources.append(source)

        # Генерируем топики для источника
        for _ in range(random.randint(1, 3)):
            SourceTopic.objects.create(
                source=source, topic_id=fake.unique.bothify(text="topic_####")
            )
    return sources


def generate_vacancies(users, companies, locations, skills, contacts, sources):
    print("Генерация вакансий и сырых сообщений парсера...")
    vacancies = []

    for _ in range(VACANCIES_COUNT):
        source = random.choice(sources)
        salary_min = random.randint(500, 3000)

        vacancy = Vacancy(
            source=source,
            author=random.choice(users),
            company=random.choice(companies),
            location=random.choice(locations),
            title=fake.job(),
            description=f"<p>{fake.text(max_nb_chars=500)}</p><ul><li>Обязанность 1</li><li>Обязанность 2</li></ul>",
            salary_min=salary_min,
            usd_salary_min=salary_min,
            salary_max=salary_min + random.randint(500, 2000),
            currency=random.choice(["USD", "EUR", "RUB"]),
            status=random.choice(Vacancy.Status.values),
            grade=random.choice(Vacancy.Grade.values),
            experience_from=random.randint(0, 5),
            employment_type=random.choice(Vacancy.EmploymentType.values),
            english_level=random.choice(Vacancy.EnglishLevel.values),
            work_format=random.choice(Vacancy.WorkFormat.values),
            views_count=random.randint(0, 1000),
            contacts_opened_count=random.randint(0, 100),
            content_hash=fake.unique.sha256(),
            published_at=fake.date_time_between(
                start_date="-30d",
                end_date="now",
                tzinfo=django.utils.timezone.get_current_timezone(),
            ),
        )
        vacancy.save()  # Отработает nh3.clean

        # Добавляем M2M связи
        vacancy.skills.set(random.sample(skills, k=random.randint(2, 6)))
        vacancy.contact.set(random.sample(contacts, k=random.randint(1, 2)))
        vacancies.append(vacancy)

        # Создаем сырое сообщение парсера для этой вакансии
        ParserRawMessage.objects.create(
            source=source,
            topic=source.topics.first() if source.topics.exists() else None,
            external_msg_id=fake.unique.bothify(text="msg_#######"),
            raw_text=fake.text(),
            status=ParserRawMessage.Status.PROCESSED,
        )

    return vacancies


def generate_activity(users, vacancies):
    print(
        "Генерация пользовательской активности (Жалобы, Предложения, Логи, Транзакции)..."
    )

    # Жалобы
    for _ in range(10):
        Complaint.objects.create(
            vacancy=random.choice(vacancies),
            author=random.choice(users),
            reason=random.choice(Complaint.Reason.values),
            details=fake.sentence(),
        )

    # Предложения (Suggests)
    for _ in range(5):
        Suggest.objects.create(
            author=random.choice(users),
            status=random.choice(Suggest.Status.values),
            title=fake.catch_phrase(),
            description=fake.text(),
            likes=random.randint(0, 50),
        )

    # Логи продакшена
    for _ in range(3):
        ProductionLog.objects.create(
            type=random.choice(ProductionLog.Type.values), description=fake.sentence()
        )

    # Обращения в поддержку
    for _ in range(5):
        SupportMessage.objects.create(
            author=random.choice(users),
            title=fake.sentence(nb_words=4),
            message=fake.text(),
        )

    # Транзакции слотов
    for _ in range(8):
        SlotTransaction.objects.create(
            user=random.choice(users),
            slots_added=random.randint(1, 10),
            payment_status=random.choice(SlotTransaction.PaymentStatus.values),
        )

    # Уведомления
    notification = Notification.objects.create(
        title="Системное обновление", message="Мы обновили функционал агрегатора."
    )
    for user in random.sample(users, k=5):
        notification.users.add(user)  # Создаст записи в UserNotification

    # Ошибки 404
    for _ in range(15):
        Report404.objects.create(url=f"/{fake.uri_path()}")


if __name__ == "__main__":
    print("🚀 Начало заполнения базы данных WhileWork...\n")

    clear_old_data()

    users = generate_users()
    # companies, locations, skills, contacts = generate_base_entities()
    sources = generate_sources()
    # vacancies = generate_vacancies(
    #   users, companies, locations, skills, contacts, sources
    # )
    # generate_activity(users, vacancies)

    print("\n✅ База данных успешно заполнена тестовыми данными!")
