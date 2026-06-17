import asyncio
import logging
import random
from typing import Final

from core.config import InternalAPIData, ParseData, ParseTarget
from core.exceptions import PlatformNotExistError
from factories.base_parser_factory import BaseParserFactory
from factories.telegram import TelegramParserFactory
from utils.stop_markers import get_markers

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


FACTORIES: Final[dict[str, BaseParserFactory]] = {
    "telegram": TelegramParserFactory,
}


async def main() -> None:
    parse_data = ParseData()
    internal_api = InternalAPIData()
    stop_markers = get_markers()

    try:
        factory_class = FACTORIES[parse_data.platform]
    except Exception:
        raise PlatformNotExistError(f"Platform {parse_data.platform} is not supported")

    factory = factory_class(
        auth_data=parse_data.auth_data, internal_api_data=internal_api
    )
    parse_targets: list[ParseTarget] = []

    for src_dict in parse_data.sources_batch:
        source_id = str(src_dict.get("SOURCE_ID"))
        identifier = str(src_dict.get("IDENTIFIER"))
        topics = src_dict.get("TOPICS", [])

        if topics:
            for topic in topics:
                parse_targets.append(
                    ParseTarget(
                        source_id=source_id,
                        identifier=identifier,
                        topic_uuid=str(topic.get("id")),
                        topic_id=str(topic.get("topic_id")),
                        last_parsed_id=str(topic.get("LAST_PARSED_ID") or ""),
                    )
                )
        else:
            parse_targets.append(
                ParseTarget(
                    source_id=source_id,
                    identifier=identifier,
                    topic_uuid=None,
                    topic_id=None,
                    last_parsed_id=str(src_dict.get("LAST_PARSED_ID") or ""),
                )
            )

    try:
        await factory.setup()
        parsers = factory.create_parsers(parse_targets, stop_markers)

        sem = asyncio.Semaphore(1)

        async def _safe_run(parser):
            async with sem:
                await asyncio.sleep(random.uniform(2.0, 5.0))
                await parser.run()

        async with asyncio.TaskGroup() as tg:
            for parser in parsers:
                tg.create_task(_safe_run(parser))
    except Exception as e:
        logger.error(f"Parse error, e:{e}")
        raise RuntimeError(f"Parse error, e:{e}")
    finally:
        await factory.teardown()


if __name__ == "__main__":
    asyncio.run(main())
