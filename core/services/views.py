from django.shortcuts import render
from rest_framework import viewsets
from core.permissions import CustomPermissions, EndUserOnly
from core.services.models import Service
from core.services.serializers import ServiceSerializer


class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = (CustomPermissions, EndUserOnly,)
