from django.urls import path

from rest_framework import routers
from core.authentication.views import SignUpViewSet, current_user, login
from core.services.views import ServicesViewSet
from core.views import ClientViewSet

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'signup/', SignUpViewSet, basename='signup')
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'services', ServicesViewSet, basename='services')

urlpatterns = [
    path("login/", login),
    path('current-user/', current_user)
]

urlpatterns += router.urls
