import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist

from .services import (
    CaptchaService,
    OTPAuthService,
    delete_user,
    edit_blacklist,
    get_profile_data,
    mark_notification_as_read,
    update_viewed_vacancies,
)


@pytest.mark.asyncio
@pytest.mark.django_db
class TestOTPAuthService:
    @patch("apps.accounts.services.send_otp_email_task.kiq", new_callable=AsyncMock)
    async def test_generate_and_send_otp_success(self, mock_kiq):
        email = "test@example.com"

        result = await OTPAuthService.generate_and_send_otp(email)

        assert result is True
        cached_code = cache.get(f"otp_register_{email}")
        assert cached_code is not None
        assert len(cached_code) == 4
        mock_kiq.assert_awaited_once_with(email, cached_code)

    @patch("apps.accounts.services.send_otp_email_task.kiq", new_callable=AsyncMock)
    async def test_generate_and_send_otp_failure(self, mock_kiq):
        mock_kiq.side_effect = Exception("TaskIQ/Broker Error")

        result = await OTPAuthService.generate_and_send_otp("fail@example.com")

        assert result is False

    def test_verify_otp_code_success(self):
        email = "test@example.com"
        code = "1234"
        cache.set(f"otp_register_{email}", code, timeout=300)

        result = OTPAuthService.verify_otp_code(email, code)

        assert result is True
        assert cache.get(f"otp_register_{email}") is None

    def test_verify_otp_code_invalid(self):
        email = "test@example.com"
        cache.set(f"otp_register_{email}", "1234", timeout=300)

        result = OTPAuthService.verify_otp_code(email, "9999")

        assert result is False


class TestCaptchaService:
    @patch("requests.post")
    def test_verify_turnstile_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response

        assert CaptchaService.verify_turnstile("valid_token") is True

    @patch("requests.post")
    def test_verify_turnstile_failure(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {"success": False}
        mock_post.return_value = mock_response

        assert CaptchaService.verify_turnstile("invalid_token") is False

    def test_verify_turnstile_empty_token(self):
        assert CaptchaService.verify_turnstile("") is False


@pytest.mark.django_db
def test_get_profile_data(django_user_model):
    user = django_user_model.objects.create_user(
        email="test@user.com", password="password"
    )
    user.available_slots = 5
    user.save()

    profile_data = get_profile_data(user.email)

    assert profile_data["email"] == user.email
    assert profile_data["user_id"] == user.id
    assert profile_data["available_slots"] == 5
    assert "notifications" in profile_data
    assert "blacklist" in profile_data


@pytest.mark.asyncio
class TestEditBlacklist:
    async def test_edit_blacklist_add(self):
        mock_user = Mock()
        mock_user.company_blacklist.aadd = AsyncMock()
        company_id = uuid.uuid4()

        result = await edit_blacklist(
            user=mock_user, company_id=company_id, delete=False
        )

        mock_user.company_blacklist.aadd.assert_awaited_once_with(company_id)
        assert result == "Company added to blacklist"

    async def test_edit_blacklist_remove(self):
        mock_user = Mock()
        mock_user.company_blacklist.aremove = AsyncMock()
        company_id = uuid.uuid4()

        result = await edit_blacklist(
            user=mock_user, company_id=company_id, delete=True
        )

        mock_user.company_blacklist.aremove.assert_awaited_once_with(company_id)
        assert result == "Company removed from blacklist"


class TestMarkNotificationAsRead:
    @patch("apps.accounts.services.timezone")
    @patch("apps.accounts.services.UserNotification")
    def test_mark_notification_as_read_success(
        self, mock_user_notification, mock_timezone
    ):
        user_id = uuid.uuid4()
        notif_id = uuid.uuid4()

        mock_filter = mock_user_notification.objects.filter
        mock_update = mock_filter.return_value.update
        mock_update.return_value = 1
        mock_now = mock_timezone.now.return_value

        mark_notification_as_read(user_id=user_id, notif_id=notif_id)

        mock_filter.assert_called_once_with(user_id=user_id, notification_id=notif_id)
        mock_update.assert_called_once_with(is_read=True, read_at=mock_now)

    @patch("apps.accounts.services.UserNotification")
    def test_mark_notification_as_read_not_found(self, mock_user_notification):
        user_id = uuid.uuid4()
        notif_id = uuid.uuid4()

        mock_update = mock_user_notification.objects.filter.return_value.update
        mock_update.return_value = 0

        with pytest.raises(ObjectDoesNotExist, match="Notification not found"):
            mark_notification_as_read(user_id=user_id, notif_id=notif_id)


@pytest.mark.asyncio
async def test_delete_user_success():
    mock_user = Mock()
    mock_user.check_password.return_value = True
    mock_user.delete = Mock()

    result = await delete_user(mock_user, "correct_password")

    assert result is True
    mock_user.check_password.assert_called_once_with("correct_password")
    mock_user.delete.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_wrong_password():
    mock_user = Mock()
    mock_user.check_password.return_value = False
    mock_user.delete = Mock()

    result = await delete_user(mock_user, "wrong_password")

    assert result is False
    mock_user.check_password.assert_called_once_with("wrong_password")
    mock_user.delete.assert_not_called()


@pytest.mark.asyncio
async def test_update_viewed_vacancies_success():
    mock_user = Mock()
    mock_user.viewed_vacancies.aadd = AsyncMock()
    vacancy_id = uuid.uuid4()

    result = await update_viewed_vacancies(mock_user, vacancy_id)

    assert result is True
    mock_user.viewed_vacancies.aadd.assert_awaited_once_with(vacancy_id)


@pytest.mark.asyncio
async def test_update_viewed_vacancies_failure():
    mock_user = Mock()
    mock_user.viewed_vacancies.aadd = AsyncMock(side_effect=Exception("DB Error"))
    vacancy_id = uuid.uuid4()

    result = await update_viewed_vacancies(mock_user, vacancy_id)

    assert result is False
