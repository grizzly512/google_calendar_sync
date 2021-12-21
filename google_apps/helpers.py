import logging
import shutil
import time
import urllib
from typing import Tuple

from django.urls import reverse

from googleapiclient.errors import HttpError

from httplib2 import ServerNotFoundError

logger = logging.getLogger('google')


terminal_size = shutil.get_terminal_size()


def exception_handler(func):
    ''' Helps to catch google exceptions '''
    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as e:
            logger.error(f'Function {func}. Status {e.resp.status}, message {e.resp.message}')
            return False, None, f'Status {e.resp.status}, message {e.resp.message}'
        except ServerNotFoundError:
            logger.warning(f'Function {func}. Server error. Wait for a while...')
            time.sleep(5)
            return func(*args, **kwargs)
    return inner_function


def dictionary_check(
    response: dict, check_main_parameters: list, check_items: list = None
) -> Tuple[bool, str]:
    ''' Сhecks the server response for the required values '''
    if not isinstance(response, dict):
        return False, 'Response is not dictionary instance.'

    bool_list = [not(x in response) for x in check_main_parameters]
    if any(bool_list):
        return False, 'Response main parameters check fail'

    if check_items:
        for item in response['items']:

            bool_list = [not(x in item) for x in check_items]
            if any(bool_list):
                return False, 'Response items check fail'

    return True, ''


def build_url(*args, **kwargs) -> str:
    ''' Builds url with GET parameters '''
    get = kwargs.pop('get', {})
    url = reverse(*args, **kwargs)
    if get:
        url += '?' + urllib.parse.urlencode(get)
    return url


def dash_out(string_to_print: str) -> str:
    ''' Just decoration '''
    dash = '-' * int((terminal_size.columns - len(string_to_print) - 5) / 2)
    return f'\n [{dash} \033[31m\033[4m{string_to_print}\033[0m {dash}]'
