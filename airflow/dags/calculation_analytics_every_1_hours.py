import logging
from datetime import timedelta
from pathlib import Path
from typing import Any, Final

import pendulum
from airflow.decorators import dag
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


DAGS_FOLDER = Path(__file__).parent
AIRFLOW_ROOT = DAGS_FOLDER.parent
SCRIPTS_FOLDER = str(AIRFLOW_ROOT / "scripts")

DEFAULT_ARGS: Final[dict[str, Any]] = {
    "owner": "whilework",
    "depends_on_past": False,
    "retries": 2,
    "retry_delta": timedelta(minutes=5),
}


@dag(
    dag_id="calculation_analytics_every_1_hours",
    default_args=DEFAULT_ARGS,
    schedule="0 3 * * *",
    start_date=pendulum.datetime(2026, 7, 6, tz="Europe/Moscow"),
    catchup=False,
    max_active_runs=1,
    template_searchpath=[SCRIPTS_FOLDER],
)
def calculating_analytics() -> None:
    run = SQLExecuteQueryOperator(
        task_id="run_dml_analytics",
        conn_id="postgres_default",
        sql="DML_calculating_analytics.sql",
    )

    run


dag_instance = calculating_analytics()
