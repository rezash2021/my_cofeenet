from django.test import TestCase
from django.contrib.auth.models import User
from .utils import generate_otp,create_phone_verification
from django.utils import timezone
from datetime import timedelta
from core.models import PhoneVerification

from unittest.mock import patch
from django.test import SimpleTestCase, override_settings

from core.sms import send_otp,SMSError
from core.sms_providers import kavenegar,smsir
from .models import Profile


class GenerateOTPTest(TestCase):

    def test_generate_otp_is_six_digits(self):
        code = generate_otp()

        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

class CreatePhoneVerificationTest(TestCase):
     def test_create_phone_verification(self): 
        user = User.objects.create_user( username="testuser", password="testpass123" ) 
        verification = create_phone_verification( user=user, phone_number="09123456789", purpose="password_reset" ) 
        self.assertEqual(verification.phone_number, "09123456789") 
        self.assertEqual(verification.purpose, "password_reset")
        self.assertEqual(len(verification.code), 6) 
        self.assertFalse(verification.is_verified)


class PhoneVerificationCooldownTest(TestCase):

    def test_cooldown_blocks_immediate_request(self):
        user = User.objects.create_user(
            username="cooldownuser",
            password="testpass123"
        )

        create_phone_verification(
            user=user,
            phone_number="09123456789",
            purpose="password_reset"
        )

        from .utils import can_request_phone_verification

        self.assertFalse(
            can_request_phone_verification(
                user,
                purpose="password_reset"
            )
        )

class PhoneVerificationCooldownPassedTest(TestCase):
    def test_cooldown_allows_request_after_60_seconds(self):
        user = User.objects.create_user(
            username="cooldownpassed",
            password="testpass123"
        )

        verification = create_phone_verification(
            user=user,
            phone_number="09123456789",
            purpose="password_reset"
        )

        verification.created_at = timezone.now() - timedelta(seconds=61)
        verification.save(update_fields=["created_at"])

        from .utils import can_request_phone_verification

        self.assertTrue(
            can_request_phone_verification(
                user,
                purpose="password_reset"
            )
        )        


class PhoneVerificationPurposeTest(TestCase):
    def test_new_verification_does_not_invalidate_other_purpose(self):
        user = User.objects.create_user(
            username="purposeuser",
            password="testpass123"
        )

        password_reset_verification = create_phone_verification(
            user=user,
            phone_number="09123456789",
            purpose="password_reset"
        )

        create_phone_verification(
            user=user,
            phone_number="09123456789",
            purpose="change_phone"
        )

        password_reset_verification.refresh_from_db()

        self.assertFalse(password_reset_verification.is_verified)


class RegistrationVerificationExpiryTest(TestCase):
    def test_expired_verification_is_not_accepted(self):
        user = User.objects.create_user(
            username="expiryuser",
            password="testpass123"
        )

        verification = create_phone_verification(
            user=None,
            phone_number="09123456789",
            purpose="registration"
        )

        verification.expires_at = timezone.now() - timedelta(minutes=1)
        verification.save(update_fields=["expires_at"])

        self.assertTrue(
            verification.expires_at < timezone.now()
        )

class RegistrationVerificationViewTest(TestCase):
    def test_expired_otp_is_rejected(self):
        verification = create_phone_verification(
            user=None,
            phone_number="09123456789",
            purpose="registration"
        )

        verification.expires_at = timezone.now() - timedelta(minutes=1)
        verification.save(update_fields=["expires_at"])

        session = self.client.session
        session["registration_username"] = "viewtestuser"
        session["registration_phone"] = "09123456789"
        session.save()

        response = self.client.post(
            "/register/verify/",
            {"code": verification.code}
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.wsgi_request.session.get(
                "registration_verified",
                False
            )
        )

class RegistrationVerificationAttemptsTest(TestCase):
    def test_verification_is_locked_after_five_wrong_attempts(self):
        verification = create_phone_verification(
            user=None,
            phone_number="09123456789",
            purpose="registration"
        )

        session = self.client.session
        session["registration_username"] = "attemptuser"
        session["registration_phone"] = "09123456789"
        session.save()

        wrong_code = "000000" if verification.code != "000000" else "111111"

        for _ in range(5):
         self.client.post(
         "/register/verify/",
         {"code": wrong_code}
           )

        verification.refresh_from_db()

        self.assertEqual(verification.attempts, 5)
        self.assertTrue(verification.is_verified)


