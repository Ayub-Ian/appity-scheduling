import datetime
from decimal import Decimal
from typing import Optional

import pycountry
from rest_framework.request import Request

from django.db import models
from django.http import HttpRequest
from django.utils import timezone
from django.contrib.sessions.models import Session
from django.contrib.auth.models import AbstractUser, UserManager
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property

from core.utils import RandomId, appity_create_user, appity_create_superuser

# Create your models here.
def get_default_currency():
    try:
        return Currency.objects.get(is_default=True)
    except (Currency.MultipleObjectsReturned, Currency.DoesNotExist):
        return None

class AppityUserManager(UserManager):
    def create_user(self, username=None, email=None, password=None, **extra_fields):
        # username is not used, default to None
        return appity_create_user(email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        # username is not used, default to None
        return appity_create_superuser(email, password, **extra_fields)


class AppUser(AbstractUser):
    id = models.BigIntegerField(unique=True, default=RandomId('core.AppUser'), primary_key=True)
    email_verified = models.BooleanField(default=False)
    email_last_verified_at = models.DateTimeField(blank=True, null=True, default=None)
    email = models.EmailField(unique=True)
    unverified_email = models.EmailField(blank=True, null=True, default=None)
    username = None
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    language = models.CharField(max_length=5, blank=True)
    is_superuser = models.BooleanField(default=False,
                                       help_text=('Designates that this user has all '
                                                  'permissions without explicitly assigning them.'),
                                       verbose_name='superuser status')
    mobile_phone_number = models.CharField(max_length=64, null=True, blank=True)
    unregistered = models.BooleanField(
        default=False,
        help_text=('Designates whether the user is pending invitation and not signed up yet.'),
    )

    objects = AppityUserManager()

    class Meta:
        app_label = 'core'
        verbose_name = 'user'
        verbose_name_plural = 'users'
        ordering = ['-date_joined']

    @cached_property
    def display(self):
        full_name = self.get_full_name()
        if full_name:
            return '{} ({}) #{}'.format(full_name, self.email, self.id)
        else:
            return '{} #{}'.format(self.email, self.id)

    def __str__(self):
        return self.display

    @property
    def managed_clients(self):
        excluded_clients_ids = UserToClient.objects.filter(user=self, invitation=True).values_list(
            'client__id', flat=True,
        )
        return self.clients.exclude(id__in=excluded_clients_ids).order_by('usertoclient')

    def get_active_client(self, request) -> Optional['Client']:
        if request:
            if self.is_admin:
                # LOG.error('Method should not be called for an admin user !!!')
                return None
            if request.user.is_anonymous or request.user.is_admin:
                # method is called from an admin user for a regular user, or by anonymous user,
                # we do not have active client information here
                return None

            active_client_id = None
            # attempt to retrieve active client based on request parameters
            if isinstance(request, Request):
                active_client_id = request.query_params.get('active_client')
            elif isinstance(request, HttpRequest):
                active_client_id = request.GET.get('active_client')

            if active_client_id:
                active_client = self.managed_clients.filter(id=active_client_id).first()
                if active_client:
                    if active_client_id != request.session.get('active_client_id'):
                        # save active client id in session if not already present
                        request.session['active_client_id'] = active_client_id
                        # reset permission cache since client might have changed
                        # active_client_changed.send(sender=self.__class__, user=self)
                    return active_client

            active_client_id = request.session.get('active_client_id')
            active_client = self.managed_clients.filter(id=active_client_id).first()
            if active_client:
                return active_client
            # LOG.info('Active client not found from request, returning first client for user {}'.format(self.display))
        else:
            # LOG.warning('No request provided, returning first client for user {}'.format(self.display))
            pass
        active_client = self.managed_clients.first()
        if request and active_client:
            request.session['active_client_id'] = active_client.id
        return active_client

    def get_full_name(self):
        """Returns the first_name plus the last_name, with a space in between."""
        if self.first_name and self.last_name:
            return '{} {}'.format(self.first_name, self.last_name)
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return None

    def get_short_name(self):
        """Returns the short name for the user."""
        return self.first_name

    # def email_user(self, subject, message, from_email=None, **kwargs):
    #     """Sends an email to this User."""
    #     send_mail(subject, message, from_email, [self.email], **kwargs)

    @property
    def can_impersonate(self):
        return self.is_staff

    @property
    def is_admin(self):
        return self.is_staff or self.is_superuser

    def get_session_expiration_seconds(self, remember=False):
        return settings.USER_LONG_SESSION_SECONDS if remember else settings.USER_SHORT_SESSION_SECONDS

    @property
    def clients_suspended(self) -> bool:
        return self.clients.filter(status=ClientStatus.suspended).count() > 0  # noqa: clients relation defined below

    @staticmethod
    def create_invited_user(email):
        return appity_create_user(
            email=email,
            unregistered=True,
            is_active=False,
        )

    def clear_sessions(self):
        Session.objects.filter(session_key__in=self.tokens.values('session__session_key')).delete()
        # at this point Appity tokens should've also been deleted but just to be sure run another delete query for them
        self.tokens.all().delete()



class ClientStatus:
    active = 'active'
    inactive = 'inactive'
    suspending = 'suspending'
    suspended = 'suspended'
    deleting = 'deleting'

    name_map = {
        active: _('Active'),
        inactive: _('Inactive'),
        suspending: _('Suspending'),
        suspended: _('Suspended'),
        deleting: _('Deleting'),
    }

    choices = [(active, _('Active')),
               (inactive, _('Inactive')),
               (suspended, _('Suspended')),
               (deleting, _('Deleting'))]

    blocking_statuses = [inactive, suspended, deleting]

class CurrencyManager(models.Manager):
    def get_default_or_first(self):
        return self.filter(is_default=True).first() or self.first()


class Currency(models.Model):
    code = models.CharField(max_length=3,
                            primary_key=True,
                            choices=[(i.alpha_3, i.alpha_3) for i in pycountry.currencies])
    rate = models.DecimalField(default=1, max_digits=12, decimal_places=6)
    is_default = models.BooleanField(default=False)

    objects = CurrencyManager()

    class Meta:
        verbose_name_plural = 'currencies'
        app_label = 'core'

    def to_dict(self):
        return dict(code=self.code, rate=self.rate, is_default=self.is_default)

    def save(self, *args, **kwargs):
        if self.is_default:
            # NOTE(tomo): Remove any other defaults
            Currency.objects.filter(is_default=True).exclude(code=self.code).update(is_default=False)
        return super(Currency, self).save(*args, **kwargs)

    def __str__(self):
        return self.code

class Client(models.Model):
    id = models.BigIntegerField(unique=True, default=RandomId('core.Client'), primary_key=True)
    company = models.CharField(max_length=127, blank=True, null=True)
    address1 = models.CharField(max_length=255)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=127)
    country = models.CharField(max_length=2, db_index=True, choices=[(country.alpha_2, country.name)
                                                                     for country in pycountry.countries])
    state = models.CharField(max_length=127, blank=True, null=True)
    zip_code = models.CharField(max_length=10)
    phone = models.CharField(max_length=64)
    fax = models.CharField(max_length=64, blank=True, null=True)
    date_created = models.DateTimeField(db_index=True, auto_now_add=True)
    # currency = models.ForeignKey(Currency, default=get_default_currency, on_delete=models.CASCADE)
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='clients', through='UserToClient')
    status = models.CharField(max_length=16, choices=ClientStatus.choices, db_index=True, default=ClientStatus.inactive)
    suspend_reason = models.CharField(max_length=16, db_index=True, default=None, null=True, blank=True)

    class Meta:
        app_label = 'core'
        ordering = ['-date_created']


class UserToClient(models.Model):
    """
    Map user accounts to Client objects and store permissions

    Also stores (email) communications and notifications settings.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    # roles = models.ManyToManyField('core.Role', related_name='users', blank=True)
    invitation = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'client')
        app_label = 'core'
