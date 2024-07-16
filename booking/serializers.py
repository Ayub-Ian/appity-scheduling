from rest_framework import fields, serializers

from booking.models import Appointment

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['day_of_week','start_time','end_time']
