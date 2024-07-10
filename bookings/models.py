from django.db import models
from services.models import Service

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )
    service = models.ForeignKey(Service, related_name='appointments', on_delete=models.CASCADE)
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'core'
        verbose_name = 'appointment'
        verbose_name_plural = 'appointments'

    def __str__(self):
        return f"{self.service.name} - {self.appointment_date}"
