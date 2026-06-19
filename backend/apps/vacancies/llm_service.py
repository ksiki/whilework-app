import json
import logging
from typing import Final

from django.conf import settings
from openai import AsyncOpenAI
from pydantic import ValidationError

from .schemas import CleanVacancySchema

SYSTEM_PROMPT: Final[
    str
] = """Ты — Senior HR Data Engineer и эксперт по извлечению структурированных данных.
Твоя задача: проанализировать сырой текст вакансии и извлечь из него данные строго в формате JSON, соответствующем предоставленной схеме.

ШАГ 1: ВАЛИДАЦИЯ ТЕКСТА (КРИТИЧЕСКИ ВАЖНО)
Сначала проанализируй текст и заполни поля `reasoning` и `is_vacancy`.
- Ставь is_vacancy = true ТОЛЬКО если текст содержит предложение о найме на работу (есть позиция, требования, условия).
- Ставь is_vacancy = false, если это:
  1. Резюме (CV) кандидата.
  2. Реклама курсов, вебинаров, мероприятий.
  3. Новости, статьи, мемы или обсуждения.
  4. Подборка коротких ссылок без детального описания.

ШАГ 2: ИЗВЛЕЧЕНИЕ ДАННЫХ
Если is_vacancy = false, оставь все остальные поля пустыми (null или []).
Если is_vacancy = true, извлеки данные согласно следующим правилам:
  
Правила стандартизации данных (КРИТИЧЕСКИ ВАЖНО):

1. НАВЫКИ (Skills):
- Извлекай ТОЛЬКО hard-skills (языки программирования, фреймворки, базы данных, методологии, софт, инструменты).
- СТРОГО ИГНОРИРУЙ soft-skills! Не добавляй в список такие слова как: "внимательность к деталям", "коммуникабельность", "стрессоустойчивость", "умение работать в команде", "обучаемость", "ответственность" и любые подобные.
- Используй общепринятые, канонические названия технологий. Исправляй опечатки и сленг.
- ПРИМЕРЫ: 
  - "postgres", "postgre" -> "PostgreSQL"
  - "airflow", "air flow" -> "Apache Airflow"
  - "node", "nodejs" -> "Node.js"
  - "k8s" -> "Kubernetes"
- Сохраняй правильный регистр (Python, Docker, CI/CD). Не переводи английские IT-термины на русский.

2. КОМПАНИИ (Company):
- Очищай названия от юридических форм (ООО, ЗАО, Inc., Ltd., LLC).
- Английские бренды, написанные транслитом, возвращай в оригинале ("Сбер" -> "Sber", "Тинькофф" -> "T-Bank").

3. ЛОКАЦИИ (Locations):
- Страны и города пиши строго на русском языке ("Мск" -> "Москва", "USA" -> "США").

4. ОПИСАНИЕ (Description):
- Очисти текст от мусора, эмодзи и маркетинговых призывов.
- Оберни описание в валидный HTML, используя строго только теги: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <br>.

5. ЗАРПЛАТА И ДЕНЬГИ:
- Извлекай только числа ("от 150к" -> 150000).
- Валюту приводи к кодам ISO ("руб", "₽" -> "RUB", "$" -> "USD", "евро" -> "EUR").

6. НЕЯВНЫЕ МЕТРИКИ (Грейд, Опыт, Английский, Формат):
Никогда не оставляй поля пустыми (null), если в тексте есть хоть малейший намек!
- Название вакансии: часто содержит грейд (Senior, Middle).
- Блок "Условия": всегда содержит формат работы (удаленка, офис).
- Конвертируй уровни английского в коды (B1, B2, C1) согласно схеме.

7. ЖЕСТКИЕ ТРЕБОВАНИЯ ПО МЕТРИКАМ:
- Видишь "Senior" — всегда ставь grade: "SEN".
- Видишь "3+ года" — всегда извлекай число (3) в experience_from.
- Видишь "Upper-Intermediate" — всегда ставь english_level: "B2".

8. КОНТАКТЫ (Contacts):
- Извлекай только валидные контакты для связи (Telegram, почта, Discord).
- В поле `details` записывай СТРОГО чистый контакт: юзернейм (например, "@username"), ссылку (например, "t.me/username") или email ("hr@company.com").
- Очищай `details` от лишнего текста, предлогов и фраз вроде "писать сюда", "по всем вопросам".

Если каких-то данных объективно нет в тексте, возвращай null (или пустой массив [] для списков), не придумывай информацию."""


EXAMPLE_INPUT: Final[str] = (
    """Senior Python Developer. Опыт 5 лет. Зп 300к руб. Удаленка. Английский B2. """
    """Ищем внимательного к деталям сотрудника, который знает FastAPI. Писать в тг @hr_kolya или на почту job@work.ru"""
)

EXAMPLE_OUTPUT: Final[str] = {
    "reasoning": "Это вакансия, так как есть должность, требования и условия.",
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
        {"platform": "TG", "details": "@hr_kolya"},
        {"platform": "EM", "details": "job@work.ru"},
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
    schema_definition = json.dumps(
        CleanVacancySchema.model_json_schema(), ensure_ascii=False
    )

    system_content = f"{SYSTEM_PROMPT}\n\nСтруктура ответа должна соответствовать схеме: {schema_definition}"

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_content},
                {
                    "role": "user",
                    "content": "Вот пример того, как нужно извлекать данные:",
                },
                {"role": "user", "content": EXAMPLE_INPUT},
                {
                    "role": "assistant",
                    "content": json.dumps(EXAMPLE_OUTPUT, ensure_ascii=False),
                },
                {
                    "role": "user",
                    "content": f"Теперь проанализируй эту вакансию:\n\n{raw_text}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        raw_json_string = response.choices[0].message.content

        clean_data = CleanVacancySchema.model_validate_json(raw_json_string)
        return clean_data

    except ValidationError as e:
        logger.error(
            f"Pydantic Validation Error: LLM вернула кривой JSON. Ошибка: {e}\nСырой ответ LLM: {raw_json_string}"
        )
        return None
    except Exception as e:
        logger.error(f"DeepSeek API Error: {str(e)}")
        return None