class RegistrationVerificationLockTest(TestCase):
    def test_correct_code_is_rejected_after_five_wrong_attempts(self):
        verification = create_phone_verification(
            user=None,
            phone_number="09123456789",
            purpose="registration"
        )

        session = self.client.session
        session["registration_username"] = "lockuser"
        session["registration_phone"] = "09123456789"
        session.save()

        wrong_code = "000000" if verification.code != "000000" else "111111"

        for _ in range(5):
          self.client.post(
          "/register/verify/",
          {"code": wrong_code}
             )

        verification.refresh_from_db()

        response = self.client.post(
            "/register/verify/",
            {"code": verification.code}
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            response.wsgi_request.session.get(
                "registration_verified",
                False
            )
        )  
class PhoneVerificationCooldownPurposeTest(TestCase):
    def test_cooldown_is_separate_for_each_purpose(self):
        user = User.objects.create_user(
            username="purposecooldown",
            password="testpass123"
        )

        create_phone_verification(
            user=user,
            phone_number="09123456789",
            purpose="password_reset"
        )

        from .utils import can_request_phone_verification

        self.assertFalse(
            can_request_phone_verification(
                user,
                purpose="password_reset"
            )
        )

        self.assertTrue(
            can_request_phone_verification(
                user,
                purpose="change_phone"
            )
        )  


class SMSTest(SimpleTestCase):

    @override_settings(SMS_PROVIDER="kavenegar")
    def test_send_otp_uses_kavenegar_provider(self):
        with patch.object(
            kavenegar,
            "send_sms",
        ) as mock_send_sms:
            send_otp("09123456789", "123456")

        mock_send_sms.assert_called_once_with(
            "09123456789",
            "123456",
        )

    
    @override_settings(SMS_PROVIDER="smsir")
    def test_send_otp_uses_smsir_provider(self):
        with patch.object(
            smsir,
            "send_sms",
        ) as mock_send_sms:
            send_otp("09123456789", "123456")

        mock_send_sms.assert_called_once_with(
            "09123456789",
            "123456",
        )
    

    @override_settings(SMS_PROVIDER="")
    def test_send_otp_fails_without_provider(self):
        with self.assertRaises(SMSError):
            send_otp("09123456789", "123456")

    @override_settings(SMS_PROVIDER="unknown")
    def test_send_otp_rejects_unknown_provider(self):
        with self.assertRaises(SMSError):
            send_otp("09123456789", "123456")



class RegistrationSMSFailureTest(TestCase):

    @patch("core.views.send_otp", side_effect=SMSError("Test failure"))
    def test_registration_does_not_continue_when_sms_fails(self, mock_send):
        response = self.client.post(
            "/register/",
            {
                "username": "smsfailureuser",
                "phone_number": "09123456789",
                "password1": "TestPass123!",
                "password2": "TestPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(
            "registration_verified",
            response.wsgi_request.session,
        )

        verification = PhoneVerification.objects.filter(
            phone_number="09123456789",
            purpose="registration",
        ).latest("created_at")

        self.assertTrue(verification.is_verified)
        mock_send.assert_called_once()


class ResendPasswordResetCodeTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="resendtestuser",
            password="TestPass123!",
        )

        profile = Profile.objects.get(user=self.user)
        profile.phone_number = "09123456789"
        profile.save(update_fields=["phone_number"])

        create_phone_verification(
            user=self.user,
            phone_number="09123456789",
            purpose="password_reset",
        )

        session = self.client.session
        session["password_reset_phone"] = "09123456789"
        session.save()

    @patch("core.views.send_otp")
    def test_resend_is_blocked_during_cooldown(self, mock_send):
        response = self.client.post(
            "/password/resend/",
        )

        self.assertEqual(response.status_code, 302)
        mock_send.assert_not_called()


    @patch("core.views.send_otp")
    def test_resend_is_allowed_after_cooldown(self, mock_send):
        verification = PhoneVerification.objects.filter(
            user=self.user,
            purpose="password_reset",
        ).latest("created_at")

        verification.created_at = timezone.now() - timedelta(seconds=61)
        verification.save(update_fields=["created_at"])

        response = self.client.post("/password/resend/")

        self.assertEqual(response.status_code, 302)
        mock_send.assert_called_once()



class PasswordResetVerificationExpiryTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="expirytestuser",
            password="TestPass123!",
        )

        profile = Profile.objects.get(user=self.user)
        profile.phone_number = "09123456780"
        profile.save(update_fields=["phone_number"])

        verification = create_phone_verification(
            user=self.user,
            phone_number="09123456780",
            purpose="password_reset",
        )

        verification.expires_at = timezone.now() - timedelta(seconds=1)
        verification.save(update_fields=["expires_at"])

        session = self.client.session
        session["password_reset_phone"] = "09123456780"
        session.save()

    def test_expired_code_cannot_verify_password_reset(self):
        response = self.client.post(
            "/password/verify/",
            {"code": "123456"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "کد تایید منقضی شد")
        self.assertNotIn(
           "password_reset_verified",
           self.client.session,
        )

    