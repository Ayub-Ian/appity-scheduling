from django.urls import path

from rest_framework import routers
from core.views import SignUpViewSet, current_user, login

router = routers.SimpleRouter(trailing_slash=False)
router.register(r'signup', SignUpViewSet, basename='signup')

urlpatterns = [
    path("login/", login),
    path('current-user', current_user)
]

urlpatterns += router.urls
