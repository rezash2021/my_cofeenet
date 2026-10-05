from django.contrib.auth.models import User
from django.db import models

class Service(models.Model):

    title = models.CharField(max_length = 100)

    slug = models.SlugField(max_length=120,unique=True)

    description = models.TextField()

    icon = models.CharField(max_length = 20)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return(self.title)


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
        
    