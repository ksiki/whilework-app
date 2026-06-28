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
- Ставь is_vacancy = true ТОЛЬКО при одновременном выполнении двух условий:
  1. Текст содержит предложение о найме на работу (есть позиция, требования, условия).
  2. В тексте есть ХОТЯ БЫ ОДИН контакт для отклика (любой: ссылка, юзернейм, почта, телефон).
  3. ЦЕЛЕВАЯ СФЕРА: Профессия относится к интеллектуальному труду, цифровой экономике, удаленка или медиа-производству. Допустимые сферы: IT (разработка, QA, DevOps, Data Science), Digital, Маркетинг, SMM, Управление персоналом (HR/Рекрутинг), Аналитика, Дизайн, Менеджмент, а также КОНТЕНТ И МЕДИА (контент-мейкеры, видеомонтажеры, саунд-дизайнеры, сценаристы).
- Ставь is_vacancy = false, если это:
  1. Резюме (CV) кандидата.
  2. Реклама курсов, вебинаров, мероприятий.
  3. Новости, статьи, мемы или обсуждения.
  4. Подборка коротких ссылок без детального описания.
  5. Вакансия БЕЗ контактов (вообще нет никаких контактных данных для отклика).
  6. ОФФЛАЙН/ФИЗИЧЕСКИЙ ТРУД: Вакансия относится к сфере классического оффлайна, физического труда, логистики или сферы бытовых услуг. СТРОГО ОТКЛОНЯЙ вакансии: водитель, таксист, повар, официант, строитель, грузчик, кассир, продавец в магазине, охранник, курьер.
В поле `reasoning` обязательно обоснуй свое решение, явно указав, какие контакты найдены или констатировав их отсутствие.

ШАГ 2: ИЗВЛЕЧЕНИЕ ДАННЫХ
Если is_vacancy = false, оставь все остальные поля пустыми (null или []).
Если is_vacancy = true, извлеки данные согласно следующим правилам:
  
Правила стандартизации данных (КРИТИЧЕСКИ ВАЖНО):

1. НАВЫКИ (Skills):
- Извлекай ТОЛЬКО hard-skills (языки программирования, фреймворки, базы данных, инструменты).
- СТРОГО ИГНОРИРУЙ soft-skills! Не добавляй: "внимательность", "коммуникабельность", "ответственность".
- Используй канонические названия. ОБЯЗАТЕЛЬНО переводи русскоязычные термины на английский (например: "а/б тестирование" -> "A/B Testing", "базы данных" -> "Databases").
- УДАЛЯЙ версии технологий, если это не самостоятельный фреймворк (например: ".NET 6", ".NET Core" -> ".NET", "PostgreSQL 14" -> "PostgreSQL", но "Vue 3" -> "Vue.js").
- ПРИМЕРЫ:
  - "postgres", "postgre" -> "PostgreSQL"
  - "k8s" -> "Kubernetes"
  - "1с-битрикс" -> "1C-Bitrix"
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
- Извлекай ВСЕ найденные контакты для связи КАК ЕСТЬ.
- В поле `details` записывай сырой контакт именно в том виде, в котором он указан в тексте (полная ссылка, юзернейм, email, телефон). Не пытайся самостоятельно его форматировать или очищать от доменов.

Если каких-то данных объективно нет в тексте, возвращай null (или пустой массив [] для списков), НЕ ПРИДУМЫВАЙ ИНФОРМАЦИЮ."""


EXAMPLE_INPUT: Final[str] = (
    """Senior Python Developer. Опыт 5 лет. Зп 300к руб. Удаленка. Английский B2. """
    """Ищем внимательного к деталям сотрудника, который знает FastAPI. Писать в тг https://t.me/hr_kolya или заполняйте форму https://forms.yandex.ru/u/12345/"""
)

EXAMPLE_OUTPUT: Final[dict] = {
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
