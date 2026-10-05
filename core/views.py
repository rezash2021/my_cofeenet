from django.http import HttpResponse
from django.utils import timezone
from django.db import transaction
from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Service,PhoneVerification,Profile
from .form import ( ProfileForm, PhoneChangeForm, PhoneVerificationForm,RegisterForm,ForgotPasswordForm,PasswordForm)
from .utils import create_phone_verification,can_request_phone_verification

def index(request):

    services = Service.objects.filter(is_active = True)

    context = {
        "services":services
    }

    return render(request, "core/index.html",context)

def services(request):
    services = Service.objects.filter(is_active = True)

    context = {
        "services":services
    }

    return render(request,"core/services.html",context)


def service_detail(request,slug):

    service = get_object_or_404(

        Service,
        slug=slug,
        is_active = True
    )

    context = {

        "service":service
    }

    return render(request,"core/service_detail.html",context)

def about(request):
    return render(request,"core/about.html")

def contact(request):
    return render(request,"core/contact.html")

def user_login(request):
    error = None
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username = username,
            password = password,
        ) 

        if user is not None:
            login(request,user)
            next_url =request.POST.get("next") or request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
            ):
                return redirect(next_url)
            return redirect("home")   


        error = "نام کاربری یا کلمه عبور اشتباه است"

        

    return render(request,"core/login.html",{"error":error})    

def user_logout(request):
    logout(request)
    return redirect("home")


def register(request):

    if request.method == "POST":

        form = RegisterForm(request.POST)

        if form.is_valid():

           username = form.cleaned_data["username"]
           phone_number = form.cleaned_data["phone_number"]

           request.session["registration_username"] = username
           request.session["registration_phone"] = phone_number
           request.session["registration_verified"] = False

           verification = create_phone_verification(
               user=None,
               phone_number=phone_number,
               purpose="registration"
           )

           print(
               f"Registration OTP for : {verification.phone_number} : "
               f"{verification.code}"
           )

           return redirect("verify_registration")

    else:

        form = RegisterForm()

    return render(
        request,
        "core/register.html",
        {
            "form": form,
        },
    )

def verify_registration(request):

    username = request.session.get("registration_username")
    phone_number = request.session.get("registration_phone")

    if not username or not phone_number:
        return redirect("register")

    verification = PhoneVerification.objects.filter(
        user__isnull=True,
        phone_number=phone_number,
        is_verified=False,
        purpose="registration"
    ).order_by("-created_at").first()

    if not verification:
        return redirect("register")

    if request.method == "POST":

        form = PhoneVerificationForm(request.POST)

        if form.is_valid():

            code=form.cleaned_data["code"]

            if verification.expires_at < timezone.now():

                form.add_error(
                    "code",
                    "کد تایید منقضی شد لطفا مجدد درخواست کد کنید"
                )
            elif verification.code != code:

                verification.attempts += 1

                if verification.attempts >= 5:

                    verification.is_verified = True

                    verification.save(
                        update_fields = [
                            "attempts",
                            "is_verified"
                        ]
                    )

                    form.add_error(
                        "code",
                        "تعداد تلاش های شما به پایان رسید لطفا دوباره ثبت نام را شروع کنید"
                    ) 
                else:

                    verification.save(
                        update_fields=["attempts"]
                    )

                    remaining_attempts =  5 - verification.attempts
                    

                    form.add_error(
                        "code",
                        f"کد وارد شده صحیح نیست. "
                        f"{remaining_attempts} تلاش دیگر باقی مانده است.",
                    ) 

            else:

              verification.is_verified = True

              verification.save(update_fields=["is_verified"])  

              request.session["registration_verified"] = True

              return redirect("registration_password")

    else:

        form = PhoneVerificationForm()   

    return render(request,"core/verify_phone.html",
            {
                "form":form,
                "verification":verification
             },
            ) 


