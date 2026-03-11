from django import forms
from django.utils.translation import gettext_lazy as _

from .models import TimeEntry, HourlyRate, TimesheetsSettings


class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = [
            'date', 'start_time', 'end_time', 'duration_minutes',
            'description', 'is_billable', 'hourly_rate', 'rate_amount',
            'project_name', 'client_name',
        ]
        widgets = {
            'date': forms.DateInput(attrs={'class': 'input input-sm w-full', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'input input-sm w-full', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'input input-sm w-full', 'type': 'time'}),
            'duration_minutes': forms.NumberInput(attrs={'class': 'input input-sm w-full', 'min': '1', 'placeholder': '60'}),
            'description': forms.Textarea(attrs={'class': 'textarea textarea-sm w-full', 'rows': 3}),
            'is_billable': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'hourly_rate': forms.Select(attrs={'class': 'select select-sm w-full'}),
            'rate_amount': forms.NumberInput(attrs={'class': 'input input-sm w-full', 'step': '0.01'}),
            'project_name': forms.TextInput(attrs={'class': 'input input-sm w-full'}),
            'client_name': forms.TextInput(attrs={'class': 'input input-sm w-full'}),
        }


class HourlyRateForm(forms.ModelForm):
    class Meta:
        model = HourlyRate
        fields = ['name', 'rate', 'employee', 'is_default', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input input-sm w-full'}),
            'rate': forms.NumberInput(attrs={'class': 'input input-sm w-full', 'step': '0.01', 'min': '0'}),
            'employee': forms.Select(attrs={'class': 'select select-sm w-full'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'toggle'}),
        }


class TimesheetsSettingsForm(forms.ModelForm):
    class Meta:
        model = TimesheetsSettings
        fields = ['default_billable', 'require_approval', 'approval_period']
        widgets = {
            'default_billable': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'require_approval': forms.CheckboxInput(attrs={'class': 'toggle'}),
            'approval_period': forms.Select(attrs={'class': 'select select-sm w-full'}),
        }
