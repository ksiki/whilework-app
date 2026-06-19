import uuid
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from .services import (
    create_suggest,
    get_liked_suggest_ids,
    get_production_logs,
    get_suggests,
    like_suggest,
)


class TestGetProductionLogs:
    @patch("apps.community.services.ProductionLog")
    @patch("apps.community.services._get_page")
    def test_get_production_logs_success(self, mock_get_page, mock_production_log):
        mock_page = MagicMock()
        mock_page.paginator.num_pages = 2
        mock_page.object_list = ["log1", "log2"]
        mock_get_page.return_value = mock_page

        result = get_production_logs(1)

        assert result == ["log1", "log2"]
        mock_get_page.assert_called_once()

    def test_get_production_logs_invalid_page(self):
        assert get_production_logs(0) is None
        assert get_production_logs(-5) is None

    @patch("apps.community.services.ProductionLog")
    @patch("apps.community.services._get_page")
    def test_get_production_logs_out_of_bounds(
        self, mock_get_page, mock_production_log
    ):
        mock_page = MagicMock()
        mock_page.paginator.num_pages = 1
        mock_get_page.return_value = mock_page

        assert get_production_logs(2) is None


class TestGetSuggests:
    @patch("apps.community.services.Suggest")
    @patch("apps.community.services._get_page")
    def test_get_suggests_new_success(self, mock_get_page, mock_suggest):
        mock_page = MagicMock()
        mock_page.paginator.num_pages = 2
        mock_page.object_list = ["suggest1", "suggest2"]
        mock_get_page.return_value = mock_page

        result = get_suggests(1, "new")

        assert result == ["suggest1", "suggest2"]
        mock_suggest.objects.filter.assert_called_once_with(
            status__in=["NEW", "PLN", "RVW"]
        )

    def test_get_suggests_invalid_page(self):
        assert get_suggests(0, "new") is None

    def test_get_suggests_invalid_order_by(self):
        assert get_suggests(1, "unknown_order") is None

    @patch("apps.community.services.Suggest")
    @patch("apps.community.services._get_page")
    def test_get_suggests_out_of_bounds(self, mock_get_page, mock_suggest):
        mock_page = MagicMock()
        mock_page.paginator.num_pages = 1
        mock_get_page.return_value = mock_page

        assert get_suggests(5, "popular") is None


class TestGetLikedSuggestIds:
    def test_get_liked_suggest_ids_unauthenticated(self):
        mock_user = Mock()
        mock_user.is_authenticated = False

        result = get_liked_suggest_ids(mock_user, ["suggest1"])

        assert result == []

    def test_get_liked_suggest_ids_empty_suggests(self):
        mock_user = Mock()
        mock_user.is_authenticated = True

        result = get_liked_suggest_ids(mock_user, [])

        assert result == []

    def test_get_liked_suggest_ids_success(self):
        mock_user = Mock()
        mock_user.is_authenticated = True

        mock_suggest = Mock()
        mock_suggest.id = uuid.uuid4()

        mock_filter = mock_user.liked_suggests.filter.return_value
        mock_filter.values_list.return_value = [mock_suggest.id]

        result = get_liked_suggest_ids(mock_user, [mock_suggest])

        assert result == [mock_suggest.id]
        mock_user.liked_suggests.filter.assert_called_once_with(
            id__in=[mock_suggest.id]
        )


@pytest.mark.asyncio
class TestLikeSuggest:
    @patch("apps.community.services.Suggest")
    async def test_like_suggest_add_like(self, mock_suggest_model):
        suggest_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_suggest = MagicMock()
        mock_suggest_model.objects.aget = AsyncMock(return_value=mock_suggest)

        mock_filter_qs = MagicMock()
        mock_filter_qs.aexists = AsyncMock(return_value=False)
        mock_suggest.liked_by.filter.return_value = mock_filter_qs

        mock_suggest.liked_by.aadd = AsyncMock()

        mock_objects_filter_qs = MagicMock()
        mock_objects_filter_qs.aupdate = AsyncMock()
        mock_suggest_model.objects.filter.return_value = mock_objects_filter_qs

        result = await like_suggest(suggest_id, user_id)

        assert result is True
        mock_suggest.liked_by.aadd.assert_awaited_once_with(user_id)
        mock_suggest_model.objects.filter.assert_called_once_with(id=suggest_id)

    @patch("apps.community.services.Suggest")
    async def test_like_suggest_remove_like(self, mock_suggest_model):
        suggest_id = uuid.uuid4()
        user_id = uuid.uuid4()

        mock_suggest = MagicMock()
        mock_suggest_model.objects.aget = AsyncMock(return_value=mock_suggest)

        mock_filter_qs = MagicMock()
        mock_filter_qs.aexists = AsyncMock(return_value=True)
        mock_suggest.liked_by.filter.return_value = mock_filter_qs

        mock_suggest.liked_by.aremove = AsyncMock()

        mock_objects_filter_qs = MagicMock()
        mock_objects_filter_qs.aupdate = AsyncMock()
        mock_suggest_model.objects.filter.return_value = mock_objects_filter_qs

        result = await like_suggest(suggest_id, user_id)

        assert result is True
        mock_suggest.liked_by.aremove.assert_awaited_once_with(user_id)
        mock_suggest_model.objects.filter.assert_called_once_with(id=suggest_id)

    @patch("apps.community.services.Suggest")
    async def test_like_suggest_exception(self, mock_suggest_model):
        mock_suggest_model.objects.aget = AsyncMock(side_effect=Exception("DB Error"))

        result = await like_suggest(uuid.uuid4(), uuid.uuid4())

        assert result is False


@pytest.mark.asyncio
class TestCreateSuggest:
    @patch("apps.community.services.Suggest")
    async def test_create_suggest_success(self, mock_suggest_model):
        user_id = uuid.uuid4()
        mock_payload = Mock()
        mock_payload.title = " Valid Title "
        mock_payload.description = " Valid Description "

        mock_suggest_model.Status.MODERATION = "MODERATION"
        mock_suggest_model.objects.acreate = AsyncMock()

        result = await create_suggest(user_id, mock_payload)

        assert result is True
        mock_suggest_model.objects.acreate.assert_awaited_once_with(
            status="MODERATION",
            author_id=user_id,
            title="Valid Title",
            description="Valid Description",
        )

    async def test_create_suggest_empty_title(self):
        user_id = uuid.uuid4()
        mock_payload = Mock()
        mock_payload.title = "   "
        mock_payload.description = "Valid Description"

        result = await create_suggest(user_id, mock_payload)

        assert result is False

    @patch("apps.community.services.Suggest")
    async def test_create_suggest_exception(self, mock_suggest_model):
        user_id = uuid.uuid4()
        mock_payload = Mock()
        mock_payload.title = "Valid Title"
        mock_payload.description = "Valid Description"

        mock_suggest_model.objects.acreate = AsyncMock(
            side_effect=Exception("DB Error")
        )

        result = await create_suggest(user_id, mock_payload)

        assert result is False
