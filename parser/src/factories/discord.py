from typing import Iterator

import httpx
from core.config import InternalAPIData, ParseTarget
from parsers.base_async_parser import BaseAsyncParser
from parsers.discord import DiscordParser
from utils.discord_rate_limiter import DiscordRateLimiter

from .base_parser_factory import BaseParserFactory


class DiscordParserFactory(BaseParserFactory):
    def __init__(self, auth_data: dict, internal_api_data: InternalAPIData):
        super().__init__(auth_data, internal_api_data)
        self.token = auth_data.get("discord_token")

        self.rate_limiter = DiscordRateLimiter()
        self.http_client = None

    async def setup(self) -> None:
        self.http_client = httpx.AsyncClient(timeout=15.0)

    async def teardown(self) -> None:
        if self.http_client:
            await self.http_client.aclose()

    def create_parsers(
        self, targets: list[ParseTarget], stop_markers: list[str]
    ) -> Iterator[BaseAsyncParser]:
        return (
            DiscordParser(
                token=self.token,
                target=target,
                internal_api_data=self.internal_api_data,
                stop_markers=stop_markers,
                rate_limiter=self.rate_limiter,
                http_client=self.http_client,
            )
            for target in targets
        )
