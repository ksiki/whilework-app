import json
import logging
from typing import Final

from django.conf import settings
from openai import AsyncOpenAI
from pydantic import ValidationError

from .schemas import CleanVacancySchema

SYSTEM_PROMPT: Final[
    str
] = """Ты — Senior HR Data Engineer. Твоя задача: извлечь структурированные данные из вакансии в JSON по схеме.

ШАГ 1: ВАЛИДАЦИЯ (is_vacancy)
- true ТОЛЬКО при выполнении ДВУХ условий:
  1. Это найм (IT, Digital, медиа, удаленка).
  2. Есть ХОТЯ БЫ ОДИН ЯВНЫЙ контакт (ссылка, @юзернейм, email, телефон). "Пишите в ЛС" без указания самого контакта — НЕ контакт.
- false если: это резюме, курсы, новости, оффлайн/физ. труд (водитель, грузчик, официант) или нет явных контактов.
Обоснуй в `reasoning`.

ШАГ 2: ИЗВЛЕЧЕНИЕ (если is_vacancy = true)
- НАВЫКИ: Только hard-skills. Переводи на английский ("postgres" -> "PostgreSQL", "k8s" -> "Kubernetes", "1с-битрикс" -> "1C-Bitrix"). Сохраняй регистр. Убирай версии (Vue 3 -> Vue.js). СТРОГО игнорируй soft-skills.
- КОМПАНИИ: Очищай от форм собственности (ООО, Inc., Ltd). Английские бренды транслитом верни в оригинал ("Сбер" -> "Sber").
- ЛОКАЦИИ: Страны и города строго на русском ("USA" -> "США").
- ОПИСАНИЕ: Очисти от эмодзи. Используй HTML теги, указанные в схеме.
- МЕТРИКИ: Ищи маркеры в тексте (Senior -> SEN, "3+ года" -> experience_from: 3). Зарплата — только числа, валюта — ISO (RUB, USD).
- КОНТАКТЫ: Извлекай КАК ЕСТЬ. Написано только "в ЛС" без юзернейма -> [].

Если данных объективно нет — возвращай null (или []). НЕ придумывай от себя."""


EXAMPLE_INPUT: Final[str] = (
    "Senior Python Developer. Опыт 5 лет. Зп 300к руб. Удаленка. Английский B2. "
    "Ищем внимательного к деталям сотрудника, который знает FastAPI. Писать в тг https://t.me/hr_kolya или заполняйте форму https://forms.yandex.ru/u/12345/"
)

EXAMPLE_OUTPUT: Final[dict] = {
    "reasoning": "Это вакансия: есть позиция в IT, требования и явные контакты для связи.",
    "is_vacancy": True,
    "title": "Python Developer",
    "grade": "SEN",
    "experience_from": 5,
    "salary_min": 300000,
    "currency": "RUB",
    "work_format": "RMT",
    "english_level": "B2",
    "skills": ["Python", "FastAPI"],
    "contacts": [
        {"platform": "TG", "details": "https://t.me/hr_kolya"},
        {"platform": "FR", "details": "https://forms.yandex.ru/u/12345/"},
    ],
}


logger = logging.getLogger(__name__)

client = AsyncOpenAI(
    api_key=settings.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=60.0,
    max_retries=3,
)


async def extract_vacancy_data(raw_text: str) -> CleanVacancySchema | None:
    schema_definition = CleanVacancySchema.model_json_schema()
    schema_str = json.dumps(schema_definition, ensure_ascii=False)

    system_content = f"{SYSTEM_PROMPT}\n\nСхема JSON:\n{schema_str}"

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": "Пример входа:"},
                {"role": "user", "content": EXAMPLE_INPUT},
                {
                    "role": "assistant",
                    "content": json.dumps(EXAMPLE_OUTPUT, ensure_ascii=False),
                },
                {"role": "user", "content": f"Проанализируй вакансию:\n\n{raw_text}"},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_json_string = response.choices[0].message.content
        return CleanVacancySchema.model_validate_json(raw_json_string)

    except ValidationError as e:
        logger.error(
            f"Pydantic Validation Error: LLM вернула кривой JSON. Ошибка: {e}\n"
            f"Сырой ответ LLM: {raw_json_string}"
        )
        return None
    except Exception as e:
        logger.error(f"DeepSeek API Error: {str(e)}")
        return None
