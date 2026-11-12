from django.contrib.auth.models import User
from django.db import models

class Service(models.Model):

    CATEGORY_CHOICES = {
         "administrative":"خدمات اداری و امور آنلاین",
         "business":"راهکارهای هوشمند کسب و کار"
    }

    title = models.CharField(
         max_length = 100,
         verbose_name="عنوان خدمت"
         )

    slug = models.SlugField(
         max_length=120,unique=True,
         verbose_name="شناسه خدمت"

         )

    category = models.CharField(
         max_length=20,
         choices=CATEGORY_CHOICES,
         default="administrative",
         verbose_name="دسته بندی"
    )

    description = models.TextField(verbose_name="توضیح کوتاه")

    detail_description = models.TextField(
         blank=True,
         verbose_name="توضیحات کامل خدمت"
    )

    requirements = models.TextField(
         blank=True,
         verbose_name="مدارک موردنیاز"
    )

    process_steps = models.TextField(
         blank=True,
         verbose_name="مراحل انجام خدمت"
    )

    important_notes = models.TextField(
         blank=True,
         verbose_name="نکات مهم"
    )

    faq = models.JSONField(
         default=list,
         blank=True,
         verbose_name="پرسش های متداول"
    )


    icon = models.CharField(
         max_length = 20,
         verbose_name="آیکون"
     )

    is_active = models.BooleanField(
         default=True,
         verbose_name="فعال"
         )

    def __str__(self):
        return self.title


class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    phone_number = models.CharField(
        max_length=11,
        unique=True,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.user.username


class PhoneVerification(models.Model):

        user = models.ForeignKey(
             User,
             on_delete=models.CASCADE,
             related_name="phone_verifications",
             null=True,
             blank=True
        )

        phone_number = models.CharField(
             max_length=11
        )

        code = models.CharField(
             max_length=6
        )

        created_at = models.DateTimeField(
             auto_now_add=True
        )

        expires_at = models.DateTimeField()

        is_verified = models.BooleanField(
             default=False
        )

        attempts = models.PositiveIntegerField(default=0)

        PURPOSE_CHOICES = [
             ("registration","ثبت نام"),
             ("password_reset","بازیابی کلمه عبور"),
             ("change_phone","تغییر شماره موبایل")
        ]

        purpose = models.CharField(
             max_length=20,
             choices=PURPOSE_CHOICES,
             default="registration"
        )

        def __str__(self):
            if self.user:
                 return f"{self.user.username}-{self.phone_number}-{self.purpose}"
            return f"registration-{self.phone_number}-{self.purpose}"



class Order(models.Model):

     STATUS_CHOICES = [
          ("submitted","ثبت شده"),
          ("reviewing","در حال بررسی"),
          ("in_progress","در حال انجام"),
          ("completed","انجام شده"),
          ("rejected","رد شده"),
          ("cancelled","لغو شده")
     ]

     user = models.ForeignKey(
          User,
          on_delete=models.CASCADE,
          related_name="service_orders"
     )

     service = models.ForeignKey(
          Service,
          on_delete=models.PROTECT,
          related_name="orders"
     )

     description = models.TextField(
          verbose_name="توضیحات درخواست"
     )

     status = models.CharField(
          max_length=20,
          choices = STATUS_CHOICES,
          default="submitted",
          verbose_name="وضعیت سفارش"
     )

     created_at = models.DateTimeField(
          auto_now_add=True,
          verbose_name="زمان ثبت"
     )

     updated_at = models.DateTimeField(
          auto_now=True,
          verbose_name="آخرین به روز رسانی"
     )

     def __str__(self):
          return f"سفارش#{self.pk}-{self.service.title}"
        

class OrderMessage(models.Model):

     order = models.ForeignKey(
          Order,
          on_delete=models.CASCADE,
          related_name="message",
          verbose_name="سفارش"
     )  

     sender = models.ForeignKey(
          User,
          on_delete=models.CASCADE,
          related_name="order_message",
          verbose_name="فرستنده"
     ) 

     message = models.TextField(
          verbose_name="متن پیام"
     ) 

     created_at = models.DateTimeField(
          auto_now_add=True,
          verbose_name="زمان ارسال"
     )

     is_read = models.BooleanField(
          default=False,
          verbose_name="خوانده شده"
     )

     class Meta:
          ordering = ["created_at"]
          verbose_name = 'پیام سفارش'
          verbose_name_plural = 'پیام های سفارش'

     def __str__(self):
         return f"پیام سفارش#{self.order_id}از{self.sender}"
          