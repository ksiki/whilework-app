import json
import logging
import os
import re
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Final

import httpx

from .schemas import RawMessageBatch, RawMessageCreate

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent
ASSETS: Final[Path] = BASE_DIR / "assets"


class BaseAsyncParser(ABC):
    def __init__(
        self, source_id: int, target_url: str, last_parsed_id: str | None
    ) -> None:
        self.source_id = source_id
        self.target_url = target_url
        self.last_parsed_id = last_parsed_id

        self.internal_secret = os.getenv("INTERNAL_SECRET_TOKEN")
        self.backend_url = os.getenv("BACKEND_INTERNAL_API_URL")
        self.backend_url = f"{self.backend_url}/{self.source_id}"
        self.headers = {
            "X-Internal-Secret": self.internal_secret,
            "Content-Type": "application/json",
        }

        with open(ASSETS / "stop_markers.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        all_phrases = []
        for _, categories in data.items():
            for _, phrases in categories.items():
                all_phrases.extend(phrases)

        self.stop_markers = re.compile(r"(?i)\b(" + r"|".join(all_phrases) + r")\b")

    @abstractmethod
    @asynccontextmanager
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

    async def send_to_backend(self, batch: RawMessageBatch) -> None:
        async with httpx.AsyncClient() as client:
            api_url = f"{self.backend_url}/load-vacancies/"
            try:
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
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error sending to backend: {e.response.status_code} - {e.response.text}"
                )
                raise
            except httpx.RequestError as e:
                logger.error(f"Network error sending to backend: {str(e)}")
                raise

    async def report_error(self, error_msg: str) -> None:
        """
        Sending an error to the backend
        """
        error_url = f"{self.backend_url}/report-error/"
        payload = {"error_message": error_msg}

        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    error_url, json=payload, headers=self.headers, timeout=5.0
                )
                logger.info(f"Reported error for source {self.source_id} to backend.")
            except Exception as e:
                logger.error(f"Failed to report error to backend: {str(e)}")
                raise

    async def run(self) -> None:
        logger.info(
            f"Starting parser for source_id={self.source_id}, target={self.target_url}"
        )

        current_batch = []
        batch_limit = 100

        try:
            async for raw_message in self.fetch_messages():
                if not self.apply_screening(raw_message.raw_text):
                    continue

                current_batch.append(raw_message)

                if len(current_batch) >= batch_limit:
                    batch_model = RawMessageBatch(messages=current_batch)
                    await self.send_to_backend(batch_model)
                    current_batch = []

            if current_batch:
                batch_model = RawMessageBatch(messages=current_batch)
                await self.send_to_backend(batch_model)
        except Exception as e:
            error_text = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Fatal error in parser run loop: {str(e)}")

            await self.report_error(error_text)

            raise
