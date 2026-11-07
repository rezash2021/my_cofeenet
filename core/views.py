from django.http import Http404
from django.utils import timezone
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render,get_object_or_404,redirect
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from .models import Service,PhoneVerification,Profile,Order
from .form import ( ProfileForm, PhoneChangeForm, PhoneVerificationForm,RegisterForm,ForgotPasswordForm,PasswordForm,OrderForm)
from .utils import create_phone_verification,can_request_phone_verification

from django.contrib import messages
from core.sms import send_otp,send_order_notification,SMSError

def index(request):

    services = Service.objects.filter(is_active = True)

    context = {
        "services":services
    }

    return render(request, "core/index.html",context)

def services(request):

    categories = [
        {
            "slug":"administrative",
            "title":"خدمات اداری و امور آنلاین",
            "description":"برای انجام امور اداری و استفاده از خدمات آنلاین این بخش را انتخاب کنید"
        },
        {
            "slug":"business",
            "title":"راهکارهای هوشمند کسب و کار",
            "description":"ارائه راهکارهایی برای ساده سازی فرایندها،خودکارسازی کارهای تکراری و بهبود مدیریت کسب و کار"
        }
    ]

    return render(request,"core/services.html",{"categories":categories})


def service_category(request,category):

    category_titles = dict(Service.CATEGORY_CHOICES)

    if category not in category_titles:
        raise Http404("دسته بندی مورد نظر پیدا نشد")

    services = Service.objects.filter(
        category=category,
        is_active=True
    ).order_by("title")

    return render(request,"core/service_category.html",
                  {
                      "services":services,
                      "category":category,
                      "category_title":category_titles[category]
                  }
                  )


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

           verification = create_phone_verification(
               user=None,
               phone_number=phone_number,
               purpose="registration"
           )

           try:
               
               send_otp(phone_number,verification.code)

           except SMSError:
               
               verification.is_verified=True
               verification.save(update_fields=["is_verified"])

               messages.error(
                   request,
                   "ارسال کد ناموفق بود لطفا چند لحظه دیگر تلاش کنید."
               )

               return render(request,"core/register.html",{"form":form})


           request.session["registration_username"] = username
           request.session["registration_phone"] = phone_number
           request.session["registration_verified"] = False

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

            profile = Profile.objects.filter(
                phone_number=phone_number
                ).select_related("user").first()

            if not profile:
                form.add_error(phone_number,"اطلاعات وارد شده معتبر نیست.")

            elif not can_request_phone_verification(
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

                try:
                    send_otp(phone_number,verification.code)
                except SMSError:
                    verification.is_verified = True
                    verification.save(update_fields=["is_verified"])  

                    messages.error("ارسال کد تایید ناموفق بود لطفا چند لحظه دیگر تلاش کنید.")  

                else:
                    request.session["password_reset_phone"] = phone_number

                    request.session.pop("password_reset_verified",None)

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


def resend_password_reset_code(request):

    if request.method != "POST":
        return redirect("forgot_password")

    phone_number = request.session.get("password_reset_phone")

    if not phone_number:
        return redirect("forgot_password")

    profile = Profile.objects.filter(
        phone_number=phone_number
    ).select_related("user").first()

    if not profile:
        request.session.pop("password_reset_phone",None)
        return redirect("forgot_password")
    if not can_request_phone_verification(
        profile.user,
        purpose="password_reset"
    ):
        messages.error(
            request,
            "لطفا 60 ثانیه صبر کنید و سپس مجددا درخواست کد نمایید."
            )

        return redirect("verify_password_reset")
    verification = create_phone_verification(
        user=profile.user,
        phone_number=phone_number,
        purpose="password_reset"
    )

    try:
        send_otp(phone_number,verification.code)
    except SMSError:
        verification.is_verified=True
        verification.save(update_fields=["is_verified"])    

        messages.error(
            "درخواست کد تایید ناموفق بود لطفا لحظاتی بعد دوباره تلاش کنید."
        )
    else:
        request.session.pop("password_reset_verified",None)   
        messages.success(
            request,
            "کد تایید جدید ارسال شد."
        ) 

    return redirect("verify_password_reset")

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

    orders = Order.objects.filter(user=profile.user).select_related("service").order_by("-created_at")

    status_counts = {
        "submitted": orders.filter(status="submitted").count(),
        "reviewing": orders.filter(status="reviewing").count(),
        "in_progress": orders.filter(status="in_progress").count(),
        "completed": orders.filter(status="completed").count(),
        "rejected": orders.filter(status="rejected").count(),
        "cancelled": orders.filter(status="cancelled").count(),
    }


    order_stats = {
        "total_orders":orders.count(),
        **{
            f"{status}_orders":count
            for status,count in status_counts.items()
        }
    }

    status_filters = [
        {
            "value":"all",
            "label":"همه سفارش ها"
        },
        *[
            {
                "value":status,
                "label":label
            }
            for status,label in Order.STATUS_CHOICES
        ]
    ]



    stats_cards = [
        {
            "title": "کل سفارش‌ها",
            "count": order_stats["total_orders"],
            "description": "مجموع درخواست‌های ثبت‌شده",
            "color": "indigo",
            "icon": "#",
        },
        {
            "title": "ثبت‌شده",
            "count": order_stats["submitted_orders"],
            "description": "در انتظار بررسی اولیه",
            "color": "blue",
            "icon": "✓",
        },
        {
            "title": "در حال بررسی",
            "count": order_stats["reviewing_orders"],
            "description": "در حال بررسی درخواست",
            "color": "amber",
            "icon": "◷",
        },
        {
            "title": "در حال انجام",
            "count": order_stats["in_progress_orders"],
            "description": "درخواست‌های در حال پیگیری",
            "color": "violet",
            "icon": "↻",
        },
        {
            "title": "انجام شده",
            "count": order_stats["completed_orders"],
            "description": "درخواست‌های به پایان رسیده",
            "color": "green",
            "icon": "✓",
        },
        {
            "title": "ردشده",
            "count": order_stats["rejected_orders"],
            "description": "درخواست‌های ردشده",
            "color": "red",
            "icon": "×",
        },
        {
            "title": "لغوشده",
            "count": order_stats["cancelled_orders"],
            "description": "درخواست‌های لغوشده",
            "color": "slate",
            "icon": "−",
        },
    ]

    status_styles = {
        "submitted": "border-blue-200 bg-blue-50 text-blue-700",
        "reviewing": "border-amber-200 bg-amber-50 text-amber-700",
        "in_progress": "border-indigo-200 bg-indigo-50 text-indigo-700",
        "completed": "border-green-200 bg-green-50 text-green-700",
        "rejected": "border-red-200 bg-red-50 text-red-700",
        "cancelled": "border-slate-200 bg-slate-100 text-slate-700",
    }

    for order in orders:
        order.status_style = status_styles.get(
            order.status,
            "border-slate-200 bg-slate-100 text-slate-700",
        )    
        
    
    return render(request,"core/profile.html",
                  {
                      "profile":profile,
                      "current_phone_number" : profile.phone_number,
                      "orders":orders,
                      **order_stats,
                      "stats_cards":stats_cards,
                      "status_filters":status_filters
                   
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

               try:
                 send_otp(phone_number,verification.code)
               except SMSError:
                 form.add_error(
                     None,
                     "ارسال کد تایید ناموفق بود.لطفا مجددا تلاش کنید."
                 )
               else:
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

@login_required
def create_order(request,slug):
    service = get_object_or_404(
        Service,
        slug=slug,
        is_active=True
    )

    if request.method == "POST":
        form = OrderForm(request.POST)

        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.service = service
            order.save()

            try:
                send_order_notification(order)
            except Exception:
                import logging
                logging.getLogger(__name__).exception(
                    "Order notification failed for order #%s",
                     order.pk,
                )

            messages.success(
                request,
                f"درخواست شما با شماره{order.pk}ثبت شد."
            )

            return redirect("profile")
    else:
        form = OrderForm()

    return render(request,
                  "core/order_form.html",
                  {
                      "form":form,
                      "service":service
                  }
                  )     

@login_required
def cancel_order(request,order_id):

    if request.method != "POST":
        return redirect("profile")

    order = get_object_or_404(
        Order,
        pk=order_id,
        user=request.user
    )

    if order.status != "submitted":
        messages.error(
            request,
            "لغو درخواست ممکن نیست.درخواست در حال بررسی یا انجام شده می باشد."
        )
        return redirect("profile")

    order.status = "cancelled"
    order.save(update_fields=["status"])

    messages.success(
        request,
        f"درخواست شماره{order.pk}با موفقیت لغو شد."
    )

    return redirect("profile")

    

