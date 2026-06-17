from abc import ABC, abstractmethod
from typing import Iterator

from core.config import InternalAPIData, ParseTarget
from parsers.base_async_parser import BaseAsyncParser


class BaseParserFactory(ABC):
    def __init__(self, auth_data: dict, internal_api_data: InternalAPIData):
        self.auth_data = auth_data
        self.internal_api_data = internal_api_data

    @abstractmethod
    async def setup(self) -> None:
        pass

    @abstractmethod
    async def teardown(self) -> None:
        pass

    @abstractmethod
    def create_parsers(
        self, targets: list[ParseTarget], stop_markers: list[str]
    ) -> Iterator[BaseAsyncParser]:
        pass