def set_registration_password(request):

    username = request.session.get("registration_username")
    phone_number = request.session.get("registration_phone")
    verified = request.session.get("registration_verified")

    if not username or not phone_number or not verified:

        return redirect("register")

    if request.method == "POST":

        form = PasswordForm(request.POST)

        if form.is_valid():

            password = form.cleaned_data["password"]

            request.session["registration_pass"] = password

            return redirect("complete_registration")

    else:

      form = PasswordForm()

    return render(
        request,
         "core/registration_password.html"
        ,{"form":form}
         )    



def complete_registration(request):

    username = request.session.get("registration_username")
    phone_number = request.session.get("registration_phone")
    verified = request.session.get("registration_verified")
    password = request.session.get("registration_pass")

    if (
        not username
        or not phone_number
        or not verified
        or not password
    ):
        return redirect("register")

    if User.objects.filter(username=username).exists():
        return redirect("register")

    if Profile.objects.filter(phone_number=phone_number).exists():
        return redirect("register")

    user = User.objects.create_user(
        username=username,
        password=password
    )

    user.profile.phone_number=phone_number
    user.profile.save(update_fields=["phone_number"])

    login(request,user)

    request.session.pop("registration_username",None)
    request.session.pop("registration_phone",None)
    request.session.pop("registration_pass",None)
    request.session.pop("registration_verified",None)

    return redirect("home")

def forgot_password(request):

    if request.method == "POST":

        form = ForgotPasswordForm(request.POST)

        if form.is_valid():

            phone_number = form.cleaned_data["phone_number"]

            profile = Profile.objects.get(phone_number=phone_number)

            if not can_request_phone_verification(
                profile.user,
                purpose="password_reset"
                ):

                form.add_error(
                    "phone_number",
                    "لطفا 60 ثانیه صبر کنید و مجدد درخواست کد کنید"
                )

            else: 
                verification = create_phone_verification(
                user=profile.user,
                phone_number=phone_number,
                purpose="password_reset"
            )

                print(
                     f"OTP password reset for {phone_number} :"
                     f"{verification.code}"
                   )

                request.session["password_reset_phone"] = phone_number

                return redirect("verify_password_reset")

    else:

        form = ForgotPasswordForm()

    return render(request,"core/forgot_password.html",{"form":form})    


def verify_password_reset(request):

    phone_number = request.session.get("password_reset_phone")

    if not phone_number:

        return redirect("forgot_password")

    verification = PhoneVerification.objects.filter(
        user__isnull=False,
        phone_number=phone_number,
        is_verified=False,
        purpose="password_reset"
    ).order_by("-created_at").first()

    if not verification:
        return redirect("forgot_password")

    if request.method == "POST":

        form = PhoneVerificationForm(request.POST)

        if form.is_valid():

            code = form.cleaned_data["code"]

            if verification.expires_at <timezone.now():

                form.add_error(
                    "code",
                    "کد تایید منقضی شد لطفا درخواست کد جدید نمایید"
                )

            elif verification.code != code:

                verification.attempts += 1

                if verification.attempts >= 5:

                    verification.is_verified = True

                    verification.save(
                        update_fields=[
                            "is_verified",
                            "attempts"
                        ]
                    )

                    form.add_error(
                        "code",
                        "تعداد تلاش های شما به پایان رسید لطفا مجدد درخواست کد نمایید"
                    )
                else:
                    verification.save(update_fields=["attempts"])

                    remaining_attempts = 5-verification.attempts

                    form.add_error(
                        "code",
                        f"کد وارد شده صحیح نمی باشد تعداد {remaining_attempts} تلاش دیگر باقی مانده"
                    )  

            else:

                verification.is_verified = True

                verification.save(update_fields=["is_verified"])

                request.session["password_reset_verified"] = True

                return redirect("set_new_password")

    else:

        form = PhoneVerificationForm()

    return render(request,"core/verify_phone.html",
                  {
                      "form":form,
                      "verification":verification
                      }
                  )  

