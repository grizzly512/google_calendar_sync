import logging

logger = logging.getLogger('tests')


def mocked_google_get_service(credentials):
    logger.info(f'Mocking Google get_service for user: {credentials.user.username}')

    return True, ''


def mocked_google_get_calendars(sync_token=None, next_page_token: str = None):
    logger.info(f'Mocking Google get_calendars Sync token :{sync_token} Page token: {next_page_token}')
    response = {
        'kind': 'calendar#calendarList',
        'etag': '"p328a51uaujmv80g"',
        'nextSyncToken': 'CJCih8r07fQCEhtraGFadGataXJvdi5yaW5hdEBnbWFpbC5jb20=',
        'items': [
            {
                'kind': 'calendar#calendarListEntry',
                'etag': '"1639753286053000"',
                'id': 'fami6234502460287942@group.calendar.google.com',
                'summary': 'Test Calendar 1',
                'description': 'Some description',
            },
            {
                'kind': 'calendar#calendarListEntry',
                'etag': '"16392215321353000"',
                'id': 'fsddfi134sfsd287942@group.calendar.google.com',
                'summary': 'Test Calendar 2',
                'description': 'Some description',
            }]
    }
    return True, response, ''


def mocked_google_get_events_from_calendar(
        calendar_id: str, sync_token=None, next_page_token: str = None):
    logger.info(
        f'Mocking Google get_events_from_calendar Calendar ID {calendar_id}  Sync token :{sync_token} \
        Page token: {next_page_token}')

    response = {
        'kind': 'calendar#events',
        'etag': '"p328a51uaujmv80g"',
        'nextSyncToken': 'CJCihasdawd@3traGFadGataXJvdi5yaW5hdEBnbWFpbC5jb20=',
        'summary': 'Test Calendar 1',
        'items': [
            {
                'kind': 'calendar#event',
                'etag': '"163975323286053000"',
                'id': '0d0msedhv1tq5avasdw2br8skrm7hm3',
                'summary': 'Test Event 1',
                'description': 'Some description',
                'start': {
                    'dateTime': '2021-12-17T16:30:00+03:00',
                    'timeZone': 'Europe/Moscow'
                },
                'end': {
                    'dateTime': '2021-12-17T17:30:00+03:00',
                    'timeZone': 'Europe/Moscow'
                },
            },
            {
                'kind': 'calendar#event',
                'etag': '"16397532323286053000"',
                'id': '0d0msedhv1525tq5avasdw2br8skrm7hm3',
                'summary': 'Test Event 2',
                'description': 'Some description',
                'start': {
                    'dateTime': '2021-12-17T16:00:00+03:00',
                    'timeZone': 'Europe/Moscow'
                },
                'end': {
                    'dateTime': '2021-12-17T17:00:00+03:00',
                    'timeZone': 'Europe/Moscow'
                },
            },
            {
                'kind': 'calendar#event',
                'etag': '"1639723532323286053000"',
                'id': '0d0msedhv23451525tq5avasdw2br8skrm7hm3',
                'summary': 'Test Event 3',
                'description': 'Some description',
                'start': {
                    'dateTime': '2021-12-17T20:00:00+03:00',
                    'timeZone': 'Europe/Moscow'
                },
                'end': {
                    'dateTime': '2021-12-17T21:00:00+03:00',
                    'timeZone': 'Europe/Moscow'
                },
            },
        ]
    }

    return True, response, ''
