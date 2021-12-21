import logging
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from mock import patch

from .helpers import (
    mocked_google_get_service,
    mocked_google_get_calendars,
    mocked_google_get_events_from_calendar,
)

from ..helpers import dash_out

from ..models.calendar import (
    Company, Hall, Event
)
from ..models.common import (
    GoogleCredentials
)
from ..tasks import sync_company


logger = logging.getLogger('tests')


class VeryBasicWhiteTests(TestCase):

    def setUp(self):
        logger.debug(dash_out('SETUP'))
        self.user = User.objects.create_superuser(
            username='admin', email='example@example.com', password='PassW0rD')

    def test_login_page_redirect(self):
        logger.debug(dash_out('Test Login Redirect START'))

        resp = self.client.get(reverse('google_apps:main'))
        self.assertEqual(resp.status_code, 302)
        logger.debug('Redirect pass')

        logger.debug(dash_out('Test Login Redirect PASS'))

    @patch(
        "google_apps.google_api.CalendarAPI.get_service",
        side_effect=mocked_google_get_service
    )
    @patch(
        "google_apps.google_api.CalendarAPI.get_calendars",
        side_effect=mocked_google_get_calendars
    )
    @patch(
        "google_apps.google_api.CalendarAPI.get_events_from_calendar",
        side_effect=mocked_google_get_events_from_calendar
    )
    def test_sync_and_views(self, *args):
        logger.debug(dash_out('Test sync START'))

        GoogleCredentials.objects.create(user=self.user)
        company = Company.objects.create(user=self.user, name='Test Company')
        sync_company(company.pk)

        self.assertEqual(Hall.objects.all().count(), 2)
        logger.debug('Hall sync Pass')
        hall = Company.objects.all().first().halls.first()
        hall.disabled = False
        hall.save()

        self.assertEqual(Hall.objects.filter(disabled=False).count(), 1)

        sync_company(company.pk)

        self.assertEqual(Event.objects.all().count(), 3)
        logger.debug('Event sync Pass')
        self.assertEqual(Event.objects.filter(error=True).count(), 2)
        logger.debug('Intersection Pass')

        logger.debug(dash_out('Test sync PASS'))

        logger.debug(dash_out('Test views START'))

        self.client.force_login(self.user)

        resp = self.client.get(reverse('google_apps:main'))
        self.assertTemplateUsed(
            resp, 'google_apps/main_page.html')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['object_list']), 1)
        logger.debug('Main page view Pass')

        resp = self.client.get(reverse('google_apps:company_detail', kwargs={'pk': company.pk}))
        self.assertTemplateUsed(
            resp, 'google_apps/company_detail.html')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['object'].halls.all()), 2)
        logger.debug('Company detail view Pass')

        resp = self.client.get(reverse('google_apps:hall_detail', kwargs={'hall': Hall.objects.all().first().pk}))
        self.assertTemplateUsed(
            resp, 'google_apps/event_list.html')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.context['object_list']), 3)
        logger.debug('Hall detail view Pass')

        resp = self.client.get(reverse('google_apps:log'))
        self.assertTemplateUsed(
            resp, 'google_apps/log.html')
        self.assertEqual(resp.status_code, 200)
        self.assertGreater(len(resp.context['object_list']), 0)
        logger.debug('Log view Pass')

        logger.debug(dash_out('Test views PASS'))
