from django.shortcuts import render
from rest_framework import viewsets
from services.models import Service
from services.serializers import ServiceSerializer


class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
