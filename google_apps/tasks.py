import logging
from datetime import timedelta

import celery

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .helpers import dash_out

logger = logging.getLogger('celery_tasks')
logger.propagate = False


@celery.decorators.periodic_task(
    name='google_apps.tasks.sync_companies',
    run_every=timedelta(seconds=float(settings.UPDATE_FREQUENCY)),
    queue='sync'
)
def sync_companies() -> None:
    logger.info(dash_out('START SYNC COMPANIES'))
    companies = [x.pk for x in apps.get_model(app_label='google_apps', model_name='Company').objects.all()]

    for company_id in companies:
        sync_company.apply_async(
            queue='sync_company', kwargs={'company_pk': company_id}, time_limit=settings.SYNC_TIMEOUT)

    logger.info(dash_out('STOP SYNC COMPANIES'))


@celery.decorators.task(name='google_apps.tasks.sync_company')
def sync_company(company_pk) -> None:

    # Getting Company from pk
    try:
        company = apps.get_model(app_label='google_apps', model_name='Company').objects.get(pk=company_pk)
    except ObjectDoesNotExist:
        logger.error(f'Company ID {company_pk} invalid')
        return
    logger.info(dash_out(f'START SYNC COMPANY ID - {company_pk}, name - {company.name}'))

    # Starting sync Halls
    result, message, response = company.sync_halls()

    if not result:
        logger.error(f'Company ID {company_pk} sync halls fail. MESSAGE "{message}", RESPONSE "{response}"')
        return

    company.last_sync = timezone.now()
    company.save()

    # Getting Halls from Company
    halls = apps.get_model(
        app_label='google_apps', model_name='Hall').objects.filter(company=company, disabled=False)

    for hall in halls:

        # Starting sync Halls
        result, message, response = hall.sync_events()
        if not result:
            logger.error(
                f'Hall ID {hall.pk} sync events fail. MESSAGE "{message}", RESPONSE "{response}"')

        else:
            # Checking intersections
            hall.check_intersection()
            hall.last_sync = timezone.now()
            hall.save()
            logger.info(f'Hall ID {hall.pk} sync events SUCCESS')

    logger.info(dash_out(f'END SYNC COMPANY ID - {company_pk}, name - {company.name}'))
