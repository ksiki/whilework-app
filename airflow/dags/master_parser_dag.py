import logging
import os
from datetime import datetime, timedelta
from typing import Any

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.http.hooks.http import HttpHook

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "whilework",
    "depends_on_past": False,
    "retries": 2,
    "retry_delta": timedelta(minutes=5),
}


@dag(
    dag_id="master_parser_orchestrator",
    default_args=DEFAULT_ARGS,
    schedule="*/5 * * * *",
    start_date=datetime(2026, 5, 20),
    catchup=False,
    max_active_runs=1,
)
def master_parser_dag() -> None:
    @task(multiple_outputs=False)
    def fetch_active_sources() -> list[dict[str, Any]]:
        internal_token = os.getenv("INTERNAL_API_SECRET")
        headers = {"X-Internal-Secret": internal_token}

        http_hook = HttpHook(http_conn_id="internal_api", method="GET")
        endpoint = "/api/internal/v1"

        response = http_hook.run(endpoint=f"{endpoint}/sources/", headers=headers)
        records = response.json()

        if not records:
            logger.warning("Sources list is empty")
            return []

        tg_session = Variable.get("TG_MAIN_SESSION")
        tg_api_id = Variable.get("TG_API_ID")
        tg_api_hash = Variable.get("TG_API_HASH")
        discord_token = Variable.get("DISCORD_BOT_TOKEN")

        env_list = []
        for row in records:
            platform = str(row.get("platform")).lower()
            last_parsed_id = row.get("last_parsed_id")

            if platform == "telegram":
                auth_creds = tg_session
            elif platform == "discord":
                auth_creds = discord_token
            else:
                auth_creds = ""

            env_list.append(
                {
                    "SOURCE_ID": str(row.get("id")),
                    "PLATFORM": platform,
                    "IDENTIFIER": str(row.get("identifier")),
                    "LAST_PARSED_ID": str(last_parsed_id)
                    if last_parsed_id is not None
                    else "",
                    "AUTH_CREDENTIALS": auth_creds,
                    "TG_API_ID": tg_api_id,
                    "TG_API_HASH": tg_api_hash,
                    "INTERNAL_API_TOKEN": internal_token,
                    "INTERNAL_BACKEND_URL": f"{http_hook.host}{endpoint}",
                }
            )

        return env_list

    active_sources_envs = fetch_active_sources()

    run_parsers = DockerOperator.partial(
        task_id="run_isolated_parser",
        image="whilework-app-parser:latest",
        api_version="auto",
        auto_remove="success",
        network_mode="backend_network",
        docker_url="unix://var/run/docker.sock",
        pool="docker_parsers_pool",
    ).expand(environment=active_sources_envs)

    active_sources_envs >> run_parsers


dag_instance = master_parser_dag()
