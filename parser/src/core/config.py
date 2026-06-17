from typing import Any, Optional

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class ParseTarget(BaseModel):
    source_id: str
    identifier: str
    topic_uuid: Optional[str] = None
    topic_id: Optional[str] = None
    last_parsed_id: str


class InternalAPIData(BaseSettings):
    internal_api_token: str
    internal_backend_url: str

    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore")


class ParseData(BaseSettings):
    platform: str
    sources_batch: list[dict[str, Any]]
    auth_data: dict[str, Any]

    model_config = SettingsConfigDict(env_ignore_empty=True, extra="ignore")
