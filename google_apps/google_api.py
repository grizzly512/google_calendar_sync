import logging
from typing import Tuple

from google.auth.transport.requests import Request

from googleapiclient import discovery

from .helpers import dictionary_check, exception_handler
from .models.common import GoogleCredentials


API_SERVICE_NAME = "calendar"
API_VERSION = "v3"


logger = logging.getLogger('calendar')


class CalendarAPI(object):
    ''' Google Calendar API '''

    def __init__(self):
        self._service = None

    def get_service(self, credentials: GoogleCredentials) -> Tuple[bool, str]:
        ''' Build service and refresh credentials if necessary '''

        if not isinstance(credentials, GoogleCredentials):
            return False, 'Database credentials not valid.'
        creds = credentials.credentials
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            credentials.credentials = creds
            credentials.save()
        service = discovery.build(
            API_SERVICE_NAME, API_VERSION, credentials=creds)

        self._service = service
        return True, ''

    @exception_handler
    def get_calendars(
        self, sync_token=None, next_page_token: str = None
    ) -> Tuple[bool, dict, str]:

        main_parameters = ['kind', 'etag']
        item_parameters = ['id', ]

        request = self._service.calendarList().list(
            syncToken=sync_token,
            pageToken=next_page_token,
        )
        response = request.execute()

        logger.debug(response)

        result, message = dictionary_check(response, main_parameters, item_parameters)
        if not result:
            return False, None, message

        return True, response, ''

    @exception_handler
    def get_events_from_calendar(
        self, calendar_id: str, sync_token=None, next_page_token: str = None
    ) -> Tuple[bool, dict, str]:

        main_parameters = ['kind', 'etag']
        item_parameters = ['id', 'status']

        request = self._service.events().list(
            singleEvents=True,
            calendarId=calendar_id,
            pageToken=next_page_token,
            syncToken=sync_token,
        )
        response = request.execute()

        logger.debug(response)

        result, message = dictionary_check(response, main_parameters, item_parameters)
        if not result:
            return False, None, message

        return True, response, ''
