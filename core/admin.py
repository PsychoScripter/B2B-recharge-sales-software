from django.contrib import admin

from core.models import PhoneNumber


# Register your models here.
@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ["number", "created_at"]