import logging

from .models import Currency

logger = logging.getLogger(__name__)


def convert_to_usd(amount: int, iso_code: str) -> int | None:
    try:
        currency = Currency.objects.get(iso=iso_code)
        return amount // currency.currency_rate
    except (Currency.DoesNotExist, ZeroDivisionError) as e:
        logger.error(f"Converted to usd failed: {e}")
        return None
