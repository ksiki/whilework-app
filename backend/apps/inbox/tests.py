import hashlib
from typing import Any
from unittest.mock import MagicMock, Mock, patch

import pytest
from tests.factories import (
    UUID_1_ID,
    UUID_2_ID,
    UUID_3_ID,
    SourceFactory,
    SourceTopicFactory,
)

from apps.inbox.models import ParserRawMessage
from apps.inbox.services import (
    _create_object_list_and_search_last_ids,
    atomic_saved_messages_and_update_sources,
)
from apps.inbox.tasks import generate_content_hash, process_pending_messages_task
from apps.vacancies.models import Company, Location, Vacancy


@pytest.fixture
def sample_messages_data() -> list[dict[str, Any]]:
    return [
        {
            "source_id": UUID_1_ID,
            "topic_id": UUID_3_ID,
            "external_msg_id": "msg_100",
            "raw_text": "Ищем Python Backend разработчика",
            "metadata": {"author": "HR"},
        },
        {
            "source_id": UUID_1_ID,
            "topic_id": UUID_3_ID,
            "external_msg_id": "msg_101",
            "raw_text": "Вакансия Data Engineer",
            "metadata": {},
        },
        {
            "source_id": UUID_2_ID,
            "topic_id": None,
            "external_msg_id": "post_55",
            "raw_text": "Middle Django Developer",
            "metadata": {"views": 150},
        },
    ]


@pytest.fixture
def setup_sources(db) -> None:
    source_1 = SourceFactory(id=UUID_1_ID, is_active=True)
    SourceTopicFactory(id=UUID_3_ID, source=source_1, is_active=True)

    SourceFactory(id=UUID_2_ID, is_active=True)


def test_create_object_list_and_search_last_ids(sample_messages_data) -> None:
    result = _create_object_list_and_search_last_ids(sample_messages_data)

    assert len(result.instances) == 3
    assert all(isinstance(obj, ParserRawMessage) for obj in result.instances)

    assert result.instances[0].source_id == UUID_1_ID
    assert result.instances[0].topic_id == UUID_3_ID
    assert result.instances[0].external_msg_id == "msg_100"
    assert result.instances[0].raw_text == "Ищем Python Backend разработчика"

    assert dict(result.latest_topic_ids) == {
        UUID_3_ID: "msg_101",
    }
    assert dict(result.latest_source_ids) == {
        UUID_2_ID: "post_55",
    }


@pytest.mark.django_db
@patch("apps.inbox.services.sources_services.update_last_parsed_message_ids")
def test_atomic_saved_messages_and_update_sources(
    mock_update_sources, sample_messages_data, setup_sources
) -> None:
    atomic_saved_messages_and_update_sources(sample_messages_data)

    assert ParserRawMessage.objects.count() == 3

    saved_msg = ParserRawMessage.objects.get(external_msg_id="msg_100")
    assert saved_msg.status == "PND"
    assert saved_msg.source_id == UUID_1_ID
    assert saved_msg.topic_id == UUID_3_ID

    atomic_saved_messages_and_update_sources(sample_messages_data)
    assert ParserRawMessage.objects.count() == 3

    assert mock_update_sources.called

    called_kwargs = mock_update_sources.call_args.kwargs
    assert "source_updates" in called_kwargs
    assert "topic_updates" in called_kwargs

    assert dict(called_kwargs["source_updates"]) == {
        UUID_2_ID: "post_55",
    }
    assert dict(called_kwargs["topic_updates"]) == {
        UUID_3_ID: "msg_101",
    }


def test_generate_content_hash():
    text = "test message"
    result = generate_content_hash(text)
    assert result == hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.mark.django_db
