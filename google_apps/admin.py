from django.contrib import admin

from .models.calendar import (
    Company,
    Event,
    Hall,
)
from .models.common import GoogleCredentials


@admin.register(GoogleCredentials)
class GoogleCredentialsAdmin(admin.ModelAdmin):
    pass


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display = ('name', 'given_name', 'company', 'description', 'google_id', 'disabled')
    list_filter = ('company', 'disabled')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'hall', 'company', 'description', 'google_id', 'date_start', 'date_end')
    list_filter = ('company', 'hall')
