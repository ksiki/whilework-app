from typing import Iterator
from urllib.parse import urlparse

from core.config import InternalAPIData, ParseTarget
from factories.base_parser_factory import BaseParserFactory
from parsers.base_async_parser import BaseAsyncParser
from parsers.telegram import TelegramParser
from telethon import TelegramClient
from telethon.network.connection.tcpintermediate import ConnectionTcpIntermediate
from telethon.sessions import StringSession


class TelegramParserFactory(BaseParserFactory):
    def __init__(self, auth_data: dict, internal_api_data: InternalAPIData):
        super().__init__(auth_data, internal_api_data)
        self.client = TelegramClient(
            session=StringSession(self.auth_data.get("TG_SESSION")),
            api_id=self.auth_data.get("TG_API_ID"),
            api_hash=self.auth_data.get("TG_API_HASH"),
            proxy=self._get_format_proxy(),
            connection=ConnectionTcpIntermediate,
        )

    async def setup(self) -> None:
        await self.client.connect()

    async def teardown(self) -> None:
        await self.client.disconnect()

    def create_parsers(
        self, targets: list[ParseTarget], stop_markers: list[str]
    ) -> Iterator[BaseAsyncParser]:
        return (
            TelegramParser(
                client=self.client,
                target=target,
                internal_api_data=self.internal_api_data,
                stop_markers=stop_markers,
            )
            for target in targets
        )

    def _get_format_proxy(self) -> tuple:
        proxy_str = self.auth_data.get("PROXY_URL", None)
        if not proxy_str:
            return None

        parsed = urlparse(proxy_str)
        return {
            "proxy_type": "socks5",
            "addr": parsed.hostname,
            "port": parsed.port,
            "rdns": True,
            "username": parsed.username or "",
            "password": parsed.password or "",
        }
