from django.db import models

from booking.models import Appointment
from core.models.models import Client
from core.utils import RandomId

class Service(models.Model):
    PRIVATE = 0
    PUBLIC = 1

    ACCESS_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    ]

    id = models.BigIntegerField(unique=True, default=RandomId('core.Services'), primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    category = models.CharField(max_length=100, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duration = models.IntegerField()
    access = models.CharField(max_length=50, choices=ACCESS_CHOICES, default=PUBLIC)
    appointment = models.ForeignKey(Appointment, related_name='services', on_delete=models.CASCADE,null=True, blank=True)
    client = models.ForeignKey(Client, related_name='services', on_delete=models.CASCADE)

    class Meta:
        app_label = 'core'
        verbose_name = 'services'

    def __str__(self):
        return self.name
