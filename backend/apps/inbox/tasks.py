# apps/inbox/tasks.py
import hashlib
import logging
import re

from asgiref.sync import async_to_sync
from core.broker import broker
from django.db import transaction
from django.utils import timezone

from apps.inbox.models import ParserRawMessage
from apps.system import services as system_services
from apps.vacancies.llm_service import extract_vacancy_data
from apps.vacancies.models import Company, Contact, Location, Skill, Vacancy

logger = logging.getLogger(__name__)


def generate_content_hash(text: str) -> str:
    text = text.lower()
    text = re.sub(r"http[s]?://\S+", "", text)
    text = re.sub(r"\W+", "", text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@broker.task
def process_pending_messages_task(count: int) -> None:
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
        try:
            clean_data = async_to_sync(extract_vacancy_data)(msg.raw_text)
            if not clean_data:
                msg.status = ParserRawMessage.Status.FAILED
                msg.save(update_fields=["status", "updated_at"])
                continue

            if not clean_data.is_vacancy:
                logger.info(f"Skipped message {msg.id}. Reason: {clean_data.reasoning}")
                msg.status = ParserRawMessage.Status.REJECTED
                msg.metadata["reject_reason"] = clean_data.reasoning
                msg.save(update_fields=["status", "metadata", "updated_at"])
                continue

            if not clean_data.description or not clean_data.description.strip():
                logger.info(f"Skipped message {msg.id}. Reason: Empty description")
                msg.status = ParserRawMessage.Status.REJECTED
                msg.metadata["reject_reason"] = (
                    "LLM не смогла извлечь описание вакансии"
                )
                msg.save(update_fields=["status", "metadata", "updated_at"])
                continue

            with transaction.atomic():
                company_obj = None
                if clean_data.company_name:
                    company_obj = Company.objects.get_or_create(
                        name=clean_data.company_name.strip()
                    )[0]

                location_obj = None
                if any(
                    [
                        clean_data.location_region,
                        clean_data.location_country,
                        clean_data.location_city,
                    ]
                ):
                    location_obj = Location.objects.get_or_create(
                        region=clean_data.location_region,
                        country=clean_data.location_country,
                        city=clean_data.location_city,
                    )[0]

                current_hash = generate_content_hash(msg.raw_text)
                vacancy, created = Vacancy.objects.get_or_create(
                    content_hash=current_hash,
                    defaults={
                        "source": msg.source,
                        "company": company_obj,
                        "location": location_obj,
                        "title": clean_data.title,
                        "description": clean_data.description,
                        "salary_min": clean_data.salary_min,
                        "salary_max": clean_data.salary_max,
                        "currency": clean_data.currency,
                        "grade": clean_data.grade.value if clean_data.grade else None,
                        "experience_from": clean_data.experience_from,
                        "employment_type": clean_data.employment_type.value
                        if clean_data.employment_type
                        else None,
                        "english_level": clean_data.english_level.value
                        if clean_data.english_level
                        else None,
                        "work_format": clean_data.work_format.value
                        if clean_data.work_format
                        else None,
                        "usd_salary_min": system_services.convert_to_usd(
                            amount=clean_data.salary_min, iso_code=clean_data.currency
                        )
                        if clean_data.salary_min
                        else None,
                        "published_at": msg.metadata.get(
                            "publish_date", timezone.now()
                        ),
                    },
                )

                if created:
                    if clean_data.skills:
                        skill_objects = []
                        for skill_name in clean_data.skills:
                            clean_skill = skill_name.strip().lower()
                            if clean_skill:
                                skill_obj = Skill.objects.get_or_create(
                                    name=clean_skill
                                )[0]
                                skill_objects.append(skill_obj)

                        vacancy.skills.set(skill_objects)

                    if clean_data.contacts:
                        contact_objects = []
                        for contact_data in clean_data.contacts:
                            contact_obj = Contact.objects.get_or_create(
                                platform=contact_data.platform,
                                details=contact_data.details.strip(),
                            )[0]
                            contact_objects.append(contact_obj)

                        vacancy.contact.set(contact_objects)

                msg.status = ParserRawMessage.Status.PROCESSED
                msg.save(update_fields=["status", "updated_at"])

        except Exception as e:
            logger.error(f"Error parsing message {msg.id}: {str(e)}", exc_info=True)
            msg.status = ParserRawMessage.Status.FAILED
            msg.metadata = msg.metadata or {}
            msg.metadata["parse_error"] = str(e)
            msg.save(update_fields=["status", "metadata", "updated_at"])
