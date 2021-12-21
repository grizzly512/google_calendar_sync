import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import Form
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView
from django.views.generic.base import RedirectView
from django.views.generic.edit import CreateView, FormView, UpdateView

from django_db_logger.models import StatusLog

import google_auth_oauthlib.flow

from .forms import CompanyCreateForm, ConfirmForm, HallEnableForm
from .helpers import build_url
from .models.calendar import Company, Event, Hall
from .models.common import GoogleCredentials


logger = logging.getLogger('django')


class LoggingListView(LoginRequiredMixin, ListView):
    template_name = 'google_apps/log.html'
    login_url = 'accounts/login/'
    model = StatusLog
    paginate_by = 50

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['company_create_form'] = CompanyCreateForm
        return context


class CompanyListView(LoginRequiredMixin, ListView):
    template_name = 'google_apps/main_page.html'
    login_url = 'accounts/login/'
    model = Company

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['company_create_form'] = CompanyCreateForm
        return context


class CompanyDetailView(LoginRequiredMixin, DetailView):
    template_name = 'google_apps/company_detail.html'
    login_url = 'accounts/login/'
    model = Company

    def get_context_data(self, **kwargs) -> dict:
        context = super().get_context_data(**kwargs)
        context['hall_enable_form'] = HallEnableForm
        context['hall_disable_form'] = ConfirmForm
        return context


class EventListView(LoginRequiredMixin, ListView):
    template_name = 'google_apps/event_list.html'
    login_url = 'accounts/login/'
    model = Event
    paginate_by = 50

    def get_queryset(self):
        return self.model.objects.filter(hall__pk=self.kwargs['hall'])


class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyCreateForm

    def form_valid(self, form: Form) -> render:
        form.instance.user = self.request.user
        return super(CompanyCreateView, self).form_valid(form)

    def get_success_url(self):
        return build_url('google_apps:main')


class HallEnableView(LoginRequiredMixin, UpdateView):
    model = Hall
    form_class = HallEnableForm

    def form_valid(self, form: Form) -> render:

        # single hall enabled checking
        count_of_enabled_halls = Hall.objects.filter(
            google_id=self.object.google_id, disabled=False).exclude(pk=self.object.pk).count()
        if count_of_enabled_halls > 0:
            messages.warning(self.request, _('Hall enabled in other company! Disable it first!'))
            return self.form_invalid(form)

        form.instance.disabled = False

        # update after enabling
        if settings.SYNC_AFTER_CREATE:
            result, message, response = self.object.sync_events()
            if result:
                logger.info(f'Initial Sync Success for hall ID: {self.object.pk}. Name: {self.object.name}')
                self.object.last_sync = timezone.now()
            else:
                logger.error(
                    f'Initial Sync Fail for hall ID: {self.object.pk}. Name: {self.object.name}\
                    MESSAGE: "{message}", RESPONSE {response}')

        messages.success(self.request, _(f'Hall enabled with name: {form.instance.given_name}'))
        return super(HallEnableView, self).form_valid(form)

    def form_invalid(self, form: Form) -> redirect:
        return redirect(self.get_success_url(), permanent=False)

    def get_success_url(self):
        return build_url('google_apps:company_detail', kwargs={'pk': self.object.company.pk})


class HallDisableView(LoginRequiredMixin, FormView):
    form_class = ConfirmForm

    def form_valid(self, form: Form) -> render:

        try:
            hall = Hall.objects.get(id=self.kwargs['id'])
        except Hall.DoesNotExist:
            messages.warning(self.request, _('Invalid hall ID!'))
            return self.form_invalid(form)

        hall.disabled = True
        hall.save()

        messages.success(self.request, _('Hall disabled!'))
        return super(HallDisableView, self).form_valid(form)

    def form_invalid(self, form: Form) -> redirect:
        return redirect(self.get_success_url(), permanent=False)

    def get_success_url(self):
        return build_url('google_apps:company_detail', kwargs={'pk': self.kwargs['company']})


class CredentialsCalendarFirstStepView(LoginRequiredMixin, RedirectView):
    ''' Google First step authorization '''

    permanent = False

    def get_google_uri(self):

        CLIENT_SECRET_FILE_PATH = settings.CLIENT_SECRET_FILE_PATH
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
                  'https://www.googleapis.com/auth/calendar.events.readonly']

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE_PATH, SCOPES)

        flow.redirect_uri = f'{settings.DOMAIN}/callback/oauth2/calendar'

        authorization_url, state = flow.authorization_url(
            access_type='offline', include_granted_scopes='true')

        return authorization_url

    def get_redirect_url(self, *args, **kwargs):
        return self.get_google_uri()


class CredentialsCalendarSecondStepView(LoginRequiredMixin, RedirectView):
    ''' Google Second step authorization '''

    permanent = False

    def get_google_credentials(self):

        state = self.request.GET.get('state', None)

        CLIENT_SECRET_FILE_PATH = settings.CLIENT_SECRET_FILE_PATH
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly',
                  'https://www.googleapis.com/auth/calendar.events.readonly']

        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE_PATH,
            scopes=SCOPES,
            state=state,
        )

        flow.redirect_uri = f'{settings.DOMAIN}/callback/oauth2/calendar'
        flow.fetch_token(authorization_response=self.request.build_absolute_uri())

        credentials = flow.credentials

        if credentials and credentials.valid and credentials.refresh_token:
            try:

                obj, created = GoogleCredentials.objects.get_or_create(user=self.request.user)
                obj.credentials = credentials
                obj.save()

                messages.success(self.request, _('Credentials saves succesfully!'))
            except GoogleCredentials.DoesNotExist:
                messages.warning(self.request, _('Credentials expired, please try again later!'))
        else:

            messages.error(
                self.request,
                _('Your credentials invalid, please visit "https://myaccount.google.com/u/0/permissions", \
                    remove access to an app and try again.'))

    def get_redirect_url(self, *args, **kwargs):
        self.get_google_credentials()
        return build_url('google_apps:main')
