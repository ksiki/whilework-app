from typing import Final

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    auth_credentials: str

    source_id: str
    platform: str
    identifier: str
    last_parsed_id: str | None

    internal_api_token: str
    internal_backend_url: str

    @field_validator("last_parsed_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value


config: Final[Config] = Config()
