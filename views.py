"""
Timesheets Module Views
"""
import datetime
from decimal import Decimal

from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render as django_render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.accounts.decorators import login_required, permission_required
from apps.accounts.models import LocalUser
from apps.core.htmx import htmx_view
from apps.modules_runtime.navigation import with_module_nav

from .forms import TimeEntryForm, HourlyRateForm, TimesheetsSettingsForm
from .models import TimeEntry, TimesheetApproval, HourlyRate, TimesheetsSettings


def _hub_id(request):
    return request.session.get('hub_id')


def _get_settings(hub_id):
    """Get or create module settings."""
    obj, _ = TimesheetsSettings.objects.get_or_create(
        hub_id=hub_id,
        defaults={'default_billable': True, 'require_approval': True, 'approval_period': 'weekly'},
    )
    return obj


def _week_bounds(date=None):
    """Return (monday, sunday) for the week containing `date`."""
    if date is None:
        date = timezone.localdate()
    monday = date - datetime.timedelta(days=date.weekday())
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday


# ======================================================================
# My Time (index)
# ======================================================================

@login_required
@with_module_nav('timesheets', 'my_time')
@htmx_view('timesheets/pages/index.html', 'timesheets/partials/my_time.html')
def index(request):
    hub_id = _hub_id(request)
    local_user_id = request.session.get('local_user_id')

    # Determine which week to show
    week_offset = int(request.GET.get('week', 0))
    today = timezone.localdate()
    ref_date = today + datetime.timedelta(weeks=week_offset)
    monday, sunday = _week_bounds(ref_date)

    entries = TimeEntry.objects.filter(
        hub_id=hub_id,
        employee_id=local_user_id,
        is_deleted=False,
        date__gte=monday,
        date__lte=sunday,
    ).order_by('date', 'start_time')

    # Build day-by-day structure
    days = []
    for i in range(7):
        day_date = monday + datetime.timedelta(days=i)
        day_entries = [e for e in entries if e.date == day_date]
        day_total = sum(e.duration_minutes for e in day_entries)
        days.append({
            'date': day_date,
            'entries': day_entries,
            'total_minutes': day_total,
            'total_hours': round(day_total / 60, 1) if day_total else 0,
            'is_today': day_date == today,
        })

    total_minutes = sum(d['total_minutes'] for d in days)
    billable_entries = [e for e in entries if e.is_billable]
    billable_minutes = sum(e.duration_minutes for e in billable_entries)

    return {
        'days': days,
        'monday': monday,
        'sunday': sunday,
        'week_offset': week_offset,
        'total_minutes': total_minutes,
        'total_hours': round(total_minutes / 60, 1) if total_minutes else 0,
        'billable_minutes': billable_minutes,
        'billable_hours': round(billable_minutes / 60, 1) if billable_minutes else 0,
        'entries_count': len(entries),
    }


# ======================================================================
# Time Entry CRUD
# ======================================================================

@login_required
@htmx_view('timesheets/pages/time_entry_form.html', 'timesheets/partials/time_entry_form.html')
def time_entry_create(request):
    hub_id = _hub_id(request)
    local_user_id = request.session.get('local_user_id')
    settings = _get_settings(hub_id)

    rates = HourlyRate.objects.filter(hub_id=hub_id, is_deleted=False, is_active=True)

    if request.method == 'POST':
        form = TimeEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.hub_id = hub_id
            entry.employee_id = local_user_id
            if entry.hourly_rate and not entry.rate_amount:
                entry.rate_amount = entry.hourly_rate.rate
            entry.save()
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('timesheets:index')
            return response
    else:
        initial = {
            'date': timezone.localdate(),
            'is_billable': settings.default_billable,
        }
        form = TimeEntryForm(initial=initial)

    form.fields['hourly_rate'].queryset = rates
    return {'form': form, 'rates': rates}


@login_required
@htmx_view('timesheets/pages/time_entry_form.html', 'timesheets/partials/time_entry_form.html')
def time_entry_edit(request, pk):
    hub_id = _hub_id(request)
    entry = get_object_or_404(TimeEntry, pk=pk, hub_id=hub_id, is_deleted=False)
    rates = HourlyRate.objects.filter(hub_id=hub_id, is_deleted=False, is_active=True)

    if request.method == 'POST':
        form = TimeEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)
            if entry.hourly_rate and not entry.rate_amount:
                entry.rate_amount = entry.hourly_rate.rate
            entry.save()
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('timesheets:index')
            return response
    else:
        form = TimeEntryForm(instance=entry)

    form.fields['hourly_rate'].queryset = rates
    return {'form': form, 'entry': entry, 'rates': rates}


