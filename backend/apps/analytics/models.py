from core.models import TimeStampedMixin
from django.db import models
from django.db.models import JSONField


class GlobalAnalyticsSnapshot(TimeStampedMixin):
    """
    Хранит периодически рассчитываемые слепки глобальной аналитики
    для быстрого отображения дашборда без фильтров.
    """

    # Общие мета-данные
    total_vacancies = models.IntegerField(
        verbose_name="Общее количество активных вакансий в выборке", default=0
    )

    # 1. Топ востребованных технологий
    # Ожидаемый формат: [{"skill": "Python", "count": 1500}, {"skill": "PostgreSQL", "count": 1200}, ...]
    top_skills = JSONField(verbose_name="Топ навыков", default=list)

    # 2. Распределение форматов работы
    # Ожидаемый формат: {"Uncnown": 100, "Remote": 800, "Office": 200, "Hybrid": 400}
    work_formats = JSONField(verbose_name="Форматы работы", default=dict)

    # 3. Воронка требуемого опыта
    # Ожидаемый формат: {"Uncnown": 50, "1": 400, "2": 700, "3": 150, ...}
    experience_funnel = JSONField(verbose_name="Опыт работы", default=dict)

    # 4. Круговая диаграмма по грейдам
    # Ожидаемый формат: {"Junior": 100, "Middle": 600, "Senior": 400, ...}
    grades_distribution = JSONField(
        verbose_name="Распределение по грейдам", default=dict
    )

    # 5. Количество вакансий за каждый месяц
    # Ожидаемый формат (день-месяц): [{"day": "30-05", "count": 320}, {"day": "01-06", "count": 410}]
    vacancies_per_day = JSONField(verbose_name="Динамика вакансий", default=list)

    class Meta:
        db_table = "analytics_global_snapshot"
        verbose_name = "Global Analytics Snapshot"
        verbose_name_plural = "Global Analytics Snapshots"
        ordering = ["-created_at"]
        get_latest_by = "created_at"

    def __str__(self):
        return f"Analytic at {self.created_at.strftime('%Y-%m-%d %H:%M')} (Total: {self.total_vacancies})"
