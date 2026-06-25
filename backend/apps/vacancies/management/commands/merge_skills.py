from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.inbox.tasks import normalize_skill_name
from apps.vacancies.models import Skill


class Command(BaseCommand):
    help = "Объединяет дублирующиеся навыки и нормализует их названия на основе skill_aliases.json"

    def handle(self, *args, **options):
        grouped_skills = defaultdict(list)
        all_skills = Skill.objects.all()

        self.stdout.write(
            self.style.WARNING(f"Total skills before cleaning: {all_skills.count()}")
        )

        for skill in all_skills:
            norm_name = normalize_skill_name(skill.name)
            if norm_name:
                grouped_skills[norm_name].append(skill)

        merged_count = 0
        deleted_count = 0

        with transaction.atomic():
            for norm_name, skills_list in grouped_skills.items():
                if len(skills_list) <= 1:
                    single_skill = skills_list[0]
                    if single_skill.name != norm_name:
                        single_skill.name = norm_name
                        single_skill.save(update_fields=["name"])
                    continue

                skills_list.sort(key=lambda x: x.id)
                canonical_skill = skills_list[0]
                duplicate_skills = skills_list[1:]

                if canonical_skill.name != norm_name:
                    canonical_skill.name = norm_name
                    canonical_skill.save(update_fields=["name"])

                self.stdout.write(
                    f"Union for '{norm_name}' (Canonical ID: {canonical_skill.id})"
                )

                for dup_skill in duplicate_skills:
                    related_vacancies = list(dup_skill.vacancies.all())

                    if related_vacancies:
                        canonical_skill.vacancies.add(*related_vacancies)
                        merged_count += len(related_vacancies)

                    dup_skill.delete()
                    deleted_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successful! \n"
                f"- Reassigned vacancies: {merged_count}\n"
                f"- Deleted trash tags: {deleted_count}\n"
                f"Left unique skills: {Skill.objects.count()}"
            )
        )
