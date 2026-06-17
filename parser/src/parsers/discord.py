import asyncio
import datetime
import logging
from typing import AsyncGenerator

import httpx
from core.config import InternalAPIData, ParseTarget
from core.schemas import RawMessageCreate
from utils.discord_rate_limiter import DiscordRateLimiter

from .base_async_parser import BaseAsyncParser

logger = logging.getLogger(__name__)


class DiscordParser(BaseAsyncParser):
    def __init__(
        self,
        token: str,
        target: ParseTarget,
        internal_api_data: InternalAPIData,
        stop_markers: list[str],
        rate_limiter: DiscordRateLimiter,
        http_client: httpx.AsyncClient,
    ) -> None:
        super().__init__(target, internal_api_data, stop_markers)
        self.token = token
        self.rate_limiter = rate_limiter
        self.http_client = http_client

        self.ds_headers = {
            "Authorization": self.token,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    def _get_snowflake_for_date(self, dt: datetime.datetime) -> str:
        discord_epoch = 1420070400000
        timestamp_ms = int(dt.timestamp() * 1000)
        snowflake = (timestamp_ms - discord_epoch) << 22
        return str(snowflake)

    async def fetch_messages(self) -> AsyncGenerator[RawMessageCreate, None]:
        target_channel_id = self.topic_id if self.topic_id else self.identifier
        url = f"https://discord.com/api/v9/channels/{target_channel_id}/messages"

        params = {"limit": 50}

        if self.last_parsed_id:
            params["after"] = self.last_parsed_id
        else:
            days_depth = 14
            cold_start_date = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(days=days_depth)

            params["after"] = self._get_snowflake_for_date(cold_start_date)

        while True:
            await self.rate_limiter.acquire()

            response = await self.http_client.get(
                url, headers=self.ds_headers, params=params
            )

            self.rate_limiter.update_from_headers(response.headers)

            if response.status_code == 429:
                retry_after = response.json().get("retry_after", 5.0)
                logger.error(f"Status code = 429; Retry after: {retry_after}s")
                await asyncio.sleep(retry_after)
                continue

            response.raise_for_status()
            messages = response.json()

            if not messages:
                break

            messages.sort(key=lambda x: int(x["id"]))

            for msg in messages:
                metadata = {
                    "publish_date": msg.get("timestamp"),
                }

                yield RawMessageCreate(
                    source_id=self.source_id,
                    topic_id=self.topic_uuid,
                    external_msg_id=msg["id"],
                    raw_text=msg.get("content", ""),
                    metadata=metadata,
                )

            params["after"] = messages[-1]["id"]
