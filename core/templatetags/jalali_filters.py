from django import template
from django.utils import timezone
import jdatetime

register = template.Library()

@register.filter
def jalali_date(value,fmt="%y/%m/%d - %H:%M"):

    if not value:
        return ""

    if timezone.is_aware(value):
        value = timezone.localtime(value)

    jalali = jdatetime.datetime.fromgregorian(datetime=value)
    result = (
      f"{jalali.year:04d}/"
      f"{jalali.month:02d}/"
      f"{jalali.day:02d} - "
      f"{jalali.hour:02d}:"
      f"{jalali.minute:02d}"
    )   

    persian_digits = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return result.translate(persian_digits)