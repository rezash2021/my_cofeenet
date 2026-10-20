import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSError(Exception):
    """raised when an sms cannot be sent."""

def send_otp(phone_number,code):

    if settings.SMS_DEBUG_MODE and settings.DEBUG:
        logger.info("SMS debug mode is enabled;no real SMS sent.")
        return

    provider_name = settings.SMS_PROVIDER.strip().lower()

    if not provider_name:
        raise SMSError("SMS provider is not configured")

    if provider_name == "kavenegar":
        from core.sms_providers.kavenegar import send_sms
    elif provider_name == "smsir":
        from core.sms_providers.smsir import send_sms    
    else:
        raise SMSError("Unsupported SMS provider.")    

    try:
        send_sms(phone_number,code)

    except SMSError:
        logger.warning("OTP SMS delivery failed.")  
        raise  
    except Exception as exc:
        logger.exception("Unexpected SMS Provider error")
        raise SMSError("Could not send verification SMS.") from exc

    logger.info("OTP SMS Provider accepted request.")    