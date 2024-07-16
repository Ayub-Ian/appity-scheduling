from rest_framework import serializers
from services.models import Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'description', 'category', 'price', 'access', 'duration']
