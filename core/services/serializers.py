from rest_framework import serializers
from core.models.models import Client
from core.services.models import Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('name', 'description', 'category', 'price', 'access', 'duration', 'client',)

    def validate_client(self, value):
        if not Client.objects.filter(pk=value.id).exists():
            raise serializers.ValidationError("The client does not exist.")
        return value
