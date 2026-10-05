import secrets
from datetime import timedelta
from django.utils import timezone
from .models import PhoneVerification

def generate_otp():
    return f"{secrets.randbelow(1000000):06d}"


def can_request_phone_verification(user,purpose="change_phone",cooldown_seconds=60):
    last_verification = (
        PhoneVerification.objects
        .filter(user=user,purpose=purpose)
        .order_by("-created_at")
        .first()
    )

    if not last_verification:
        return True

    elapsed = timezone.now() - last_verification.created_at

    return elapsed.total_seconds() >= cooldown_seconds



def create_phone_verification(user,phone_number,purpose):

    if user:
        PhoneVerification.objects.filter(
                user=user,
                is_verified = False
            ).update(is_verified = True)
        
    else:

        PhoneVerification.objects.filter(
            user__isnull=True,
            phone_number=phone_number,
            is_verified=False
        ).update(is_verified=True)

        
    code = generate_otp()

    verification = PhoneVerification.objects.create(
        user=user,
        phone_number=phone_number,
        code=code,
        purpose=purpose,
        expires_at = timezone.now()+timedelta(minutes=2),
    )

    return verification