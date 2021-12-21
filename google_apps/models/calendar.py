import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .common import GoogleBaseModel
from ..google_api import CalendarAPI


logger = logging.getLogger('google')
logger.propagate = False


class Company(GoogleBaseModel):

    user = models.ForeignKey(
        User,
        related_name='user',
        on_delete=models.CASCADE,
    )

    def get_halls_str(self, disabled=False):
        return ', '.join([x.name for x in self.halls.filter(disabled=disabled)])

    @property
    def disabled_halls_string(self):
        return self.get_halls_str(disabled=True)

    @property
    def enabled_halls_string(self):
        return self.get_halls_str()

    def sync_halls(self, next_page_token: str = None, api: CalendarAPI = None):
        ''' Recursively check all pages with calendars '''

        logger.info(f'Start sync halls for company id {self.pk}, page_token: {next_page_token}')
        if not api:
            api = CalendarAPI()
            result, message = api.get_service(self.user.credentials)
            if not result:
                return False, _('Can not create Calendar Service %(message)s') % {'message': message, }, {}

        result, response, message = api.get_calendars(
            sync_token=self.next_sync_token, next_page_token=next_page_token)

        if not result:
            return (
                False,
                _('Can not get calendars "%(message)s" Company: %(name)s') % {'message': message, 'name': self.name},
                response
            )

        for calendar in response['items']:
            hall, created = Hall.objects.get_or_create(company=self, google_id=calendar['id'])
            hall.name = calendar.get('summary', 'None')
            hall.last_response = calendar
            description = calendar.get('description', None)
            if description:
                hall.description = description
            hall.save()

        next_page_token = response.get('nextPageToken', None)
        if next_page_token:
            self.sync_halls(next_page_token=next_page_token, api=api)

        next_sync_token = response.get('nextSyncToken', '')
        if next_sync_token:
            self.next_sync_token = next_sync_token
            self.save()
            logger.info(f'End sync halls for company id {self.pk} - SUCCESS')

        return True, '', response

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')


class Hall(GoogleBaseModel):

    given_name = models.CharField(
        _('Hall name'), max_length=120, blank=True, default='')

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='halls'
    )

    disabled = models.BooleanField(_('Disabled for this company'), default=True)

    def sync_events(self, next_page_token: str = None, api: CalendarAPI = None):
        ''' Recursively check all pages with events '''

        logger.info(f'Start sync events for hall id {self.pk}, name {self.given_name}, page_token: {next_page_token}')
        if not api:
            api = CalendarAPI()
            result, message = api.get_service(self.company.user.credentials)
            if not result:
                logger.warning(f'Fail synk events for hall id {self.pk}')
                return False, _('Can not create Calendar Service %(message)s') % {'message': message, }, {}

        result, response, message = api.get_events_from_calendar(
            calendar_id=self.google_id, sync_token=self.next_sync_token, next_page_token=next_page_token)

        if not result:
            return (
                False,
                _('Can not get events "%(message)s" Hall: %(name)s') % {'message': message, 'name': self.given_name},
                response
            )

        for event in response['items']:

            if event.get('status') == 'cancelled':

                try:
                    Event.objects.filter(hall=self, google_id=event['id']).delete()
                except Event.DoesNotExist:
                    pass
            else:
                event_obj, created = Event.objects.get_or_create(
                    hall=self, company=self.company, google_id=event['id'])

                event_obj.last_response = event

                event_obj.name = event.get('summary', 'None')

                description = event.get('description', None)
                if description:
                    event_obj.description = description

                if event.get('start'):
                    start_date = event['start'].get('dateTime')
                    if not start_date:
                        start_date = event['start'].get('date')
                    if start_date:
                        event_obj.date_start = start_date
                if event.get('end'):
                    end_date = event['end'].get('dateTime')
                    if not end_date:
                        end_date = event['end'].get('date')
                    if end_date:
                        event_obj.date_end = end_date

                event_obj.save()

        next_page_token = response.get('nextPageToken', None)
        if next_page_token:
            self.sync_events(next_page_token=next_page_token, api=api)

        next_sync_token = response.get('nextSyncToken', '')
        if next_sync_token:
            self.next_sync_token = next_sync_token
            self.save()
            logger.info(f'End sync events for hall id {self.pk}, name {self.given_name}')

        return True, '', {}

    def check_intersection(self):
        # TODO: Find a better algotritm
        all_events = self.events.all()
        all_events.update(error=False)
        events_dates = [{
            'name': x.name,
            'id': x.pk,
            'start': x.date_start.timestamp(),
            'end': x.date_end.timestamp()} for x in all_events
        ]
        intersection = []
        for start_event in events_dates:
            for end_event in events_dates:
                latest_start = max(start_event['start'], end_event['start'])
                earliest_end = min(start_event['end'], end_event['end'])
                if (latest_start < earliest_end) and (start_event['id'] != end_event['id']):
                    event_id = start_event['id']
                    logger.warning(f'Find intersection in hall ID {self.pk}. Event ID {event_id}')
                    intersection.append(start_event)
        intersection_pk_list = [x['id'] for x in intersection]
        all_events.filter(pk__in=intersection_pk_list).update(error=True)

    def __str__(self):
        return f'{self.company.name}: {self.given_name}|{self.name}'

    class Meta:
        verbose_name = _('Hall')
        verbose_name_plural = _('Halls')
        unique_together = ('company', 'google_id')


class Event(GoogleBaseModel):

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='events'
    )

    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name='events'
    )

    date_start = models.DateTimeField(
        _('Event start'), blank=True, null=True)

    date_end = models.DateTimeField(
        _('Event end'), blank=True, null=True)

    error = models.BooleanField(_('Date intersection error'), default=False)

    def __str__(self):
        return f'{self.name} - ({self.hall})'

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        unique_together = ('hall', 'google_id')
        ordering = ['date_start']


@receiver(post_save, sender=Company)
def start_sync_after_create(sender, instance, created, **kwargs):
    if created and settings.SYNC_AFTER_CREATE:
        result, message, response = instance.sync_halls()
        if result:
            logger.info(f'Initial Sync Success for company ID: {instance.pk}. Name: {instance.name}')
            instance.last_sync = timezone.now()
            instance.save()
        else:
            logger.error(
                f'Initial Sync Fail for company ID: {instance.pk}. Name: {instance.name}\
                MESSAGE: "{message}", RESPONSE {response}')


@receiver(pre_save, sender=Hall)
def check_single_enabled_hall(sender, instance, **kwargs):
    ''' For admin single hall enabled checking '''
    if not instance.disabled:
        count_of_enabled_halls = Hall.objects.filter(
            google_id=instance.google_id, disabled=False).exclude(pk=instance.pk).count()
        if count_of_enabled_halls > 0:
            raise ValueError('Only one unique hall may be enabled!')