@login_required
@require_POST
def time_entry_delete(request, pk):
    hub_id = _hub_id(request)
    entry = get_object_or_404(TimeEntry, pk=pk, hub_id=hub_id, is_deleted=False)
    entry.is_deleted = True
    entry.deleted_at = timezone.now()
    entry.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('timesheets:index')
    return response


@login_required
@require_POST
def time_entry_submit(request, pk):
    hub_id = _hub_id(request)
    entry = get_object_or_404(TimeEntry, pk=pk, hub_id=hub_id, is_deleted=False)
    if entry.status == 'draft':
        entry.status = 'submitted'
        entry.save(update_fields=['status', 'updated_at'])
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('timesheets:index')
    return response


# ======================================================================
# Approvals
# ======================================================================

@login_required
@permission_required('timesheets.approve_timesheet')
@with_module_nav('timesheets', 'approvals')
@htmx_view('timesheets/pages/approvals.html', 'timesheets/partials/approvals.html')
def approvals(request):
    hub_id = _hub_id(request)

    pending = TimesheetApproval.objects.filter(
        hub_id=hub_id, is_deleted=False, status='pending',
    ).select_related('employee')

    submitted_entries = TimeEntry.objects.filter(
        hub_id=hub_id, is_deleted=False, status='submitted',
    ).select_related('employee').order_by('employee__name', 'date')

    return {
        'pending_approvals': pending,
        'submitted_entries': submitted_entries,
    }


@login_required
@permission_required('timesheets.approve_timesheet')
@require_POST
def approval_action(request, pk):
    hub_id = _hub_id(request)
    local_user_id = request.session.get('local_user_id')
    action = request.POST.get('action', '')

    entry = get_object_or_404(TimeEntry, pk=pk, hub_id=hub_id, is_deleted=False)

    if action == 'approve' and entry.status == 'submitted':
        entry.status = 'approved'
        entry.save(update_fields=['status', 'updated_at'])
    elif action == 'reject' and entry.status == 'submitted':
        entry.status = 'rejected'
        entry.save(update_fields=['status', 'updated_at'])

    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('timesheets:approvals')
    return response


# ======================================================================
# Reports
# ======================================================================

@login_required
@permission_required('timesheets.view_reports')
@with_module_nav('timesheets', 'reports')
@htmx_view('timesheets/pages/reports.html', 'timesheets/partials/reports.html')
def reports(request):
    hub_id = _hub_id(request)

    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    filter_employee = request.GET.get('employee', '')

    qs = TimeEntry.objects.filter(hub_id=hub_id, is_deleted=False)

    if date_from:
        qs = qs.filter(date__gte=date_from)
    else:
        # Default: current month
        today = timezone.localdate()
        date_from = today.replace(day=1).isoformat()
        qs = qs.filter(date__gte=date_from)

    if date_to:
        qs = qs.filter(date__lte=date_to)

    if filter_employee:
        qs = qs.filter(employee_id=filter_employee)

    # Summaries
    total_minutes = qs.aggregate(total=Sum('duration_minutes'))['total'] or 0
    billable_qs = qs.filter(is_billable=True)
    billable_minutes = billable_qs.aggregate(total=Sum('duration_minutes'))['total'] or 0
    non_billable_minutes = total_minutes - billable_minutes

    # By employee
    by_employee = []
    employee_ids = qs.values_list('employee_id', flat=True).distinct()
    for eid in employee_ids:
        emp_entries = qs.filter(employee_id=eid)
        emp_total = emp_entries.aggregate(total=Sum('duration_minutes'))['total'] or 0
        emp_billable = emp_entries.filter(is_billable=True).aggregate(total=Sum('duration_minutes'))['total'] or 0
        emp = emp_entries.first()
        emp_name = emp.employee.name if emp and hasattr(emp, 'employee') and emp.employee else str(eid)
        by_employee.append({
            'employee_id': eid,
            'employee_name': emp_name,
            'total_minutes': emp_total,
            'total_hours': round(emp_total / 60, 1),
            'billable_minutes': emp_billable,
            'billable_hours': round(emp_billable / 60, 1),
        })

    # By project
    by_project = []
    project_names = qs.exclude(project_name='').values_list('project_name', flat=True).distinct()
    for pname in project_names:
        proj_entries = qs.filter(project_name=pname)
        proj_total = proj_entries.aggregate(total=Sum('duration_minutes'))['total'] or 0
        proj_billable = proj_entries.filter(is_billable=True).aggregate(total=Sum('duration_minutes'))['total'] or 0
        by_project.append({
            'project_name': pname,
            'total_minutes': proj_total,
            'total_hours': round(proj_total / 60, 1),
            'billable_minutes': proj_billable,
            'billable_hours': round(proj_billable / 60, 1),
        })

    employees = LocalUser.objects.filter(hub_id=hub_id, is_active=True).order_by('name')

    return {
        'total_minutes': total_minutes,
        'total_hours': round(total_minutes / 60, 1) if total_minutes else 0,
        'billable_minutes': billable_minutes,
        'billable_hours': round(billable_minutes / 60, 1) if billable_minutes else 0,
        'non_billable_minutes': non_billable_minutes,
        'non_billable_hours': round(non_billable_minutes / 60, 1) if non_billable_minutes else 0,
        'by_employee': by_employee,
        'by_project': by_project,
        'date_from': date_from,
        'date_to': date_to,
        'filter_employee': filter_employee,
        'employees': employees,
    }


