from django import forms
from .models import Schedule, Subject, Teacher, Class


class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['day_of_week', 'hour_start', 'subject', 'class_fk', 'teacher']
        widgets = {
            'day_of_week': forms.Select(choices=[('Monday','Monday'),('Tuesday','Tuesday'),('Wednesday','Wednesday'),('Thursday','Thursday'),('Friday','Friday')]),
            'hour_start': forms.NumberInput(attrs={'min': 1, 'max': 12}),
        }
