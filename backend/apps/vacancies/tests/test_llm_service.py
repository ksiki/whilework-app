from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from apps.vacancies.llm_service import extract_vacancy_data


class _DummyModel(BaseModel):
    x: int


def _get_validation_error():
    try:
        _DummyModel(x="invalid")
    except ValidationError as e:
        return e


@pytest.mark.asyncio
@patch("apps.vacancies.llm_service.CleanVacancySchema")
@patch(
    "apps.vacancies.llm_service.client.chat.completions.create", new_callable=AsyncMock
)
async def test_extract_vacancy_data_success(mock_create, mock_schema):
    mock_schema.model_json_schema.return_value = {"type": "object"}

    mock_clean_data = MagicMock()
    mock_schema.model_validate_json.return_value = mock_clean_data

    mock_message = MagicMock()
    mock_message.content = '{"is_vacancy": true}'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response

    result = await extract_vacancy_data("test raw text")

    assert result == mock_clean_data
    mock_create.assert_awaited_once()
    mock_schema.model_validate_json.assert_called_once_with('{"is_vacancy": true}')


@pytest.mark.asyncio
@patch("apps.vacancies.llm_service.CleanVacancySchema")
@patch(
    "apps.vacancies.llm_service.client.chat.completions.create", new_callable=AsyncMock
)
async def test_extract_vacancy_data_validation_error(mock_create, mock_schema):
    mock_schema.model_json_schema.return_value = {"type": "object"}
    mock_schema.model_validate_json.side_effect = _get_validation_error()

    mock_message = MagicMock()
    mock_message.content = '{"invalid": "data"}'
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_create.return_value = mock_response

    result = await extract_vacancy_data("test raw text")

    assert result is None


@pytest.mark.asyncio
@patch("apps.vacancies.llm_service.CleanVacancySchema")
@patch(
    "apps.vacancies.llm_service.client.chat.completions.create", new_callable=AsyncMock
)
async def test_extract_vacancy_data_api_error(mock_create, mock_schema):
    mock_schema.model_json_schema.return_value = {"type": "object"}
    mock_create.side_effect = Exception("API connection failed")

    result = await extract_vacancy_data("test raw text")

    assert result is None
