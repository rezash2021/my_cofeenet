import requests
import logging
from django.conf import settings

from core.sms import SMSError

logger = logging.getLogger(__name__)

def send_sms(phone_number,code):

    api_key = settings.SMS_API_KEY

    template_id = settings.SMSIR_OTP_TEMPLATE_ID

    if not api_key:
        raise SMSError("SMS.IR api key is not configured.")

    if not template_id:
        raise SMSError("SMS.IR template is not configured.")

    mobile = phone_number

    if mobile.startswith("0"):
        mobile = mobile[1:]

    payload = {
        "mobile":mobile,
        "templateId":int(template_id),
        "parameters": [
            {
                "name":"CODE",
                "value":str(code)
            }
        ]
    }  

    headers = {
        "content-type":"application/json",
        "Accept":"text/plain",
        "x-api-key":api_key
    }  

    try:
        response = requests.post(
            "https://api.sms.ir/v1/send/verify",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") != 1:
            logger.warning(
                "SMS.ir rejected OTP request. status: %s",
                result.get("status")
            )
            raise SMSError("SMS.ir rejected the verification SMS request.")
    except requests.RequestException as exc:
        logger.warning(
            "SMS.IR request failed.HTTP status: %s",
            getattr(getattr(exc,"response",None),"status_code",None)
        )
        raise SMSError("SMS.IR failed to send verification sms.") from exc







