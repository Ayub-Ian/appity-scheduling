from typing import Optional

from django.contrib.auth import user_login_failed

from core.models import AppUser


def match_user_for_invalid_authentication_input(input_value: str) -> Optional[AppUser]:
    return AppUser.objects.filter(email=input_value).first()


def appity_authenticate_user(email: str, password: str, request) -> Optional[AppUser]:
    matched_user = AppUser.objects.filter(email=email).first()  # type: AppUser
    is_active = getattr(matched_user, 'is_active', None)
    if not matched_user:
        return None
    if matched_user.check_password(password) and (is_active or is_active is None):
        return matched_user
    else:
        user_login_failed.send(
            sender=__name__,
            credentials=dict(
                email=email
            ),
            request=request
        )
        return None
