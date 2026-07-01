import hashlib
import logging
from datetime import datetime, timedelta

from asgiref.sync import async_to_sync
from core.broker import broker
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.system import services as system_services
from apps.vacancies.llm_service import extract_vacancy_data
from apps.vacancies.models import Company, Contact, Location, Relocation, Skill, Vacancy
from apps.vacancies.schemas import (
    CleanVacancySchema,
)

from . import tools
from .models import ParserRawMessage

logger = logging.getLogger(__name__)


def generate_semantic_hash(
    company: str | None,
    title: str | None,
    experience: int | None,
    work_format: str | None,
    salary_min: int | None,
    salary_max: int | None,
    contacts: list | None,
) -> str:
    comp = str(company).lower().strip() if company else "no_comp"
    ttl = str(title).lower().strip() if title else "no_title"
    exp = str(experience).strip() if experience is not None else "no_exp"
    fmt = str(work_format).lower().strip() if work_format else "no_fmt"
    s_min = str(salary_min).strip() if salary_min is not None else "no_smin"
    s_max = str(salary_max).strip() if salary_max is not None else "no_smax"

    cnts = "no_contacts"
    if contacts:
        extracted_contacts = [str(c.details).lower().strip() for c in contacts]
        cnts = ",".join(sorted(extracted_contacts))

    raw_string = f"{comp}|{ttl}|{exp}|{fmt}|{s_min}|{s_max}|{cnts}"

    return hashlib.sha256(raw_string.encode("utf-8")).hexdigest()


def _get_publish_date(msg: ParserRawMessage) -> datetime:
    """Извлекает и безопасно парсит дату публикации из метадаты."""
    raw_date = msg.metadata.get("publish_date")
    if raw_date:
        parsed_date = parse_datetime(raw_date)
        if parsed_date:
            return parsed_date
    return timezone.now()


def _save_vacancy_to_db(
    msg: ParserRawMessage, clean_data: CleanVacancySchema, publish_date: datetime
) -> bool:
    """
    Сохраняет вакансию в БД. Возвращает True, если обработка завершена успешно,
    или False, если это дубликат, который нужно проигнорировать.
    """
    with transaction.atomic():
        company_obj = None
        if clean_data.company_name:
            company_name = clean_data.company_name.strip()
            try:
                with transaction.atomic():
                    company_obj, _ = Company.objects.get_or_create(name=company_name)
            except IntegrityError:
                company_obj = Company.objects.get(name=company_name)

        relocation_obj = None
        if clean_data.relocation_country:
            relocation_country = clean_data.relocation_country.strip()
            try:
                with transaction.atomic():
                    relocation_obj, _ = Relocation.objects.get_or_create(
                        country=relocation_country
                    )
            except IntegrityError:
                relocation_obj = Relocation.objects.get(country=relocation_country)

        location_obj = None
        if any(
            [
                clean_data.location_region,
                clean_data.location_country,
                clean_data.location_city,
            ]
        ):
            location_obj, _ = Location.objects.get_or_create(
                region=clean_data.location_region,
                country=clean_data.location_country,
                city=clean_data.location_city,
            )

        current_hash = generate_semantic_hash(
            company=clean_data.company_name,
            title=clean_data.title,
            experience=clean_data.experience_from,
            work_format=clean_data.work_format.value
            if clean_data.work_format
            else None,
            salary_min=clean_data.salary_min,
            salary_max=clean_data.salary_max,
            contacts=clean_data.contacts,
        )

        existing_vacancy = Vacancy.objects.filter(content_hash=current_hash).first()

        if existing_vacancy:
            time_difference = publish_date - existing_vacancy.published_at

            if time_difference <= timedelta(days=7):
                return False
            else:
                existing_vacancy.published_at = publish_date
                existing_vacancy.save(update_fields=["published_at"])
                return True

        vacancy = Vacancy.objects.create(
            content_hash=current_hash,
            source=msg.source,
            company=company_obj,
            location=location_obj,
            relocation=relocation_obj,
            title=clean_data.title,
            description=clean_data.description,
            salary_min=clean_data.salary_min,
            salary_max=clean_data.salary_max,
            currency=clean_data.currency,
            grade=clean_data.grade.value if clean_data.grade else None,
            experience_from=clean_data.experience_from,
            employment_type=clean_data.employment_type.value
            if clean_data.employment_type
            else None,
            english_level=clean_data.english_level.value
            if clean_data.english_level
            else None,
            work_format=clean_data.work_format.value
            if clean_data.work_format
            else None,
            usd_salary_min=(
                system_services.convert_to_usd(
                    amount=clean_data.salary_min, iso_code=clean_data.currency
                )
                if clean_data.salary_min
                else None
            ),
            published_at=publish_date,
        )

        if clean_data.skills:
            skill_objects = []
            for skill_name in clean_data.skills:
                clean_skill = tools.normalize_skill_name(skill_name)
                if clean_skill:
                    try:
                        with transaction.atomic():
                            skill_obj, _ = Skill.objects.get_or_create(name=clean_skill)
                    except IntegrityError:
                        skill_obj = Skill.objects.get(name=clean_skill)
                    skill_objects.append(skill_obj)
            vacancy.skills.set(skill_objects)

        if clean_data.contacts:
            contact_objects = []
            for contact_data in clean_data.contacts:
                contact_obj, _ = Contact.objects.get_or_create(
                    platform=contact_data.platform,
                    details=contact_data.details.strip(),
                )
                contact_objects.append(contact_obj)
            vacancy.contact.set(contact_objects)

        return True


