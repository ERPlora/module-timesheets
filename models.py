from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models.base import HubBaseModel


class TimesheetsSettings(HubBaseModel):
    default_billable = models.BooleanField(default=True, verbose_name=_('Default Billable'))
    require_approval = models.BooleanField(default=True, verbose_name=_('Require Approval'))
    approval_period = models.CharField(
        max_length=20,
        choices=[
            ('weekly', _('Weekly')),
            ('biweekly', _('Bi-weekly')),
            ('monthly', _('Monthly')),
        ],
        default='weekly',
        verbose_name=_('Approval Period'),
    )

    class Meta(HubBaseModel.Meta):
        db_table = 'timesheets_settings'
        unique_together = [('hub_id',)]

    def __str__(self):
        return f'TimesheetsSettings (hub={self.hub_id})'


class HourlyRate(HubBaseModel):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_('Rate'))
    employee = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='hourly_rates',
        verbose_name=_('Employee'),
    )
    is_default = models.BooleanField(default=False, verbose_name=_('Is Default'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))

    class Meta(HubBaseModel.Meta):
        db_table = 'timesheets_hourly_rate'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.rate}/h)'


class TimeEntry(HubBaseModel):
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('submitted', _('Submitted')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    employee = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.CASCADE,
        related_name='time_entries_ts',
        verbose_name=_('Employee'),
    )
    date = models.DateField(verbose_name=_('Date'))
    start_time = models.TimeField(null=True, blank=True, verbose_name=_('Start Time'))
    end_time = models.TimeField(null=True, blank=True, verbose_name=_('End Time'))
    duration_minutes = models.PositiveIntegerField(verbose_name=_('Duration in minutes'))
    description = models.TextField(verbose_name=_('Description'))
    is_billable = models.BooleanField(default=True, verbose_name=_('Is Billable'))
    hourly_rate = models.ForeignKey(
        HourlyRate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='time_entries',
        verbose_name=_('Hourly Rate'),
    )
    rate_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name=_('Rate Amount'),
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='draft',
        verbose_name=_('Status'),
    )
    project_name = models.CharField(max_length=200, blank=True, verbose_name=_('Project'))
    client_name = models.CharField(max_length=200, blank=True, verbose_name=_('Client'))

    class Meta(HubBaseModel.Meta):
        db_table = 'timesheets_time_entry'
        ordering = ['-date', '-start_time']

    def __str__(self):
        return f'{self.employee} - {self.date} ({self.duration_minutes}m)'

    @property
    def duration_hours(self):
        return self.duration_minutes / 60

    @property
    def total_amount(self):
        if self.rate_amount and self.duration_minutes:
            return (self.rate_amount * self.duration_minutes) / 60
        return None


class TimesheetApproval(HubBaseModel):
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    employee = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.CASCADE,
        related_name='timesheet_approvals',
        verbose_name=_('Employee'),
    )
    period_start = models.DateField(verbose_name=_('Period Start'))
    period_end = models.DateField(verbose_name=_('Period End'))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name=_('Status'),
    )
    approved_by = models.ForeignKey(
        'accounts.LocalUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_timesheets',
        verbose_name=_('Approved By'),
    )
    total_minutes = models.PositiveIntegerField(default=0, verbose_name=_('Total Minutes'))
    billable_minutes = models.PositiveIntegerField(default=0, verbose_name=_('Billable Minutes'))
    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    class Meta(HubBaseModel.Meta):
        db_table = 'timesheets_approval'
        ordering = ['-period_start']

    def __str__(self):
        return f'{self.employee} ({self.period_start} - {self.period_end})'