# ======================================================================
# Rates
# ======================================================================

@login_required
@permission_required('timesheets.manage_rates')
@with_module_nav('timesheets', 'rates')
@htmx_view('timesheets/pages/rates.html', 'timesheets/partials/rates.html')
def rates_list(request):
    hub_id = _hub_id(request)
    rates = HourlyRate.objects.filter(hub_id=hub_id, is_deleted=False)
    return {'rates': rates}


@login_required
@permission_required('timesheets.manage_rates')
@htmx_view('timesheets/pages/rate_form.html', 'timesheets/partials/rate_form.html')
def rate_create(request):
    hub_id = _hub_id(request)
    employees = LocalUser.objects.filter(hub_id=hub_id, is_active=True).order_by('name')

    if request.method == 'POST':
        form = HourlyRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.hub_id = hub_id
            rate.save()
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('timesheets:rates')
            return response
    else:
        form = HourlyRateForm()

    form.fields['employee'].queryset = employees
    return {'form': form}


@login_required
@permission_required('timesheets.manage_rates')
@htmx_view('timesheets/pages/rate_form.html', 'timesheets/partials/rate_form.html')
def rate_edit(request, pk):
    hub_id = _hub_id(request)
    rate = get_object_or_404(HourlyRate, pk=pk, hub_id=hub_id, is_deleted=False)
    employees = LocalUser.objects.filter(hub_id=hub_id, is_active=True).order_by('name')

    if request.method == 'POST':
        form = HourlyRateForm(request.POST, instance=rate)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('timesheets:rates')
            return response
    else:
        form = HourlyRateForm(instance=rate)

    form.fields['employee'].queryset = employees
    return {'form': form, 'rate': rate}


@login_required
@permission_required('timesheets.manage_rates')
@require_POST
def rate_delete(request, pk):
    hub_id = _hub_id(request)
    rate = get_object_or_404(HourlyRate, pk=pk, hub_id=hub_id, is_deleted=False)
    rate.is_deleted = True
    rate.deleted_at = timezone.now()
    rate.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])
    response = HttpResponse(status=204)
    response['HX-Redirect'] = reverse('timesheets:rates')
    return response


# ======================================================================
# Settings
# ======================================================================

@login_required
@permission_required('timesheets.view_settings')
@with_module_nav('timesheets', 'settings')
@htmx_view('timesheets/pages/settings.html', 'timesheets/partials/settings.html')
def settings_view(request):
    hub_id = _hub_id(request)
    settings = _get_settings(hub_id)

    if request.method == 'POST':
        form = TimesheetsSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            response = HttpResponse(status=204)
            response['HX-Redirect'] = reverse('timesheets:settings')
            return response
    else:
        form = TimesheetsSettingsForm(instance=settings)

    return {'form': form, 'settings': settings}
