"""Tests for timesheets models."""
import pytest
from decimal import Decimal
from django.utils import timezone

from timesheets.models import TimeEntry, HourlyRate, TimesheetsSettings, TimesheetApproval


@pytest.mark.django_db
class TestHourlyRate:
    """HourlyRate model tests."""

    def test_create(self, hourly_rate):
        """Test HourlyRate creation."""
        assert hourly_rate.pk is not None
        assert hourly_rate.is_deleted is False

    def test_str(self, hourly_rate):
        """Test string representation."""
        result = str(hourly_rate)
        assert 'Standard Rate' in result
        assert '50.00' in result

    def test_soft_delete(self, hourly_rate):
        """Test soft delete."""
        pk = hourly_rate.pk
        hourly_rate.is_deleted = True
        hourly_rate.deleted_at = timezone.now()
        hourly_rate.save()
        assert not HourlyRate.objects.filter(pk=pk).exists()
        assert HourlyRate.all_objects.filter(pk=pk).exists()


@pytest.mark.django_db
class TestTimeEntry:
    """TimeEntry model tests."""

    def test_create(self, time_entry):
        """Test TimeEntry creation."""
        assert time_entry.pk is not None
        assert time_entry.is_deleted is False

    def test_str(self, time_entry):
        """Test string representation."""
        assert str(time_entry) is not None
        assert len(str(time_entry)) > 0

    def test_duration_hours(self, time_entry):
        """Test duration_hours property."""
        assert time_entry.duration_hours == 2.0

    def test_total_amount(self, time_entry):
        """Test total_amount property."""
        expected = (Decimal('50.00') * 120) / 60
        assert time_entry.total_amount == expected

    def test_total_amount_none(self, hub_id, admin_user):
        """Test total_amount returns None when no rate."""
        entry = TimeEntry.objects.create(
            hub_id=hub_id,
            employee=admin_user,
            date=timezone.localdate(),
            duration_minutes=60,
            description='No rate entry',
        )
        assert entry.total_amount is None

    def test_soft_delete(self, time_entry):
        """Test soft delete."""
        pk = time_entry.pk
        time_entry.is_deleted = True
        time_entry.deleted_at = timezone.now()
        time_entry.save()
        assert not TimeEntry.objects.filter(pk=pk).exists()
        assert TimeEntry.all_objects.filter(pk=pk).exists()

    def test_queryset_excludes_deleted(self, hub_id, time_entry):
        """Test default queryset excludes deleted."""
        time_entry.is_deleted = True
        time_entry.deleted_at = timezone.now()
        time_entry.save()
        assert TimeEntry.objects.filter(hub_id=hub_id).count() == 0


@pytest.mark.django_db
class TestTimesheetsSettings:
    """TimesheetsSettings model tests."""

    def test_create(self, timesheets_settings):
        """Test TimesheetsSettings creation."""
        assert timesheets_settings.pk is not None
        assert timesheets_settings.default_billable is True
        assert timesheets_settings.require_approval is True
        assert timesheets_settings.approval_period == 'weekly'

    def test_str(self, timesheets_settings):
        """Test string representation."""
        assert str(timesheets_settings) is not None


@pytest.mark.django_db
class TestTimesheetApproval:
    """TimesheetApproval model tests."""

    def test_create(self, hub_id, admin_user):
        """Test TimesheetApproval creation."""
        today = timezone.localdate()
        approval = TimesheetApproval.objects.create(
            hub_id=hub_id,
            employee=admin_user,
            period_start=today,
            period_end=today,
            status='pending',
            total_minutes=480,
            billable_minutes=360,
        )
        assert approval.pk is not None
        assert approval.status == 'pending'

    def test_str(self, hub_id, admin_user):
        """Test string representation."""
        today = timezone.localdate()
        approval = TimesheetApproval.objects.create(
            hub_id=hub_id,
            employee=admin_user,
            period_start=today,
            period_end=today,
        )
        result = str(approval)
        assert str(today) in result

    def test_soft_delete(self, hub_id, admin_user):
        """Test soft delete."""
        today = timezone.localdate()
        approval = TimesheetApproval.objects.create(
            hub_id=hub_id,
            employee=admin_user,
            period_start=today,
            period_end=today,
        )
        pk = approval.pk
        approval.is_deleted = True
        approval.deleted_at = timezone.now()
        approval.save()
        assert not TimesheetApproval.objects.filter(pk=pk).exists()
        assert TimesheetApproval.all_objects.filter(pk=pk).exists()
