from django.db import models
from django.conf import settings
from core.utils import RandomId

class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )
    id = models.BigIntegerField(unique=True, default=RandomId('booking.Appointment'), primary_key=True)
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)


    class Meta:
        app_label = 'booking'
        verbose_name = 'appointment'
        verbose_name_plural = 'appointments'

    def __str__(self):
        return f"{self.service.name} - {self.appointment_date}"



class Availability(models.Model):
    class DayOfWeek(models.IntegerChoices):
        SUNDAY = 1
        MONDAY = 2
        TUESDAY = 3
        WEDNESDAY =4
        THURSDAY = 5
        FRIDAY = 6
        SATURDAY = 7

    id = models.BigIntegerField(unique=True, default=RandomId('booking.Availability'), primary_key=True)
    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='availability', on_delete=models.CASCADE)

    class Meta:
        app_label = 'booking'
        verbose_name_plural = 'availabilities'

    def __str__(self):
        return f"{self.day_of_week}: {self.start_time} - {self.end_time}"
