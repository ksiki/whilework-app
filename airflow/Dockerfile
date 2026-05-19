FROM apache/airflow:2.9.0-python3.12

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER airflow

ENV POETRY_VERSION=1.8.2 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install "poetry==$POETRY_VERSION"

COPY pyproject.toml ./
RUN poetry install --no-interaction --no-ansi --no-root