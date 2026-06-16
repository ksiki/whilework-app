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
  1. Резюме (CV) кандидата, который ищет работу (маркеры: "ищу работу", "мой опыт").
  2. Реклама ИТ-курсов, вебинаров, конференций.
  3. Новости, статьи, мемы или личные обсуждения.
  4. Подборка из множества коротких ссылок без детального описания.

ШАГ 2: ИЗВЛЕЧЕНИЕ ДАННЫХ
Если is_vacancy = false, оставь все остальные поля пустыми (null или []).
Если is_vacancy = true, извлеки данные согласно следующим правилам:
  
Правила стандартизации данных (КРИТИЧЕСКИ ВАЖНО):

1. НАВЫКИ (Skills):
- Используй только общепринятые, канонические названия технологий.
- Исправляй опечатки и сленг.
- ПРИМЕРЫ: 
  - "postgres", "postgre" -> "PostgreSQL"
  - "airflow", "air flow" -> "Apache Airflow"
  - "node", "nodejs" -> "Node.js"
  - "react js", "react.js" -> "React"
  - "k8s" -> "Kubernetes"
- Все навыки должны быть написаны с правильным регистром (Python, Docker, CI/CD). Не переводи английские термины на русский.

2. КОМПАНИИ (Company):
- Очищай названия от юридических форм (ООО, ЗАО, Inc., Ltd., LLC).
- Если название написано транслитом или по-русски, но бренд английский, пиши оригинальный бренд.
- ПРИМЕР: "ООО Яндекс" -> "Yandex", "Сбер" -> "Sber", "Тинькофф" -> "T-Bank".

3. ЛОКАЦИИ (Locations):
- Страны и города пиши строго на русском языке.
- ПРИМЕР: "Мск" -> "Москва", "СПб" -> "Санкт-Петербург", "USA" -> "США", "РФ" -> "Росиия", "ЕС" -> "Европа", "СНГ" -> "СНГ".

4. ОПИСАНИЕ (Description):
- Очисти текст от мусора, эмодзи и призывов в духе "Жми сюда".
- Оберни описание в валидный HTML, используя только теги: <p>, <h2>, <h3>, <ul>, <li>, <strong>, <br>.

5. ЗАРПЛАТА И ДЕНЬГИ:
- Извлекай только числа. "от 150к" -> 150000.
- Валюту приводи к кодам ISO: "руб", "₽" -> "RUB", "$" -> "USD", "евро" -> "EUR".

6. НЕЯВНЫЕ МЕТРИКИ (Грейд, Опыт, Английский, Формат):
Никогда не оставляй эти поля пустыми (null), если в тексте есть хоть малейший намек на них!
- Внимательно читай Название вакансии (Title): часто грейд (Senior, Middle) указан именно там.
- Внимательно читай блок "Условия" или "Мы предлагаем": там всегда скрыт формат работы (удаленка, офис).
- Конвертируй текстовые уровни английского в коды (B1, B2, C1) согласно описанию схемы.

7. ЖЕСТКИЕ ТРЕБОВАНИЯ ПО МЕТРИКАМ:
- Если ты видишь в тексте "Senior" — всегда ставь grade: "SEN".
- Если ты видишь "3+ года" или аналогичные конструкции — всегда извлекай число (3) в experience_from.
- Если ты видишь "Upper-Intermediate" — всегда ставь english_level: "B2".
- Не пропускай эти данные, даже если они указаны неявно или в заголовке!

Если каких-то данных в тексте нет, возвращай null (или пустой массив [] для списков), не придумывай информацию."""


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

    example_input = (
        "Senior Python Developer. Опыт 5 лет. Зп 300к руб. Удаленка. Английский B2."
    )
    example_output = {
        "reasoning": "Это вакансия, так как есть должность, требования и условия.",
        "is_vacancy": True,
        "title": "Python Developer",
        "grade": "SEN",
        "experience_from": 5,
        "salary_min": 300000,
        "currency": "RUB",
        "work_format": "RMT",
        "english_level": "B2",
        "skills": ["Python"],
    }

    try:
        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_content},
                {
                    "role": "user",
                    "content": "Вот пример того, как нужно извлекать данные:",
                },
                {"role": "user", "content": example_input},
                {
                    "role": "assistant",
                    "content": json.dumps(example_output, ensure_ascii=False),
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
