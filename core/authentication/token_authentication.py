from datetime import timedelta
from typing import Optional

from django.contrib import auth
from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import authentication
from rest_framework.authentication import get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.request import Request

# from common.logger import get_fleio_logger
from core.models.appity_token import AppityToken

# from fleio.core.models import FleioOtpToken
# from fleio.core.utils import match_session_ip_or_401
# from fleio.logger.decorators import log_periodic_task
# from fleio.logger.models import PeriodicTaskLog

# LOG = get_fleio_logger(__name__)
OTP_TOKEN_MAX_LIFETIME_SECONDS = 600


def get_frontend_token(user, request) -> Optional[str]:
    token = AppityToken.objects.filter(user=user, session_id=request.session.session_key, frontend=True).first()
    if token:
        return token.token
    else:
        return None


def get_token_from_request(request) -> Optional[AppityToken]:
    if 'impersonate' in request.session and request.get_full_path().startswith('/api/'):
        # request from impersonated end user, return user frontend token
        fleio_token = AppityToken.objects.get_frontend_fleio_token(
            user=request.session['impersonate'],
            session_id=request.session.session_key,
        )
    elif isinstance(request.auth, AppityToken):
        fleio_token = request.auth
    else:
        fleio_token = None

    return fleio_token


def generate_otp_token_for_token(token: AppityToken) -> Optional[str]:
    # generate new token
    otp_token = FleioOtpToken.objects.create(
        fleio_token=token, expire_at=timezone.now() + timedelta(seconds=OTP_TOKEN_MAX_LIFETIME_SECONDS)
    )
    return otp_token.token


def generate_otp_token_for_request(request) -> Optional[str]:
    token = request.auth
    if token and isinstance(token, AppityToken):
        # delete existing expired tokens
        token.otp_tokens.filter(expire_at__isnull=False, expire_at__lt=timezone.now()).delete()
        # generate new token
        return generate_otp_token_for_token(token)

    return None


def set_expiry_date(token: AppityToken, seconds_until_expiration: int):
    expire_at = timezone.now() + timedelta(seconds=seconds_until_expiration)
    token.expire_at = expire_at
    token.save(update_fields=['expire_at'])


def initialize_frontend_token(
        user, request, seconds_until_expiration: Optional[int] = None,
) -> AppityToken:
    if not seconds_until_expiration:
        seconds_until_expiration = user.get_session_expiration_seconds()
    with transaction.atomic():
        token, new_token = AppityToken.objects.get_or_create(
            frontend=True,
            session_id=request.session.session_key,
            user=user,
        )
        if not new_token and token.is_expired:
            # existing token expired, delete and recreate
            try:
                token.delete()
            except AppityToken.DoesNotExist:
                pass
            token, new_token = AppityToken.objects.get_or_create(
                frontend=True,
                session_id=request.session.session_key,
                user=user,
            )

        if new_token:
            set_expiry_date(token=token, seconds_until_expiration=seconds_until_expiration)

        return token


def clear_impersonation_frontend_token(impersonated_user, request):
    if impersonated_user:
        AppityToken.objects.filter(
            user=impersonated_user,
            frontend=True,
            session_id=request.session.session_key
        ).delete()


def initialize_frontend_token_for_impersonation(impersonated_user, request):
    # on a new impersonation, clear old frontend token related to current session if it exists and generate a new one
    clear_impersonation_frontend_token(impersonated_user=impersonated_user, request=request)
    return initialize_frontend_token(
        user=impersonated_user,
        request=request,
        seconds_until_expiration=impersonated_user.get_session_expiration_seconds(),
    )


def extend_frontend_session(user, fleio_token: AppityToken, request, remember=False) -> AppityToken:
    """Extends frontend session by creating a new Django session & Fleio frontend token for a given user"""
    if not fleio_token.frontend:
        raise APIConflict(_('Cannot extend session for non-frontend token.'))

    # add a new session
    old_session_data = request.session.load()
    request.session.create()
    request.session.session_data = old_session_data

    session_expiration_seconds = user.get_session_expiration_seconds(remember=remember)
    if remember:
        request.session.set_expiry(session_expiration_seconds)
    else:
        # setting 0 means session expires at browser close
        request.session.set_expiry(0)

    # create the new Fleio frontend token (it will use the newly created Django session)
    new_fleio_token = initialize_frontend_token(
        user=user,
        request=request,
        seconds_until_expiration=session_expiration_seconds,
    )
    request.auth = new_fleio_token
    request.session['fleio_token'] = new_fleio_token.token
    # save session_data
    request.session.save()
    return new_fleio_token


def token_login(request, user, seconds_until_expiration: Optional[int] = None):
    request.session.flush()
    auth.login(request, user, backend='django.contrib.auth.backends.AllowAllUsersModelBackend')
    if request and request.session and request.session.session_key:
        token = initialize_frontend_token(
            user=user,
            request=request,
            seconds_until_expiration=seconds_until_expiration,
        )
        request.auth = token
        request.session['appity_token'] = token.token


# @log_periodic_task(task_name='Clear expired sessions task'
# def clear_expired_sessions(periodic_task_log: Optional[PeriodicTaskLog] = None):
#     LOG.fleio_activity('Starting to clear Django expired sessions and Fleio tokens.')
#     current_moment = timezone.now()
#     all_sessions = Session.objects.all()
#     all_expired_sessions = all_sessions.filter(expire_date__lt=current_moment)
#     # clear expired tokens or tokens that have related django session missing or expired
#     expired_tokens = AppityToken.objects.filter(
#         Q(expire_at__lt=current_moment) |
#         (Q(session_id__isnull=False) & (
#             ~Q(session_id__in=all_sessions.values('session_key')) |
#             Q(session_id__in=all_expired_sessions.values('session_key'))
#         ))
#     )
#     expired_tokens_count = expired_tokens.count()
#     expired_tokens.delete()
#     if expired_tokens_count == 0:
#         LOG.fleio_activity('Did not find expired tokens.')
#     else:
#         LOG.fleio_activity('Deleted {} expired token(s).'.format(expired_tokens_count))
#     # also clear django expired sessions
#     expired_django_sessions_count = all_expired_sessions.count()
#     all_expired_sessions.delete()
#     if expired_django_sessions_count == 0:
#         LOG.fleio_activity('Did not find expired Django sessions.')
#     else:
#         LOG.fleio_activity('Deleted {} expired Django session(s).'.format(expired_django_sessions_count))