def _process_single_message(msg: ParserRawMessage) -> None:
    """Обрабатывает одно сообщение: работает с LLM и управляет статусами."""
    try:
        clean_data = async_to_sync(extract_vacancy_data)(msg.raw_text)

        if not clean_data:
            msg.status = ParserRawMessage.Status.FAILED
            msg.save(update_fields=["status", "updated_at"])
            return

        if not clean_data.is_vacancy:
            logger.info(f"Skipped message {msg.id}. Reason: {clean_data.reasoning}")
            msg.status = ParserRawMessage.Status.REJECTED
            msg.metadata["reject_reason"] = clean_data.reasoning
            msg.save(update_fields=["status", "metadata", "updated_at"])
            return

        if not clean_data.description or not clean_data.description.strip():
            logger.info(f"Skipped message {msg.id}. Reason: Empty description")
            msg.status = ParserRawMessage.Status.REJECTED
            msg.metadata["reject_reason"] = "LLM не смогла извлечь описание вакансии"
            msg.save(update_fields=["status", "metadata", "updated_at"])
            return

        valid_contacts = tools.process_and_filter_contacts(clean_data.contacts)
        if not valid_contacts:
            logger.info(
                f"Skipped message {msg.id}. Reason: No valid contacts after filtering."
            )
            msg.status = ParserRawMessage.Status.REJECTED
            msg.metadata["reject_reason"] = (
                "Все извлеченные контакты оказались невалидными (или их не было)"
            )
            msg.save(update_fields=["status", "metadata", "updated_at"])
            return
        clean_data.contacts = valid_contacts

        publish_date = _get_publish_date(msg)

        is_saved = _save_vacancy_to_db(msg, clean_data, publish_date)

        if not is_saved:
            logger.info(f"Skipped message {msg.id}. Reason: Duplicate within 7 days.")
            msg.status = ParserRawMessage.Status.REJECTED
            msg.metadata["reject_reason"] = "Дубликат вакансии (менее 7 дней)"
        else:
            msg.status = ParserRawMessage.Status.PROCESSED

        msg.save(update_fields=["status", "metadata", "updated_at"])

    except Exception as e:
        logger.error(f"Error parsing message {msg.id}: {str(e)}", exc_info=True)
        msg.status = ParserRawMessage.Status.FAILED
        msg.metadata = msg.metadata or {}
        msg.metadata["parse_error"] = str(e)
        msg.save(update_fields=["status", "metadata", "updated_at"])


@broker.task
def process_pending_messages_task(count: int) -> None:
    """Точка входа брокера. Получает сообщения и передает их в обработчик."""
    with transaction.atomic():
        messages_qs = ParserRawMessage.objects.filter(
            status=ParserRawMessage.Status.PENDING
        ).select_for_update(skip_locked=True)[:count]

        message_ids = list(messages_qs.values_list("id", flat=True))
        if not message_ids:
            return

        ParserRawMessage.objects.filter(id__in=message_ids).update(
            status=ParserRawMessage.Status.PROCESSING
        )

    messages = ParserRawMessage.objects.filter(id__in=message_ids)

    for msg in messages:
        _process_single_message(msg)
