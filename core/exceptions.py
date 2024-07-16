from typing import Optional

from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions as rest_exceptions
from rest_framework import status


class APIBadRequest(rest_exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _('Unable to perform the requested operation')
