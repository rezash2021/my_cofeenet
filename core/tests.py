from django.test import TestCase
from django.contrib.auth.models import User
from .utils import generate_otp,create_phone_verification


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