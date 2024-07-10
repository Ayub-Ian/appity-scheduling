import binascii
import os
from typing import Optional

from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.db import models
from django.utils import timezone

from core.models.models import AppUser



class AppityTokenManager(models.Manager):
    def get_frontend_appity_token(self, user, session_id) -> Optional['AppityToken']:
        return self.filter(user=user, session_id=session_id, frontend=True).first()


class AppityToken(models.Model):
    token = models.CharField(max_length=40, db_index=True, null=False, blank=False, editable=False, unique=True)
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, null=False, blank=False, related_name='tokens')
    created_at = models.DateTimeField(auto_now_add=True)
    expire_at = models.DateTimeField(default=None, null=True, blank=True)
    frontend = models.BooleanField(default=False)
    display_name = models.CharField(max_length=255, default=None, null=True, blank=True)
    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, default=None, null=True, blank=True, db_index=True,
    )

    objects =AppityTokenManager()

    class Meta:
        verbose_name = 'Appity-Token'


    @property
    def is_expired(self) -> bool:
        if self.expire_at:
            return self.expire_at < timezone.now()
        else:
            return False

    @property
    def expiry_seconds(self) -> Optional[int]:
        if self.expire_at:
            return int((self.expire_at - timezone.now()).total_seconds())
        return None

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if (not update_fields or 'token' in update_fields) and not self.token:
            self.token = self.user.email[:2] + binascii.hexlify(os.urandom(19)).decode()
        return super(AppityToken, self).save(
            force_insert=force_insert, force_update=force_update, update_fields=update_fields,
        )

    def get_info(self, session: SessionStore, force_expire_at_browser_close=False):
        """
        Retrieves token and related session info for the browser
        :param session: session used for authentication
        :param force_expire_at_browser_close: disregard session expiration to ensure token is removed client-side at
        browser close
        :return: dictionary with token related information
        """
        if self.session_id != session.session_key:
            # return data only when Appity token and session match
            return dict(
                token=None,
                expire_at=None,
                expire_at_browser_close=None,
                expiry_seconds=None,
                short_session_seconds=None,
                long_session_seconds=None,
            )

        return dict(
            token=self.token,
            expire_at=self.expire_at,
            expire_at_browser_close=force_expire_at_browser_close or session.get_expire_at_browser_close(),
            expiry_seconds=self.expiry_seconds,
            short_session_seconds=self.user.get_session_expiration_seconds(remember=False),
            long_session_seconds=self.user.get_session_expiration_seconds(remember=True),
        )

    def __str__(self):
        return '{}'.format(self.token)
