import logging

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _

from model_utils.models import TimeStampedModel, UUIDModel

from picklefield.fields import PickledObjectField


logger = logging.getLogger('google')


class GoogleCredentials(TimeStampedModel):
    ''' Google credential '''
    credentials = PickledObjectField(null=True, blank=True)

    user = models.OneToOneField(
        User,
        related_name='credentials',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _('Google Credentials')
        verbose_name_plural = _('Google Credentials')

    def __str__(self):
        if self.credentials:
            try:
                return f'Credentials modified: {self.modified} for user: {self.user}'
            except ObjectDoesNotExist:
                return 'Credentials not related to any user'
        else:
            return 'Credentials not set'


class GoogleBaseModel(UUIDModel):
    ''' Google Base model '''

    name = models.CharField(
        _('Name'), max_length=120, blank=False)

    description = models.TextField(
        _('Description'), blank=True, default='')

    next_sync_token = models.CharField(
        _('Sync Token'), max_length=120, blank=True, default='')

    google_id = models.CharField(
        _('Google token'), max_length=120, blank=True, default='')

    last_sync = models.DateTimeField(
        _('Last Sync'), blank=True, null=True)

    last_response = models.JSONField(
        _('Last Response'), null=True, blank=True,
        default=dict)

    class Meta:
        abstract = True
