import logging
import re
from abc import ABC, abstractmethod
from typing import AsyncGenerator

import httpx
from core.config import InternalAPIData, ParseTarget
from core.schemas import RawMessageBatch, RawMessageCreate

logger = logging.getLogger(__name__)


class BaseAsyncParser(ABC):
    def __init__(
        self,
        target: ParseTarget,
        internal_api_data: InternalAPIData,
        stop_markers: list[str],
    ) -> None:
        self.source_id = target.source_id
        self.identifier = target.identifier

        self.topic_uuid = target.topic_uuid
        self.topic_id = target.topic_id
        self.last_parsed_id = target.last_parsed_id

        self.backend_url = internal_api_data.internal_backend_url
        self.headers = {
            "X-Internal-Secret": internal_api_data.internal_api_token,
            "Content-Type": "application/json",
        }

        self.stop_markers = re.compile(r"(?i)\b(" + r"|".join(stop_markers) + r")\b")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.source_id!r}, {self.identifier!r}, topic={self.topic_id!r})"

    @abstractmethod
    async def fetch_messages(self) -> AsyncGenerator[RawMessageCreate, None]:
        """
        The method must "yield" RawMessageCreate objects starting with self.last_parsed_id
        """
        pass

    def apply_screening(self, text: str) -> bool:
        """
        Checks for keywords and the absence of stop markers
        """
        if not text:
            return False

        if self.stop_markers.search(text):
            return False

        return True

    async def send_to_backend(
        self, client: httpx.AsyncClient, batch: RawMessageBatch
    ) -> None:
        api_url = f"{self.backend_url}/inbox/batch/"
        response = await client.post(
            api_url,
            content=batch.model_dump_json(),
            headers=self.headers,
            timeout=10.0,
        )
        response.raise_for_status()
        logger.info(
            f"Successfully sent batch of {len(batch.messages)} messages for source {self.source_id} (topic: {self.topic_id})"
        )

    async def report_error(self, client: httpx.AsyncClient, error_msg: str) -> None:
        """
        Sending an error to the backend
        """
        error_url = f"{self.backend_url}/sources/{self.source_id}/report-error/"
        payload = {"error_message": error_msg}

        if self.topic_uuid:
            payload["topic_id"] = self.topic_uuid

        await client.post(error_url, json=payload, headers=self.headers, timeout=5.0)
        logger.info(
            f"Reported error for source {self.source_id} (topic: {self.topic_uuid}) to backend."
        )

    async def run(self) -> None:
        logger.info(
            f"Starting parser for source_id={self.source_id}, target={self.identifier}, topic_id={self.topic_id}"
        )

        current_batch = []
        batch_limit = 15

        async with httpx.AsyncClient(timeout=10.0, headers=self.headers) as http_client:
            try:
                async for raw_message in self.fetch_messages():
                    if not self.apply_screening(raw_message.raw_text):
                        continue

                    current_batch.append(raw_message)

                    if len(current_batch) >= batch_limit:
                        batch_model = RawMessageBatch(messages=current_batch)
                        await self.send_to_backend(
                            client=http_client, batch=batch_model
                        )
                        current_batch.clear()

                if current_batch:
                    batch_model = RawMessageBatch(messages=current_batch)
                    await self.send_to_backend(client=http_client, batch=batch_model)
            except Exception as e:
                logger.error(f"Fatal error in parser run loop: {str(e)}")

                error_text = f"{type(e).__name__}: {str(e)}"
                await self.report_error(client=http_client, error_msg=error_text)
