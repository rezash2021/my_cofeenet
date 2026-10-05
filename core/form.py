from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

from .models import Profile


class RegisterForm(forms.Form):

    username = forms.CharField(
        max_length=150,
        label="نام کاربری",
        widget=forms.TextInput(
            attrs={
                "class":"w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder":"نام کاربری",
                "autocomplete":"username"
            }
        )
    )

    phone_number = forms.CharField(
        max_length=11,
        min_length=11,
        label="شماره موبایل",
        validators=[
            RegexValidator(
                regex=r"^09\d{9}$",
                message="شماره موبایل باید 11 رقم باشد و با 09 شروع شود"
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class":"w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder":"09123456789",
                "inputmode":"numeric",
                "autocomplete":"tel"
            }
        )
    )

    def clean_username(self):

        username = self.cleaned_data["username"]

        if User.objects.filter(username=username).exists():

            raise forms.ValidationError(
                "این نام کاربری متعلق به شخص دیگری است"
            )

        return username

    def clean_phone_number(self):

        phone_number = self.cleaned_data["phone_number"]

        if Profile.objects.filter(phone_number=phone_number).exists():

            raise forms.ValidationError(
                "این شماره موبایل متعلق به کاربر دیگری می باشد"
            )

        return phone_number






class ProfileForm(forms.ModelForm):

    class Meta:

        model = Profile
        fields = ()
        


class PhoneChangeForm(forms.Form):

    phone_number = forms.CharField(
        max_length=11,
        min_length=11,
        label="شماره موبایل جدید",
        validators=[
            RegexValidator(
                regex=r"^09\d{9}$",
                message="شماره موبایل باید 11 رقم باشد و با 09 شروع شود"
            )
        ],
        widget=forms.TextInput(
            attrs={
                "class":"w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline focus:ring-2 focus:ring-indigo-500",
                "placeholder":"09123456789"
            }
        )
    )

    def __init__(self,*args,user=None,**kwargs):

        super().__init__(*args,**kwargs)
        self.user=user

    def clean_phone_number(self):
         phone_number = self.cleaned_data["phone_number"]

         if phone_number == self.user.profile.phone_number:
            raise forms.ValidationError(
                "شماره جدید باید با شماره فعلی متفاوت باشد"
            )
         if Profile.objects.filter(
             phone_number=phone_number
            ).exclude(user=self.user).exists():

             raise forms.ValidationError(
                "این شماره موبایل متعلق به کاربر دیگری است",
                code="duplicate_phone_number"
            )
         return phone_number     

class PhoneVerificationForm(forms.Form):

    code=forms.CharField(
        max_length=6,
        min_length=6,
        label="کد تایید",
        widget=forms.TextInput(
            attrs={
                "class":"w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder":"کد 6 رقمی",
                "inputmode":"numeric",
                "autocomplete":"one-time-code"
            }
        )
    )

    def clean_code(self):

        code = self.cleaned_data["code"]

        persian_digits = "۰۱۲۳۴۵۶۷۸۹"
        english_digits = "0123456789"

        translation_table = str.maketrans(
            persian_digits,
            english_digits
        )

        code = code.translate(translation_table)

        if not code.isdigit():
            raise forms.ValidationError(
                "کد تایید باید فقط شامل عدد باشد"
            )

        return code


class PasswordForm(forms.Form):

    password = forms.CharField(
        label="کلمه عبور",
        min_length=8,
        widget=forms.PasswordInput(
            attrs={
                "class":"w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder":"کلمه عبور",
                "autocomplete":"new-password"
            }
         )
    )

    password_confirm = forms.CharField(
        label="تکرار کلمه عبور",
        min_length=8,
        widget=forms.PasswordInput(
             attrs={
                "class":"w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder":"تکرار کلمه عبور",
                "autocomplete":"new-password",
            }
        )
    )


    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm:

             if password != password_confirm:

                 raise forms.ValidationError(
                    " کلمه عبور با تکرار آن یکسان نیست"
                 )
        return cleaned_data    


class ForgotPasswordForm(forms.Form):

    phone_number = forms.CharField(
        max_length=11,
        min_length=11,
        label="شماره موبایل",
        validators=[
            RegexValidator(
                regex=r"^09\d{9}$",
                message="شماره موبایل باید 11 رقم باشد و با 09 شروع شود"
            )
        ],

        widget=forms.TextInput(
            attrs={
                "class":"w-full px-4 py-3 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500",
                "placeholder":"مثلا 09123456789",
                "inputmode":"numeric",
                "autocomplete":"tel"
            }
        )
    )

    def clean_phone_number(self):

        phone_number = self.cleaned_data["phone_number"]

        if not Profile.objects.filter(
            phone_number=phone_number
        ).exists():

            raise forms.ValidationError(
                "حساب کاربری با این شماره موبایل یافت نشد"
            )
        return phone_number
            
                








        