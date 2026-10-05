from django.contrib import admin

from .models import Service,Profile

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
