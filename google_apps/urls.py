from django.urls import path

from .views import (
    CompanyCreateView,
    CompanyDetailView,
    CompanyListView,
    CredentialsCalendarFirstStepView,
    CredentialsCalendarSecondStepView,
    EventListView,
    HallDisableView,
    HallEnableView,
    LoggingListView,
)

app_name = 'google_apps'

urlpatterns = [
    path('', view=CompanyListView.as_view(),
         name='main'),
    path('company/create', view=CompanyCreateView.as_view(),
         name='company_create'),
    path('company/<uuid:pk>', view=CompanyDetailView.as_view(),
         name='company_detail'),
    path('hall/<uuid:hall>', view=EventListView.as_view(),
         name='hall_detail'),
    path('hall/<uuid:pk>/enable', view=HallEnableView.as_view(),
         name='hall_enable'),
    path('hall/<uuid:id>/<uuid:company>/disable', view=HallDisableView.as_view(),
         name='hall_disable'),
    path('user/register', view=CredentialsCalendarFirstStepView.as_view(),
         name='user_register'),
    path('callback/oauth2/calendar', view=CredentialsCalendarSecondStepView.as_view(),
         name='google_calendar_callback'),
    path('log', view=LoggingListView.as_view(),
         name='log'),
]
