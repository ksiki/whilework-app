from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from slugify import slugify
from unidecode import unidecode

from apps.vacancies.models import Skill


class Command(BaseCommand):
    help = "Безопасно перегенерирует слаги для всех навыков по IT-правилам"

    def it_slugify(self, text: str) -> str:
        """Безопасный слаг для ИТ-терминов."""
        safe_name = (
            text.replace("+", "-plus-").replace("#", "-sharp-").replace(".", "-dot-")
        )
        return slugify(unidecode(safe_name))

    def handle(self, *args, **options):
        skills = Skill.objects.all()
        total = skills.count()
        updated_count = 0
        collision_count = 0
        error_count = 0

        self.stdout.write(self.style.WARNING(f"Начинаем проверку {total} навыков..."))

        for skill in skills:
            expected_slug = self.it_slugify(skill.name)

            if skill.slug != expected_slug:
                old_slug = skill.slug

                try:
                    with transaction.atomic():
                        skill.slug = expected_slug
                        skill.save(update_fields=["slug"])

                    updated_count += 1
                    self.stdout.write(
                        f"Обновлен: {skill.name} | {old_slug} -> {expected_slug}"
                    )

                except IntegrityError:
                    fallback_slug = f"{expected_slug}-{skill.id}"

                    try:
                        with transaction.atomic():
                            skill.slug = fallback_slug
                            skill.save(update_fields=["slug"])

                        collision_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"Исправлена коллизия: {skill.name} | {old_slug} -> {fallback_slug}"
                            )
                        )
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f"Критическая ошибка при обновлении {skill.name}: {e}"
                            )
                        )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nГотово!\n"
                f"- Всего проверено: {total}\n"
                f"- Успешно обновлено: {updated_count}\n"
                f"- Исправлено коллизий: {collision_count}\n"
                f"- Ошибок: {error_count}"
            )
        )
