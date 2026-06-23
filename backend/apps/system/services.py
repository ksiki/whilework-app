import logging
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from .models import Currency

logger = logging.getLogger(__name__)


def convert_to_usd(amount: int | Decimal | float, iso_code: str) -> Decimal | None:
    try:
        amount_dec = Decimal(str(amount))
        currency = Currency.objects.get(iso=iso_code)

        if currency.currency_rate == 0:
            logger.error(f"Conversion failed: Rate for {iso_code} is zero.")
            return None

        result = amount_dec / currency.currency_rate
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Currency.DoesNotExist:
        logger.error(f"Conversion failed: Currency {iso_code} does not exist.")
        return None
    except (ZeroDivisionError, InvalidOperation) as e:
        logger.error(f"Conversion failed for {iso_code} with amount {amount}: {e}")
        return None
