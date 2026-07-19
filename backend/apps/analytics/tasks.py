import logging
from pathlib import Path

from core.broker import broker
from django.db import connection

logger = logging.getLogger(__name__)

SQL_DIR = Path(__file__).resolve().parent / "sql"
ANALYTICS_SQL_FILE = SQL_DIR / "DML_calculating_analytics.sql"


@broker.task(schedule=[{"cron": "30 * * * *"}])
def run_dml_analytics_task() -> None:
    """
    Периодическая задача для агрегации данных и расчета аналитики.
    Выполняется каждый час в 30 минут.
    """
    if not ANALYTICS_SQL_FILE.exists():
        logger.error("SQL file not found at: %s", ANALYTICS_SQL_FILE)
        return

    try:
        with open(ANALYTICS_SQL_FILE, "r", encoding="utf-8") as file:
            sql_query = file.read()

        with connection.cursor() as cursor:
            cursor.execute(sql_query)

        logger.info("Analytics DML script executed successfully.")
    except Exception as e:
        logger.error(
            "Failed to execute analytics DML script: %s", str(e), exc_info=True
        )
        raise
