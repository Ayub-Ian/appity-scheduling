from django.contrib import auth
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework import exceptions as rest_exceptions
from rest_framework import throttling
from rest_framework import permissions
from rest_framework import viewsets
from rest_framework.views import Response


from core.authentication.token_authentication import get_token_from_request, token_login
from core.authentication.utils import appity_authenticate_user
from core.models.models import AppUser, UserToClient
from core.authentication.serializers import LoginSerializer, SignUpSerializer
from core.utils import login_without_password

class LoginRateThrottle(throttling.AnonRateThrottle):
    scope = 'login'


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
@throttle_classes([LoginRateThrottle])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    data = serializer.validated_data

    user = appity_authenticate_user(
        email=data['email'],
        password=data['password'],
        request=request,
    )

    # ip, routable = get_client_ip(request)

    if user is None:
        raise rest_exceptions.AuthenticationFailed(detail=_('Incorrect email or password'))
    elif not user.is_active:
        raise rest_exceptions.AuthenticationFailed(detail=_('This account is inactive'))
    else:
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()

        remember_me = data.get('remember_me', False)
        session_expiration_seconds = user.get_session_expiration_seconds(remember_me)
        token_login(request, user, session_expiration_seconds)
        if remember_me:
            request.session.set_expiry(session_expiration_seconds)
        else:
            # setting 0 means session expires at browser close
            request.session.set_expiry(0)

        # request.session['ip'] = ip

        response_dict = {
            'user': get_current_user_info(request),
            # 'features': staff_active_features.all,
        }
        # if remember_sfa_token:
        #     response_dict['remember_sfa_token'] = remember_sfa_token
        return Response(response_dict)


def get_current_user_info(request):
    user = request.user
    appity_token = get_token_from_request(request=request)
    return {
        'id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'email': user.email,
        'language': user.language,
        'appity_token': appity_token.get_info(session=request.session) if appity_token else None,
    }


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def current_user(request):
    if request.user.is_authenticated :

        response = {
            'user': get_current_user_info(request),
            # 'features': staff_active_features.all,
            # 'formatting': {
            #     'currency': {
            #         'display_mode': formatting_settings.currency_display_mode,
            #         'min_fraction_digits': formatting_settings.currency_min_fraction_digits,
            #     },
            #     'date': {
            #         'date_format': formatting_settings.date_format,
            #         'date_time_format': formatting_settings.date_time_format,
            #     },
            # },
            # 'referrals_enabled': referral_settings.enable_referral_system,
            # 'notifications': notifications_count,
            # 'total_notifications': notifications_count,  # total that appears on my profile avatar

        }

        return Response(response)
    else:
        sign_on_data = {
            # 'features': staff_active_features.all,
        }

        return Response(sign_on_data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout(request):
    user = request.user

    if not user.is_authenticated:
        return Response(status=200)  # nothing should happen
    else:
        auth.logout(request)

    return Response({'detail': _('Logged out')})


class SignUpRateThrottle(throttling.AnonRateThrottle):
    key = None
    history = None
    scope = 'signup'

    def remove_last_history_item(self, request, view):
        if self.rate is not None:
            self.key = self.get_cache_key(request, view)
            if self.key is not None:
                self.history = self.cache.get(self.key, [])  # type: list
                self.history.pop()
                self.cache.set(self.key, self.history, self.duration)


class SignUpViewSet(viewsets.ViewSet):
    """New user account sign up API end-point."""

    permission_classes = (permissions.AllowAny,)
    throttle_classes = (SignUpRateThrottle,)

    def create(self, request):
        """Create a new user account."""
        # if not active_features.is_enabled('clients&users.signup'):
        #     if active_features.is_enabled('clients&users.invitations'):
        #         # allow signup through invitation if related feature is enabled but signup is not
        #         if not request.data.get('invitation_id') or not request.data.get('invitation_token'):
        #             raise NotFound()
        #     else:
        #         # both signup and invitations disabled
        #         raise NotFound()

        serializer = SignUpSerializer(data=request.data.copy(), context={'request': request})
        if not serializer.is_valid(raise_exception=False):
            SignUpRateThrottle().remove_last_history_item(request, self)
            raise rest_exceptions.ValidationError(serializer.errors)

        with transaction.atomic():
            user: AppUser = serializer.save()
            invitation_id = serializer.validated_data.get('invitation_id')
            invitation_token = serializer.validated_data.get('invitation_token')
            # if invitation_id and invitation_token:
            #     u2c = UserToClient.objects.filter(id=invitation_id, user=user).first()
            #     if u2c and u2c.invitation:
            #         pass
            #         # if invitation_token_generator.check_token(user_to_client=u2c, token=invitation_token):
            #         #     utils.login_without_password(request, user)
            #         #     u2c.invitation = False
            #         #     u2c.save(update_fields=['invitation'])
            #         #     # user accepted the invitation through email, thus we can mark his email as verified
            #         #     user.email_verified = True
            #         #     user.email_last_verified_at = timezone.now()
            #         #     user.save(update_fields=['email_verified', 'email_last_verified_at'])
            #         # else:
            #         #     raise APIBadRequest(_('Invitation token missing or invalid'))
            #     else:
            #         raise APIBadRequest(_('Invitation token missing or invalid'))
            # else:
            #     utils.login_without_password(request, user)

            login_without_password(request, user)
            response_obj = dict(
                user=get_current_user_info(request)
            )

        # if signup_settings.require_confirmation and not user.email_verified:
        #     # send confirmation email
        #     generate_verification_token_and_send(user=user)
        #     response_obj['needs_email_confirmation'] = signup_settings.require_confirmation

        # user_signed_up.send(sender=__name__, user=user, request=request)
        return Response(response_obj)