def set_new_password(request):

    phone_number = request.session.get("password_reset_phone")
    verified = request.session.get("password_reset_verified")  

    if not phone_number or not verified:

        return redirect("forgot_password")

    profile = Profile.objects.filter(
        phone_number=phone_number
    ).first()

    if not profile:
        return redirect("forgot_password")

    if request.method == "POST":

        form = PasswordForm(request.POST)

        if form.is_valid():

            password = form.cleaned_data["password"]

            user = profile.user

            user.set_password(password)
            user.save()

            login(request,user)

            request.session.pop("password_reset_phone")
            request.session.pop("password_reset_verified")

            return redirect("home")

    else:

        form = PasswordForm()

    return render(
        request,
        "core/registration_password.html",
        {
            "form": form,
        },
    )                         

@login_required
def profile(request):

    profile = request.user.profile
    return render(request,"core/profile.html",
                  {
                      "profile":profile,
                      "current_phone_number" : profile.phone_number
                   
                   },
                  )

@login_required
def change_phone(request):

   if request.method == "POST":
        form = PhoneChangeForm(
             request.POST,
             user=request.user
          )

        if form.is_valid():

           if not can_request_phone_verification(request.user,purpose="change_phone"):

               form.add_error(
                   "phone_number",
                   "لطفا حداقل 60 ثانیه صبر کنید و سپس کد را مجدد درخواست کنید"
               )

           else:   

               phone_number = form.cleaned_data["phone_number"]

               verification = create_phone_verification(
                 request.user,
                  phone_number,
                  purpose="change_phone"
               ) 

               print(
                  f"OTP for {request.user.username}:"
                  f"{verification.code}"
                ) 

               return redirect("verify_phone")  

   else:
       form = PhoneChangeForm(
           user=request.user
       )

   return render(request,"core/change_phone.html",{"form":form})
@login_required
def verify_phone(request):

    verification = PhoneVerification.objects.filter(
        user=request.user,
        is_verified=False,
        purpose="change_phone"
    ).order_by("-created_at").first()

    if not verification:
        return redirect("change_phone")

    if request.method == "POST":

        form = PhoneVerificationForm(request.POST)

        if form.is_valid():

            code = form.cleaned_data["code"]

            if verification.expires_at < timezone.now():

                verification.is_verified = True
                verification.save(
                    update_fields=["is_verified"]
                )

                form.add_error(
                    "code",
                    "کد تأیید منقضی شده است. لطفاً دوباره درخواست کد کنید.",
                )

            elif verification.attempts >= 5:

                verification.is_verified = True
                verification.save(
                    update_fields=["is_verified"]
                )

                form.add_error(
                    "code",
                    "تعداد تلاش‌های شما به پایان رسیده است. لطفاً مجدداً درخواست کد کنید.",
                )

            elif verification.code != code:

                verification.attempts += 1

                if verification.attempts >= 5:

                    verification.is_verified = True
                    verification.save(
                        update_fields=[
                            "attempts",
                            "is_verified",
                        ]
                    )

                    form.add_error(
                        "code",
                        "تعداد تلاش‌های شما به پایان رسیده است. لطفاً مجدداً درخواست کد کنید.",
                    )

                else:

                    verification.save(
                        update_fields=["attempts"]
                    )

                    remaining_attempts = 5 - verification.attempts

                    form.add_error(
                        "code",
                        f"کد وارد شده صحیح نیست. "
                        f"{remaining_attempts} تلاش دیگر باقی مانده است.",
                    )

            else:

                with transaction.atomic():

                    profile = request.user.profile
                    profile.phone_number = verification.phone_number
                    profile.save(
                        update_fields=["phone_number"]
                    )

                    verification.is_verified = True
                    verification.save(
                        update_fields=["is_verified"]
                    )

                return redirect("profile")

    else:

        form = PhoneVerificationForm()

    return render(
        request,
        "core/verify_phone.html",
        {
            "form": form,
            "verification": verification,
        },
    )