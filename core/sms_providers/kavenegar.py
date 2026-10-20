from django.conf import settings
from kavenegar import KavenegarAPI,APIException,HTTPException
from core.sms import SMSError

def send_sms(phone_number,code):

    api_key = settings.SMS_API_KEY
    template = settings.KAVENEGAR_OTP_TEMPLATE

    if not api_key:
        raise SMSError("kavenegar api key is not configured.")

    if not template:
        raise SMSError("kavenegar OTP template is not configured.")

    try:
        api = KavenegarAPI(api_key,timeout=10)

        api.verify_lookup({
            "receptor":phone_number,
            "token":code,
            "template":template,
            "type":"sms"
        })
    except(APIException,HTTPException) as exc:
        raise SMSError("kavenegar failed to send sms.") from exc    
