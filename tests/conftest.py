"""Pytest fixtures for timesheets module tests."""
import uuid
import pytest
from decimal import Decimal
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from apps.accounts.models import LocalUser
from apps.configuration.models import HubConfig, StoreConfig
from timesheets.models import TimeEntry, HourlyRate, TimesheetsSettings, TimesheetApproval


@pytest.fixture
def hub_id():
    """Test hub_id."""
    return uuid.uuid4()


@pytest.fixture
def configured_hub(db, hub_id):
    """Configure HubConfig with test hub_id."""
    HubConfig._clear_cache()
    config = HubConfig.get_config()
    config.hub_id = hub_id
    config.is_configured = True
    config.save()
    return config


@pytest.fixture
def store_config(db):
    """StoreConfig for testing."""
    config = StoreConfig.get_solo()
    config.business_name = 'Test Store'
    config.tax_rate = Decimal('21.00')
    config.is_configured = True
    config.save()
    return config


@pytest.fixture
def admin_user(db, hub_id):
    """Admin user for testing."""
    return LocalUser.objects.create(
        hub_id=hub_id,
        name='Admin User',
        email='admin@test.com',
        role='admin',
        pin_hash=make_password('1234'),
        is_active=True,
    )


@pytest.fixture
def employee_user(db, hub_id):
    """Employee user for testing."""
    return LocalUser.objects.create(
        hub_id=hub_id,
        name='Employee User',
        email='employee@test.com',
        role='employee',
        pin_hash=make_password('5678'),
        is_active=True,
    )


@pytest.fixture
def auth_client(client, admin_user, store_config):
    """Authenticated client with session."""
    session = client.session
    session['local_user_id'] = str(admin_user.id)
    session['user_name'] = admin_user.name
    session['user_email'] = admin_user.email
    session['user_role'] = admin_user.role
    session['hub_id'] = str(admin_user.hub_id)
    session['store_config_checked'] = True
    session.save()
    return client


@pytest.fixture
def hourly_rate(db, hub_id):
    """Create a test HourlyRate."""
    return HourlyRate.objects.create(
        hub_id=hub_id,
        name='Standard Rate',
        rate=Decimal('50.00'),
        is_default=True,
        is_active=True,
    )


@pytest.fixture
def time_entry(db, hub_id, admin_user, hourly_rate):
    """Create a test TimeEntry."""
    return TimeEntry.objects.create(
        hub_id=hub_id,
        employee=admin_user,
        date=timezone.localdate(),
        duration_minutes=120,
        description='Test time entry',
        is_billable=True,
        hourly_rate=hourly_rate,
        rate_amount=Decimal('50.00'),
        status='draft',
        project_name='Test Project',
        client_name='Test Client',
    )


@pytest.fixture
def timesheets_settings(db, hub_id):
    """Create test TimesheetsSettings."""
    return TimesheetsSettings.objects.create(
        hub_id=hub_id,
        default_billable=True,
        require_approval=True,
        approval_period='weekly',
    )
