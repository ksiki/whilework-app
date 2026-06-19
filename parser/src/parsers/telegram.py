import asyncio
import datetime
import logging
import random
from typing import AsyncGenerator

from core.config import InternalAPIData, ParseTarget
from core.schemas import RawMessageCreate
from parsers.base_async_parser import BaseAsyncParser
from telethon import TelegramClient
from telethon.errors import FloodWaitError

logger = logging.getLogger(__name__)


class TelegramParser(BaseAsyncParser):
    def __init__(
        self,
        client: TelegramClient,
        target: ParseTarget,
        internal_api_data: InternalAPIData,
        stop_markers: list[str],
    ) -> None:
        super().__init__(
            target=target,
            internal_api_data=internal_api_data,
            stop_markers=stop_markers,
        )
        self.client = client

    def _get_format_telegram_id(self) -> int:
        clean_id = self.identifier.replace(" ", "")

        if clean_id.startswith("-100"):
            return int(clean_id)

        clean_id = clean_id.lstrip("-")
        return int(f"-100{clean_id}")

    async def fetch_messages(self) -> AsyncGenerator[RawMessageCreate, None]:
        try:
            channel_id = self._get_format_telegram_id()
        except ValueError:
            raise ValueError("Identifier must be an integer ID")

        try:
            entity = await self.client.get_entity(channel_id)
        except ValueError:
            logger.info(f"Cache miss for {channel_id}")
            await self.client.get_dialogs()

            try:
                entity = await self.client.get_entity(channel_id)
            except ValueError as e:
                raise ValueError(f"Channel not found even after cache warmup. e: {e}")
        except FloodWaitError as e:
            logger.warning(
                f"FloodWait on get_entity for {channel_id}. Sleeping {e.seconds}s"
            )
            await asyncio.sleep(e.seconds)
            entity = await self.client.get_entity(channel_id)

        iter_kwargs = {
            "entity": entity,
            "limit": None,
            "reverse": True,
        }

        if self.topic_id:
            iter_kwargs["reply_to"] = int(self.topic_id)
        if self.last_parsed_id:
            iter_kwargs["min_id"] = int(self.last_parsed_id)
        else:
            days_depth = 3
            cold_start_date = datetime.datetime.now(
                datetime.timezone.utc
            ) - datetime.timedelta(days=days_depth)
            iter_kwargs["offset_date"] = cold_start_date

        msg_count = 0
        try:
            async for message in self.client.iter_messages(**iter_kwargs):
                if message.forward or not message.text:
                    continue

                metadata = {
                    "publish_date": message.date.isoformat(),
                }

                yield RawMessageCreate(
                    source_id=self.source_id,
                    topic_id=self.topic_uuid,
                    external_msg_id=str(message.id),
                    raw_text=message.text,
                    metadata=metadata,
                )

                msg_count += 1

                if msg_count % 5 == 0:
                    sleep_time = random.uniform(1.5, 3.5)
                    logger.debug(f"Jitter sleep for {sleep_time:.2f}s...")
                    await asyncio.sleep(sleep_time)

        except FloodWaitError as e:
            logger.error(f"FloodWaitError: sleep {e.seconds}s")
            await asyncio.sleep(e.seconds)
