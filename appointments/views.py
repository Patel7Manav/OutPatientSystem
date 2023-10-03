from .models import Doctor, Appointment
from .serializers import DoctorSerializer, AppointmentSerializer
import datetime
from rest_framework import generics, status
from rest_framework.response import Response
from datetime import datetime, timedelta, time
from django.core.exceptions import ValidationError
from django.http import QueryDict 
from django.db import IntegrityError

class AppointmentBooking(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer

    ALLOWED_START_TIMES = [
        time(14, 0),  # 2:00 PM
        time(14, 30), # 2:30 PM
        time(15, 0),  # 3:00 PM
        time(15, 30), # 3:30 PM
        time(16, 00),
        time(16,30),
        time(17,00),
        time(17,30),
        time(18,00)
        # Add more allowed start times as needed
    ]

    def validate_start_time(self, start_time):
        if start_time not in self.ALLOWED_START_TIMES:
            raise ValidationError("Invalid start time. Allowed start times are 2:00 PM, 2:30 PM, 3:00 PM and so on till 6 PM ")

    def create(self, request, *args, **kwargs):
        doctor_id = request.data.get('doctor')
        date_str = request.data.get('date')  # Date as string
        start_time_str = request.data.get('start_time')
        patient_name = request.data.get('patient_name')

        if patient_name is None:
            return Response(
                {"detail": "patient_name is a required field."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Check if start_time is provided
        if start_time_str is None:
            return Response(
                {"detail": "start_time is a required field."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert the date string to a datetime.date object
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {"detail": "Invalid date format. Use YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Convert the start_time string to a time object
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
        except ValueError:
            return Response(
                {"detail": "Invalid time format. Use HH:MM (24-hour format)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate the start time against the list of allowed start times
        self.validate_start_time(start_time)

        # Calculate the end time based on the start time and a fixed duration (e.g., 30 minutes)
        start_datetime = datetime.combine(date, start_time)
        end_datetime = start_datetime + timedelta(minutes=30)

        # Check for conflicting appointments within the allowed time gap
        conflicting_appointments = Appointment.objects.filter(
            doctor=doctor_id,
            date=date,
            start_time__lt=end_datetime.time(),
            start_time__gte=start_time,
            patient_name=patient_name,
        )

        if conflicting_appointments.exists():
            return Response(
                {"detail": "Conflicting appointment exists for this doctor within 30 minutes."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the Appointment object with end_time and save it
        appointment = Appointment(
            doctor_id=doctor_id,
            date=date,
            start_time=start_time,
            end_time=end_datetime.time(),  # Set the end_time
        )

        try:
            appointment.save()
        except IntegrityError:
            return Response(
                {"detail": "Conflicting appointment exists for this doctor within 30 minutes."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        serializer = self.get_serializer(appointment)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
     
class DoctorList(generics.ListAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class DoctorDetail(generics.RetrieveAPIView):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
