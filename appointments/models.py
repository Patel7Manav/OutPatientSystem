from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class Doctor(models.Model):
    name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    max_patients = models.PositiveIntegerField()

    def __str__(self):
        return self.name

class Appointment(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    patient_name = models.CharField(max_length=100)

    def __str__(self):
        return f"Appointment with Dr. {self.doctor.name} on {self.date} at {self.start_time} for {self.patient_name}"

    def clean(self):
        # Ensure appointments are within the specified time frame (2 pm to 7 pm)
        if not (self.start_time >= "14:00" and self.end_time <= "19:00"):
            raise ValidationError(_('Appointments must be between 2 pm and 7 pm.'))

        # Ensure appointments are in 30-minute slots
        time_difference = (self.end_time.hour * 60 + self.end_time.minute) - (self.start_time.hour * 60 + self.start_time.minute)
        if time_difference != 30:
            raise ValidationError(_('Appointments must be in 30-minute slots.'))

        # Check for conflicting appointments for the same doctor on the same date
        conflicting_appointments = Appointment.objects.filter(
            doctor=self.doctor,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk)

        if conflicting_appointments.exists():
            raise ValidationError(_('Conflicting appointment exists for this doctor.'))

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
