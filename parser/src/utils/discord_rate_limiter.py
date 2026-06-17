import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)


class DiscordRateLimiter:
    def __init__(self):
        self.lock = asyncio.Lock()
        self.remaining = 1
        self.reset_time = 0.0

    async def acquire(self) -> None:
        async with self.lock:
            now = time.time()
            if self.remaining <= 0 and now < self.reset_time:
                sleep_duration = (self.reset_time - now) + 0.5
                logger.warning(
                    f"Rate limit threshold reached. Sleeping globally for {sleep_duration:.2f}s"
                )
                await asyncio.sleep(sleep_duration)

            self.remaining -= 1

    def update_from_headers(self, headers: httpx.Headers) -> None:
        remaining = headers.get("x-ratelimit-remaining")
        reset = headers.get("x-ratelimit-reset")

        if remaining is not None:
            self.remaining = int(remaining)
        if reset is not None:
            self.reset_time = float(reset)

        logger.info(
            f"Limits updated: {self.remaining} requests left until {self.reset_time}"
        )
