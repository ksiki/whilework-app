# %%
# Import

import os
import uuid
from pathlib import Path
from typing import Callable, Final, Sequence

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.dialects.postgresql import insert

# %%
# Environment

BASE_DIR: Final[Path] = Path.cwd()

load_dotenv(dotenv_path=BASE_DIR.parent / ".env")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_host = "localhost"
db_port = "5432"
db_name = os.getenv("DB_NAME")

# %%
# Read CSV

df = pd.read_csv(BASE_DIR / "telegram.csv")

total_sources = len(df)
unique_identifiers = df["identifier"].nunique()
duplicates = total_sources - unique_identifiers

sources_with_topics = df["topic_id"].notna().sum()
sources_without_topics = df["topic_id"].isna().sum()

total_topics_count = df["topic_id"].dropna().astype(str).str.split(";").str.len().sum()

print("=== База ===")
print(f"Всего источников загружено: {total_sources}")
print(f"Уникальных ссылок (identifier): {unique_identifiers}")

if duplicates > 0:
    print(f"Дубликатов по полю identifier: {duplicates}")

print("\n=== Статистика по topic_id ===")
print(f"Источников с настроенными топиками: {sources_with_topics}")
print(f"Источников без топиков: {sources_without_topics}")
print(f"Суммарное количество topic_id: {int(total_topics_count)}")

# %%
# Enriching

sources_list = []
topics_list = []

for row in df.itertuples():
    source_uuid = uuid.uuid4()
    sources_list.append(
        {
            "id": source_uuid,
            "platform": row.platform,
            "name": row.name,
            "link": row.link,
            "identifier": row.identifier,
        }
    )

    if pd.isna(row.topic_id):
        continue

    raw_topic_ids = str(row.topic_id).removesuffix(".0")
    topic_ids = [t.strip() for t in raw_topic_ids.split(";")]

    for topic_id in topic_ids:
        if not topic_id:
            continue
        topics_list.append(
            {
                "id": uuid.uuid4(),
                "source_id": source_uuid,
                "topic_id": topic_id,
            }
        )

sources_df = pd.DataFrame(
    sources_list, columns=["id", "platform", "name", "link", "identifier"]
)
topics_df = pd.DataFrame(topics_list, columns=["id", "source_id", "topic_id"])

# %%
# Uploading to the database

database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=db_user,
    password=db_password,
    host=db_host,
    port=db_port,
    database=db_name,
)
engine = create_engine(url=database_url)


def create_upsert_method(unique_columns: Sequence[str]) -> Callable:
    def method(table, conn, keys, data_iter):
        data = [dict(zip(keys, row)) for row in data_iter]
        if not data:
            return

        stmt = insert(table.table).values(data)
        upsert_stmt = stmt.on_conflict_do_nothing(index_elements=unique_columns)

        result = conn.execute(upsert_stmt)
        print(
            f"[Чанк {table.name}] Обработано: {len(data)} | Успешно добавлено: {result.rowcount}"
        )

    return method


def enrich_with_defaults(df: pd.DataFrame) -> pd.DataFrame:
    df_enriched = df.copy()
    current_time = pd.Timestamp.now(tz="UTC")
    df_enriched["created_at"] = current_time
    df_enriched["updated_at"] = current_time
    df_enriched["is_active"] = True
    df_enriched["error_count"] = 0
    return df_enriched


sources_df_prepared = enrich_with_defaults(sources_df)
topics_df_prepared = enrich_with_defaults(topics_df)

sources_df_prepared.to_sql(
    name="sources_source",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=50,
    method=create_upsert_method(["identifier"]),
)

with engine.connect() as conn:
    db_sources_df = pd.read_sql(
        "SELECT id AS real_db_id, identifier FROM sources_source", con=conn
    )

mapping_df = sources_df_prepared[["id", "identifier"]].rename(
    columns={"id": "pandas_id"}
)

topics_df_merged = topics_df_prepared.merge(
    mapping_df, left_on="source_id", right_on="pandas_id", how="inner"
)

topics_df_merged["identifier"] = topics_df_merged["identifier"].astype(str)
db_sources_df["identifier"] = db_sources_df["identifier"].astype(str)

topics_df_merged = topics_df_merged.merge(db_sources_df, on="identifier", how="inner")

topics_df_merged["source_id"] = topics_df_merged["real_db_id"]
topics_df_merged = topics_df_merged.drop(
    columns=["pandas_id", "identifier", "real_db_id"]
)

topics_df_merged.to_sql(
    name="sources_source_topic",
    con=engine,
    if_exists="append",
    index=False,
    chunksize=50,
    method=create_upsert_method(["source_id", "topic_id"]),
)
