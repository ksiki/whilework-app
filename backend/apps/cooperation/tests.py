import pytest

from .api.schemas import CreateMessageRequest
from .models import Message
from .services import process_cooperation_offer


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_process_cooperation_offer_success():
    payload = CreateMessageRequest(
        name="Иван Иванов",
        email="test@example.com",
        message="Тестовый текст на 50+ симоволов. Сотрудничество на 1_000_000$",
    )

    result = await process_cooperation_offer(payload)

    assert isinstance(result, Message)
    assert result.name == "Иван Иванов"
    assert result.email == "test@example.com"
    assert (
        result.text == "Тестовый текст на 50+ симоволов. Сотрудничество на 1_000_000$"
    )

    exists = await Message.objects.filter(id=result.id).aexists()
    assert exists is True
