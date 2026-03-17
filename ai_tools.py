"""AI tools for the Timesheets module."""
from assistant.tools import AssistantTool, register_tool


# ==============================================================================
# HOURLY RATES
# ==============================================================================

@register_tool
class ListHourlyRates(AssistantTool):
    name = "list_hourly_rates"
    description = "List all hourly rates with their name, rate per hour, assigned employee, and active status."
    module_id = "timesheets"
    required_permission = "timesheets.view_hourlyrate"
    parameters = {
        "type": "object",
        "properties": {
            "active_only": {
                "type": "boolean",
                "description": "If true, return only active rates. Default false.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import HourlyRate
        qs = HourlyRate.objects.all()
        if args.get("active_only"):
            qs = qs.filter(is_active=True)
        return {
            "rates": [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "rate": str(r.rate),
                    "employee_id": str(r.employee_id) if r.employee_id else None,
                    "is_default": r.is_default,
                    "is_active": r.is_active,
                }
                for r in qs
            ],
            "total": qs.count(),
        }


@register_tool
class CreateHourlyRate(AssistantTool):
    name = "create_hourly_rate"
    description = "Create a new hourly rate for billing time entries."
    module_id = "timesheets"
    required_permission = "timesheets.change_hourlyrate"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Label for this rate (e.g. 'Standard', 'Senior Developer')."},
            "rate": {"type": "number", "description": "Hourly rate amount."},
            "employee_id": {
                "type": "string",
                "description": "UUID of the employee this rate applies to (optional; leave out for a general rate).",
            },
            "is_default": {
                "type": "boolean",
                "description": "Mark as the default rate. Default false.",
            },
            "is_active": {"type": "boolean", "description": "Active status. Default true."},
        },
        "required": ["name", "rate"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import HourlyRate
        r = HourlyRate.objects.create(
            name=args["name"],
            rate=args["rate"],
            employee_id=args.get("employee_id"),
            is_default=args.get("is_default", False),
            is_active=args.get("is_active", True),
        )
        return {"id": str(r.id), "name": r.name, "rate": str(r.rate), "created": True}


@register_tool
class UpdateHourlyRate(AssistantTool):
    name = "update_hourly_rate"
    description = "Update one or more fields of an existing hourly rate; omitted fields are unchanged."
    module_id = "timesheets"
    required_permission = "timesheets.change_hourlyrate"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "rate_id": {"type": "string", "description": "UUID of the hourly rate to update."},
            "name": {"type": "string"},
            "rate": {"type": "number"},
            "employee_id": {"type": "string"},
            "is_default": {"type": "boolean"},
            "is_active": {"type": "boolean"},
        },
        "required": ["rate_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import HourlyRate
        try:
            r = HourlyRate.objects.get(id=args["rate_id"])
        except HourlyRate.DoesNotExist:
            return {"error": "Hourly rate not found"}
        for field in ["name", "rate", "is_default", "is_active"]:
            if field in args:
                setattr(r, field, args[field])
        if "employee_id" in args:
            r.employee_id = args["employee_id"] or None
        r.save()
        return {"id": str(r.id), "name": r.name, "updated": True}


@register_tool
class DeleteHourlyRate(AssistantTool):
    name = "delete_hourly_rate"
    description = "Delete an hourly rate by ID."
    module_id = "timesheets"
    required_permission = "timesheets.delete_hourlyrate"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "rate_id": {"type": "string", "description": "UUID of the hourly rate to delete."},
        },
        "required": ["rate_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import HourlyRate
        try:
            r = HourlyRate.objects.get(id=args["rate_id"])
        except HourlyRate.DoesNotExist:
            return {"error": "Hourly rate not found"}
        name = r.name
        r.delete()
        return {"deleted": True, "name": name}


# ==============================================================================
# TIME ENTRIES
# ==============================================================================

@register_tool
class ListTimeEntries(AssistantTool):
    name = "list_time_entries"
    description = "List time entries, optionally filtered by employee, status, date range, or project."
    module_id = "timesheets"
    required_permission = "timesheets.view_timeentry"
    parameters = {
        "type": "object",
        "properties": {
            "employee_id": {
                "type": "string",
                "description": "Filter by employee UUID.",
            },
            "status": {
                "type": "string",
                "description": "Filter by status: 'draft', 'submitted', 'approved', 'rejected'.",
            },
            "date_from": {
                "type": "string",
                "description": "Start date filter (YYYY-MM-DD).",
            },
            "date_to": {
                "type": "string",
                "description": "End date filter (YYYY-MM-DD).",
            },
            "project_name": {
                "type": "string",
                "description": "Filter by project name (partial match).",
            },
            "billable_only": {
                "type": "boolean",
                "description": "If true, return only billable entries.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return. Default 30.",
            },
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimeEntry
        qs = TimeEntry.objects.all()
        if args.get("employee_id"):
            qs = qs.filter(employee_id=args["employee_id"])
        if args.get("status"):
            qs = qs.filter(status=args["status"])
        if args.get("date_from"):
            qs = qs.filter(date__gte=args["date_from"])
        if args.get("date_to"):
            qs = qs.filter(date__lte=args["date_to"])
        if args.get("project_name"):
            qs = qs.filter(project_name__icontains=args["project_name"])
        if args.get("billable_only"):
            qs = qs.filter(is_billable=True)
        limit = args.get("limit", 30)
        return {
            "entries": [
                {
                    "id": str(e.id),
                    "employee_id": str(e.employee_id),
                    "date": str(e.date),
                    "start_time": str(e.start_time) if e.start_time else None,
                    "end_time": str(e.end_time) if e.end_time else None,
                    "duration_minutes": e.duration_minutes,
                    "description": e.description,
                    "is_billable": e.is_billable,
                    "status": e.status,
                    "project_name": e.project_name,
                    "client_name": e.client_name,
                    "rate_amount": str(e.rate_amount) if e.rate_amount else None,
                }
                for e in qs[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class GetTimeEntry(AssistantTool):
    name = "get_time_entry"
    description = "Get full details of a specific time entry by ID."
    module_id = "timesheets"
    required_permission = "timesheets.view_timeentry"
    parameters = {
        "type": "object",
        "properties": {
            "entry_id": {"type": "string", "description": "UUID of the time entry."},
        },
        "required": ["entry_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimeEntry
        try:
            e = TimeEntry.objects.get(id=args["entry_id"])
        except TimeEntry.DoesNotExist:
            return {"error": "Time entry not found"}
        return {
            "id": str(e.id),
            "employee_id": str(e.employee_id),
            "date": str(e.date),
            "start_time": str(e.start_time) if e.start_time else None,
            "end_time": str(e.end_time) if e.end_time else None,
            "duration_minutes": e.duration_minutes,
            "description": e.description,
            "is_billable": e.is_billable,
            "hourly_rate_id": str(e.hourly_rate_id) if e.hourly_rate_id else None,
            "rate_amount": str(e.rate_amount) if e.rate_amount else None,
            "status": e.status,
            "project_name": e.project_name,
            "client_name": e.client_name,
            "total_amount": str(e.total_amount) if e.total_amount else None,
        }


@register_tool
class CreateTimeEntry(AssistantTool):
    name = "create_time_entry"
    description = "Log a new time entry for an employee."
    module_id = "timesheets"
    required_permission = "timesheets.change_timeentry"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "employee_id": {"type": "string", "description": "UUID of the employee."},
            "date": {"type": "string", "description": "Date of work in YYYY-MM-DD format."},
            "duration_minutes": {"type": "integer", "description": "Total duration in minutes."},
            "description": {"type": "string", "description": "Description of work performed."},
            "start_time": {"type": "string", "description": "Start time in HH:MM format (optional)."},
            "end_time": {"type": "string", "description": "End time in HH:MM format (optional)."},
            "is_billable": {"type": "boolean", "description": "Whether this time is billable. Default true."},
            "hourly_rate_id": {"type": "string", "description": "UUID of the hourly rate to apply (optional)."},
            "rate_amount": {"type": "number", "description": "Override rate amount per hour (optional)."},
            "project_name": {"type": "string", "description": "Project name (optional)."},
            "client_name": {"type": "string", "description": "Client name (optional)."},
            "status": {
                "type": "string",
                "description": "Initial status: 'draft' (default) or 'submitted'.",
            },
        },
        "required": ["employee_id", "date", "duration_minutes", "description"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimeEntry
        e = TimeEntry.objects.create(
            employee_id=args["employee_id"],
            date=args["date"],
            duration_minutes=args["duration_minutes"],
            description=args["description"],
            start_time=args.get("start_time"),
            end_time=args.get("end_time"),
            is_billable=args.get("is_billable", True),
            hourly_rate_id=args.get("hourly_rate_id"),
            rate_amount=args.get("rate_amount"),
            project_name=args.get("project_name", ""),
            client_name=args.get("client_name", ""),
            status=args.get("status", "draft"),
        )
        return {"id": str(e.id), "date": str(e.date), "duration_minutes": e.duration_minutes, "created": True}


@register_tool
class UpdateTimeEntry(AssistantTool):
    name = "update_time_entry"
    description = "Update one or more fields of an existing time entry; omitted fields are unchanged."
    module_id = "timesheets"
    required_permission = "timesheets.change_timeentry"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "entry_id": {"type": "string", "description": "UUID of the time entry to update."},
            "date": {"type": "string", "description": "Date in YYYY-MM-DD format."},
            "duration_minutes": {"type": "integer"},
            "description": {"type": "string"},
            "start_time": {"type": "string"},
            "end_time": {"type": "string"},
            "is_billable": {"type": "boolean"},
            "hourly_rate_id": {"type": "string"},
            "rate_amount": {"type": "number"},
            "project_name": {"type": "string"},
            "client_name": {"type": "string"},
            "status": {
                "type": "string",
                "description": "New status: 'draft', 'submitted', 'approved', 'rejected'.",
            },
        },
        "required": ["entry_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimeEntry
        try:
            e = TimeEntry.objects.get(id=args["entry_id"])
        except TimeEntry.DoesNotExist:
            return {"error": "Time entry not found"}
        for field in ["date", "duration_minutes", "description", "start_time", "end_time",
                      "is_billable", "rate_amount", "project_name", "client_name", "status"]:
            if field in args:
                setattr(e, field, args[field])
        if "hourly_rate_id" in args:
            e.hourly_rate_id = args["hourly_rate_id"] or None
        e.save()
        return {"id": str(e.id), "status": e.status, "updated": True}


@register_tool
class DeleteTimeEntry(AssistantTool):
    name = "delete_time_entry"
    description = "Delete a time entry by ID."
    module_id = "timesheets"
    required_permission = "timesheets.delete_timeentry"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "entry_id": {"type": "string", "description": "UUID of the time entry to delete."},
        },
        "required": ["entry_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimeEntry
        try:
            e = TimeEntry.objects.get(id=args["entry_id"])
        except TimeEntry.DoesNotExist:
            return {"error": "Time entry not found"}
        e.delete()
        return {"deleted": True}


# ==============================================================================
# TIMESHEET APPROVALS
# ==============================================================================

@register_tool
class ListTimesheetApprovals(AssistantTool):
    name = "list_timesheet_approvals"
    description = "List timesheet approval records, optionally filtered by employee or status."
    module_id = "timesheets"
    required_permission = "timesheets.view_timesheetapproval"
    parameters = {
        "type": "object",
        "properties": {
            "employee_id": {"type": "string", "description": "Filter by employee UUID."},
            "status": {
                "type": "string",
                "description": "Filter by status: 'pending', 'approved', 'rejected'.",
            },
            "limit": {"type": "integer", "description": "Maximum results to return. Default 20."},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimesheetApproval
        qs = TimesheetApproval.objects.all()
        if args.get("employee_id"):
            qs = qs.filter(employee_id=args["employee_id"])
        if args.get("status"):
            qs = qs.filter(status=args["status"])
        limit = args.get("limit", 20)
        return {
            "approvals": [
                {
                    "id": str(a.id),
                    "employee_id": str(a.employee_id),
                    "period_start": str(a.period_start),
                    "period_end": str(a.period_end),
                    "status": a.status,
                    "total_minutes": a.total_minutes,
                    "billable_minutes": a.billable_minutes,
                    "approved_by_id": str(a.approved_by_id) if a.approved_by_id else None,
                    "notes": a.notes,
                }
                for a in qs[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class GetTimesheetApproval(AssistantTool):
    name = "get_timesheet_approval"
    description = "Get full details of a specific timesheet approval record by ID."
    module_id = "timesheets"
    required_permission = "timesheets.view_timesheetapproval"
    parameters = {
        "type": "object",
        "properties": {
            "approval_id": {"type": "string", "description": "UUID of the approval record."},
        },
        "required": ["approval_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimesheetApproval
        try:
            a = TimesheetApproval.objects.get(id=args["approval_id"])
        except TimesheetApproval.DoesNotExist:
            return {"error": "Approval not found"}
        return {
            "id": str(a.id),
            "employee_id": str(a.employee_id),
            "period_start": str(a.period_start),
            "period_end": str(a.period_end),
            "status": a.status,
            "total_minutes": a.total_minutes,
            "billable_minutes": a.billable_minutes,
            "approved_by_id": str(a.approved_by_id) if a.approved_by_id else None,
            "notes": a.notes,
        }


@register_tool
class UpdateTimesheetApproval(AssistantTool):
    name = "update_timesheet_approval"
    description = "Approve or reject a timesheet approval record, optionally adding notes."
    module_id = "timesheets"
    required_permission = "timesheets.change_timesheetapproval"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "approval_id": {"type": "string", "description": "UUID of the approval to update."},
            "status": {
                "type": "string",
                "description": "New status: 'pending', 'approved', or 'rejected'.",
            },
            "approved_by_id": {
                "type": "string",
                "description": "UUID of the employee approving/rejecting.",
            },
            "notes": {"type": "string", "description": "Notes or rejection reason."},
            "total_minutes": {"type": "integer"},
            "billable_minutes": {"type": "integer"},
        },
        "required": ["approval_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimesheetApproval
        try:
            a = TimesheetApproval.objects.get(id=args["approval_id"])
        except TimesheetApproval.DoesNotExist:
            return {"error": "Approval not found"}
        for field in ["status", "notes", "total_minutes", "billable_minutes"]:
            if field in args:
                setattr(a, field, args[field])
        if "approved_by_id" in args:
            a.approved_by_id = args["approved_by_id"] or None
        a.save()
        return {"id": str(a.id), "status": a.status, "updated": True}


@register_tool
class DeleteTimesheetApproval(AssistantTool):
    name = "delete_timesheet_approval"
    description = "Delete a timesheet approval record by ID."
    module_id = "timesheets"
    required_permission = "timesheets.delete_timesheetapproval"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "approval_id": {"type": "string", "description": "UUID of the approval record to delete."},
        },
        "required": ["approval_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from timesheets.models import TimesheetApproval
        try:
            a = TimesheetApproval.objects.get(id=args["approval_id"])
        except TimesheetApproval.DoesNotExist:
            return {"error": "Approval not found"}
        a.delete()
        return {"deleted": True}
