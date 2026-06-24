import json
import logging
import os
from collections import defaultdict
from datetime import timedelta
from typing import Any, Final

import pendulum
from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.providers.http.hooks.http import HttpHook

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _get_auth_data(platform: str) -> dict[str, Any]:
    if platform == "telegram":
        tg_config = Variable.get("TG_CONFIG", deserialize_json=True, default_var={})
        return {
            "TG_SESSION": tg_config.get("session", ""),
            "TG_API_ID": tg_config.get("api_id", ""),
            "TG_API_HASH": tg_config.get("api_hash", ""),
            "PROXY_URL": tg_config.get("proxy_url", ""),
        }
    elif platform == "discord":
        return {
            "DISCORD_TOKEN": Variable.get("DISCORD_BOT_TOKEN", default_var=""),
        }

    return {}


DEFAULT_ARGS: Final[dict[str, Any]] = {
    "owner": "whilework",
    "depends_on_past": False,
    "retries": 2,
    "retry_delta": timedelta(minutes=5),
}


@dag(
    dag_id="master_parser_orchestrator_v2",
    default_args=DEFAULT_ARGS,
    schedule="0 3,9,15,21 * * *",
    start_date=pendulum.datetime(2026, 6, 23, tz="Europe/Moscow"),
    catchup=False,
    max_active_runs=1,
)
def master_parser_dag() -> None:
    @task(multiple_outputs=False)
    def fetch_active_sources() -> list[dict[str, Any]]:
        internal_token = os.getenv("INTERNAL_API_SECRET")
        headers = {"X-Internal-Secret": internal_token}

        http_hook = HttpHook(http_conn_id="INTERNAL_API", method="GET")
        endpoint = "/api/internal/v1"

        response = http_hook.run(endpoint=f"{endpoint}/sources/", headers=headers)
        records = response.json()

        if not records:
            logger.warning("Sources list is empty")
            return []

        grouped_sources = defaultdict(list)
        for row in records:
            platform = str(row.get("platform")).lower()

            grouped_sources[platform].append(
                {
                    "SOURCE_ID": str(row.get("id")),
                    "IDENTIFIER": str(row.get("identifier")),
                    "LAST_PARSED_ID": str(row.get("last_parsed_id") or ""),
                    "TOPICS": row.get("topics", []),
                }
            )

        env_list = []
        for platform, sources in grouped_sources.items():
            if not sources:
                continue

            env_list.append(
                {
                    "environment": {
                        "PLATFORM": platform,
                        "SOURCES_BATCH": json.dumps(sources),
                        "AUTH_DATA": json.dumps(_get_auth_data(platform=platform)),
                        "INTERNAL_API_TOKEN": internal_token,
                        "INTERNAL_BACKEND_URL": f"{http_hook.base_url}{endpoint}",
                    },
                    "container_name": "airflow-parser-{{ ti.map_index }}-{{ run_id }}",
                }
            )

        return env_list

    active_sources_envs = fetch_active_sources()

    run_parsers = DockerOperator.partial(
        task_id="run_isolated_parser",
        image="whilework-app-parser:latest",
        api_version="auto",
        auto_remove="success",
        network_mode="whilework-app_backend_network",
        docker_url="unix://var/run/docker.sock",
        pool="docker_parsers_pool",
        mount_tmp_dir=False,
    ).expand_kwargs(active_sources_envs)

    active_sources_envs >> run_parsers


dag_instance = master_parser_dag()
