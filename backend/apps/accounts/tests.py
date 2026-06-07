from unittest.mock import patch

import pytest
from django.core.cache import cache

from .services import OTPAuthService, get_profile_data


@pytest.mark.django_db
class TestOTPAuthService:
    @patch("apps.accounts.services.send_mail")
    def test_generate_and_send_otp_success(self, mock_send_mail):
        mock_send_mail.return_value = 1  # 1 message seccuess sending
        email = "test@example.com"

        result = OTPAuthService.generate_and_send_otp(email)

        assert result is True
        cached_code = cache.get(f"otp_register_{email}")
        assert cached_code is not None
        assert len(cached_code) == 4
        mock_send_mail.assert_called_once()

    @patch("apps.accounts.services.send_mail")
    def test_generate_and_send_otp_failure(self, mock_send_mail):
        mock_send_mail.side_effect = Exception("SMTP Error")

        result = OTPAuthService.generate_and_send_otp("fail@example.com")

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
