from django.contrib import admin
from django.urls import reverse

from .models import Service,Profile,Order,OrderMessage

admin.site.register(Profile)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):

    list_display = (

        "title",
        "icon",
        "is_active",
    )

    search_fields = (

        "title",
        "description",
    )

    list_filter = (

        "is_active",
    )  

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "service",
        "status",
        "created_at",
        "updated_at"
    )

    list_filter = (
        "status",
        "created_at",
        "service"
    )

    search_fields = (
        "user__username",
        "service__title",
        "description",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)  

    list_per_page = 25  

    list_editable = (
        "status",
    )

    fieldsets = (
        ("اطلاعات سفارش",{
            "fields":(
                "user",
                "service",
                "description",
                "status"
            )
        }),
        ("اطلاعات زمانی",{
            "fields":(
                "created_at",
                "updated_at"
            )
        })
    )

    change_list_template = "admin/core/order/change_list.html"

    def changelist_view(self,request,extra_context=None):
        statuses = Order.STATUS_CHOICES

        status_counts=[]

        for value,label in statuses:
            status_counts.append({
                "value":value,
                "label":label,
                "count":Order.objects.filter(status=value).count()
            })

        extra_context = extra_context or {}
        extra_context["status_counts"] = status_counts

        return super().changelist_view(
            request,
            extra_context=extra_context
        )   

    def get_row_css(self, obj, index):
     if obj.status == "submitted":
        return "new-order-row"
     return "" 

@admin.register(OrderMessage)
class OrderMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "sender", "created_at", "is_read")
    list_filter = ("is_read", "created_at")
    search_fields = ("message", "sender__username")
    readonly_fields = ("created_at",)

    

