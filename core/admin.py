from django.contrib import admin

from bookings.models import Appointment
from core.models.appity_token import AppityToken
from core.models.models import AppUser
from services.models import Service

# Register your models here.
@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'is_active', 'email_verified', 'mobile_phone_number']


@admin.register(AppityToken)
class AppityTokenAdmin(admin.ModelAdmin):
    list_display = ['token', 'user', 'display_name', 'frontend', 'created_at', 'expire_at']


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['service', 'appointment_date', 'status']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration', 'access']