class TestProcessPendingMessagesTask:
    @patch("apps.inbox.tasks.async_to_sync")
    def test_no_pending_messages(self, mock_async_to_sync):
        process_pending_messages_task(5)
        mock_async_to_sync.assert_not_called()

    @patch("apps.inbox.tasks.async_to_sync")
    def test_skip_not_a_vacancy(self, mock_async_to_sync):
        source = SourceFactory()
        msg = ParserRawMessage.objects.create(
            source=source,
            external_msg_id="ext_1",
            raw_text="Just some chat",
            status=ParserRawMessage.Status.PENDING,
            metadata={},
        )

        mock_extractor = Mock()
        mock_data = Mock()
        mock_data.is_vacancy = False
        mock_data.reasoning = "Not a job offer"
        mock_extractor.return_value = mock_data
        mock_async_to_sync.return_value = mock_extractor

        process_pending_messages_task(1)

        msg.refresh_from_db()
        assert msg.status == ParserRawMessage.Status.REJECTED
        assert msg.metadata["reject_reason"] == "Not a job offer"
        assert not Vacancy.objects.exists()

    @patch("apps.inbox.tasks.async_to_sync")
    def test_skip_empty_description(self, mock_async_to_sync):
        source = SourceFactory()
        msg = ParserRawMessage.objects.create(
            source=source,
            external_msg_id="ext_2",
            raw_text="We need someone",
            status=ParserRawMessage.Status.PENDING,
            metadata={},
        )

        mock_extractor = Mock()
        mock_data = Mock()
        mock_data.is_vacancy = True
        mock_data.description = "   "
        mock_extractor.return_value = mock_data
        mock_async_to_sync.return_value = mock_extractor

        process_pending_messages_task(1)

        msg.refresh_from_db()
        assert msg.status == ParserRawMessage.Status.REJECTED
        assert "LLM не смогла извлечь" in msg.metadata["reject_reason"]

    @patch("apps.system.services.convert_to_usd")
    @patch("apps.inbox.tasks.async_to_sync")
    def test_success_vacancy_creation(self, mock_async_to_sync, mock_convert_to_usd):
        mock_convert_to_usd.return_value = 5000

        source = SourceFactory()
        msg = ParserRawMessage.objects.create(
            source=source,
            external_msg_id="ext_3",
            raw_text="Python Django developer wanted",
            status=ParserRawMessage.Status.PENDING,
            metadata={},
        )

        mock_extractor = Mock()
        mock_data = MagicMock()
        mock_data.is_vacancy = True
        mock_data.description = "Awesome job description"
        mock_data.company_name = "WhileWork Inc"
        mock_data.location_region = "EU"
        mock_data.location_country = "Germany"
        mock_data.location_city = "Frankfurt"
        mock_data.title = "Python Backend Developer"
        mock_data.salary_min = 5000
        mock_data.salary_max = 7000
        mock_data.currency = "USD"
        mock_data.experience_from = 2
        mock_data.skills = ["Python", "Django", "Airflow"]

        # Используем валидные короткие ключи БД во избежание DataError
        mock_data.grade = MagicMock(value="MID")
        mock_data.employment_type = MagicMock(value="FLT")
        mock_data.english_level = MagicMock(value="B1")
        mock_data.work_format = MagicMock(value="RMT")

        contact = Mock()
        contact.platform = "TG"
        contact.details = "@kolya_hr"
        mock_data.contacts = [contact]

        mock_extractor.return_value = mock_data
        mock_async_to_sync.return_value = mock_extractor

        process_pending_messages_task(1)

        msg.refresh_from_db()
        assert msg.status == ParserRawMessage.Status.PROCESSED

        assert Company.objects.filter(name="WhileWork Inc").exists()
        assert Location.objects.filter(city="Frankfurt").exists()

        vacancy = Vacancy.objects.get(title="Python Backend Developer")
        assert vacancy.company.name == "WhileWork Inc"
        assert vacancy.usd_salary_min == 5000
        assert vacancy.skills.count() == 3
        assert vacancy.contact.count() == 1
        assert vacancy.contact.first().platform == "TG"

    @patch("apps.inbox.tasks.async_to_sync")
    def test_task_exception_handling(self, mock_async_to_sync):
        source = SourceFactory()
        msg = ParserRawMessage.objects.create(
            source=source,
            external_msg_id="ext_4",
            raw_text="Bad message",
            status=ParserRawMessage.Status.PENDING,
            metadata={},
        )

        mock_async_to_sync.side_effect = Exception("LLM connection error")

        process_pending_messages_task(1)

        msg.refresh_from_db()
        assert msg.status == ParserRawMessage.Status.FAILED
