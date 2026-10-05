from django.urls import path
from . import views

urlpatterns = [
    path("",views.index,name="home"),
    path("services/",views.services,name="services"),
    path("services/<slug:slug>",views.service_detail,name="service_detail"),
    path("about/",views.about,name="about"),
    path("contact/",views.contact,name="contact"),
    path("login/",views.user_login,name="login"),
    path("logout/",views.user_logout,name="logout"),
    path("register/",views.register,name="register"),
    path("register/verify/",views.verify_registration,name="verify_registration"),
    path("register/set_password/",views.set_registration_password, name="registration_password"),
    path("register/complete/",views.complete_registration,name="complete_registration"),
    path("password/forgot/",views.forgot_password,name="forgot_password"),
    path("password/verify/",views.verify_password_reset,name="verify_password_reset"),
    path("password/new/",views.set_new_password,name="set_new_password"),
    path("profile/",views.profile,name="profile"),
    path("profile/change_phone/",views.change_phone,name="change_phone"),
    path("profile/verify_phone/",views.verify_phone,name="verify_phone")
]
