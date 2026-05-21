import json
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator, Final

import httpx

from .config import config
from .schemas import RawMessageBatch, RawMessageCreate

logger = logging.getLogger(__name__)

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
ASSETS: Final[Path] = BASE_DIR / "assets"


class BaseAsyncParser(ABC):
    def __init__(self) -> None:
        self.source_id = config.source_id
        self.identifier = config.identifier
        self.last_parsed_id = config.last_parsed_id
        self.backend_url = config.internal_backend_url

        self.headers = {
            "X-Internal-Secret": config.internal_api_token,
            "Content-Type": "application/json",
        }

        with open(ASSETS / "stop_markers.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        all_phrases = []
        for _, categories in data.items():
            for _, phrases in categories.items():
                all_phrases.extend(phrases)

        self.stop_markers = re.compile(r"(?i)\b(" + r"|".join(all_phrases) + r")\b")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.source_id!r}, {self.platform!r}, {self.identifier!r})"

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
            f"Successfully sent batch of {len(batch.messages)} messages for source {self.source_id}"
        )

    async def report_error(self, client: httpx.AsyncClient, error_msg: str) -> None:
        """
        Sending an error to the backend
        """
        error_url = f"{self.backend_url}/sources/{self.source_id}/report-error/"
        payload = {"error_message": error_msg}

        await client.post(error_url, json=payload, headers=self.headers, timeout=5.0)
        logger.info(f"Reported error for source {self.source_id} to backend.")

    async def run(self) -> None:
        logger.info(
            f"Starting parser for source_id={self.source_id}, target={self.identifier}"
        )

        current_batch = []
        batch_limit = 100

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

                raise