#     LOG.fleio_activity('Finished clearing Django expired sessions and Fleio tokens.')
#     periodic_task_log.summary = 'Django expired sessions and Fleio tokens cleared'


class TokenAuthentication(authentication.BaseAuthentication):
    keyword = 'Fleio-Token'

    @staticmethod
    def has_fleio_token(request) -> bool:
        auth_header = get_authorization_header(request).split()
        return len(auth_header) == 2 and auth_header[0].lower() == TokenAuthentication.keyword.lower().encode()

    @staticmethod
    def get_user_id_from_header(request) -> Optional[int]:
        auth_header = get_authorization_header(request).split()
        if TokenAuthentication.has_fleio_token(request=request):
            token = auth_header[1].decode()
            request_session = request.session
            db_token = AppityToken.objects.filter(
                token=token,
                session_id=request_session.session_key if request_session else None
            ).first()
            if db_token:
                if not db_token.is_expired:
                    return db_token.user_id
                else:
                    try:
                        db_token.delete()
                    except AppityToken.DoesNotExist:
                        pass

        return None

    @staticmethod
    def is_anonymous_view(request: Request) -> bool:
        try:
            view = request.parser_context.get('view')
            if hasattr(view, 'permission_classes'):
                permission_classes = getattr(view, 'permission_classes')
                if AllowAny in permission_classes:
                    return True
        except Exception:  # noqa
            # we are not interested in exception here, consider view not anonymous for any exception
            return False

        return False

    def authenticate(self, request):
        anonymous = TokenAuthentication.is_anonymous_view(request)
        auth_header = get_authorization_header(request).split()

        if not auth_header or auth_header[0].lower() != self.keyword.lower().encode():
            # fallback on otp token
            token = None
            if request.method in ['GET', 'POST']:
                token = request.query_params.get('fleio-token', None)
            if token:
                return self.authenticate_credentials(request, token, otp=True, anonymous=anonymous)
            return None

        if len(auth_header) == 1:
            if anonymous:
                # do not raise for anonymous view
                return None
            msg = _('Invalid token header. No credentials provided.')
            raise AuthenticationFailed(msg)
        elif len(auth_header) > 2:
            if anonymous:
                # do not raise for anonymous view
                return None
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise AuthenticationFailed(msg)

        try:
            token = auth_header[1].decode()
        except UnicodeError:
            if anonymous:
                # do not raise for anonymous view
                return None
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise AuthenticationFailed(msg)

        return self.authenticate_credentials(request, token, anonymous=anonymous)

    @staticmethod
    def authenticate_credentials(request: Request, token: str, otp: bool = False, anonymous: bool = False):
        try:
            if otp:
                db_token = AppityToken.objects.get(otp_tokens__token=token)

                # delete token since it was used
                otp_token = db_token.otp_tokens.get(token=token)
                otp_token.delete()
                if otp_token.is_expired:
                    if anonymous:
                        # do not raise for anonymous view
                        return None
                    raise AuthenticationFailed(_('Expired token.'))
            else:
                request_session = getattr(request, 'session', None)
                db_token = AppityToken.objects.get(
                    token=token,
                    session_id=request_session.session_key if request_session else None,
                )
        except AppityToken.DoesNotExist:
            if anonymous:
                # do not raise for anonymous view
                return None
            raise AuthenticationFailed(_('Invalid token.'))

        if db_token.is_expired:
            if db_token.frontend:
                # expired frontend tokens will be deleted in order to be regenerated during login process
                try:
                    db_token.delete()
                except AppityToken.DoesNotExist:
                    pass

            if anonymous:
                # do not raise for anonymous view
                return None
            raise AuthenticationFailed(_('Expired token.'))

        if not db_token.user.is_active:
            if anonymous:
                # do not raise for anonymous view
                return None
            raise AuthenticationFailed(_('User inactive or deleted.'))

        if not otp:
            # validate frontend token against session
            if db_token.frontend:
                session_token = request.session.get('fleio_token')
            else:
                session_token = None

            if session_token:
                # we only check if we have a session token - checking against no session token will prevent API calls
                # without session
                if {'impersonate', 'impersonator'}.issubset(request.session.keys()):
                    # we have an active impersonation, check
                    impersonator_id = request.session.get('impersonator')
                    user_id = request.session['impersonate']
                    impersonator_token = get_frontend_token(impersonator_id, request=request)

                    if not ((db_token.user.id in [user_id, impersonator_id]) and (impersonator_token == session_token)):
                        if anonymous:
                            # do not raise for anonymous view
                            return None
                        raise AuthenticationFailed(_('Mismatched token.'))
                elif session_token != db_token.token:
                    if anonymous:
                        # do not raise for anonymous view
                        return None
                    raise AuthenticationFailed(_('Mismatched token.'))

        # try:
        #     if db_token.frontend:
        #         match_session_ip_or_401(request, user=db_token.user, token=db_token)
        # except AuthenticationFailed:
        #     if anonymous:
        #         return None
        #     raise
        # else:
            return db_token.user, db_token

    def authenticate_header(self, request):
        return self.keyword
