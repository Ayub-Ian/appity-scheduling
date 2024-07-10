from django.contrib.auth import BACKEND_SESSION_KEY
from django.contrib.auth import HASH_SESSION_KEY
from django.contrib.auth import SESSION_KEY
from django.utils.deprecation import MiddlewareMixin

from core.authentication.token_authentication import TokenAuthentication
from core.models import AppUser


class TokenAuthenticationMiddleware(MiddlewareMixin):
    @staticmethod
    def process_request(request):
        if not TokenAuthentication.has_fleio_token(request):
            return

        user_id = TokenAuthentication.get_user_id_from_header(request)
        if user_id:
            user = AppUser.objects.filter(id=user_id).first()
            if user:
                request.session[SESSION_KEY] = user_id
                request.session[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.AllowAllUsersModelBackend'
                request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()


        # # ensure we have user info in session if a Fleio token is present since django needs it sometimes
        # if not {SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY}.issubset(request.session.keys()):
        #     # set user in session
        #     user_id = TokenAuthentication.get_user_id_from_header(request)
        #     if user_id:
        #         user = AppUser.objects.filter(id=user_id).first()
        #         if user:
        #             request.session[SESSION_KEY] = user_id
        #             request.session[BACKEND_SESSION_KEY] = 'django.contrib.auth.backends.AllowAllUsersModelBackend'
        #             request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()
