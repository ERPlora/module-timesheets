"""
AI context for the Timesheets module.
Loaded into the assistant system prompt when this module's tools are active.
"""

CONTEXT = """
## Module Knowledge: Timesheets

### Models

**TimesheetsSettings** — singleton per hub.
- `default_billable` (bool, default True): new time entries default to billable
- `require_approval` (bool, default True): entries must be approved before billing
- `approval_period` (choice): weekly, biweekly, monthly (default: weekly)

**HourlyRate** — named billing rates.
- `name` (str): rate label (e.g. "Standard", "Overtime", "Training")
- `rate` (Decimal): amount per hour
- `employee` (FK → accounts.LocalUser, nullable): if set, rate is specific to this employee; null = global rate
- `is_default` (bool, default False): used when no rate is specified
- `is_active` (bool, default True)

**TimeEntry** — a single time log record.
- `employee` (FK → accounts.LocalUser): who logged the time
- `date` (date): work date
- `start_time` / `end_time` (time, nullable): clock-in/clock-out
- `duration_minutes` (int): total duration (may be entered manually or computed from start/end)
- `description` (text): what was worked on
- `is_billable` (bool, default True)
- `hourly_rate` (FK → HourlyRate, nullable)
- `rate_amount` (Decimal, nullable): snapshot of rate at time of entry
- `status` (choice): draft, submitted, approved, rejected
- `project_name` (str): project or task reference
- `client_name` (str): client reference
- Computed: `duration_hours` = duration_minutes / 60; `total_amount` = rate_amount * hours

**TimesheetApproval** — approval batch for an employee's time period.
- `employee` (FK → accounts.LocalUser)
- `period_start` / `period_end` (date): the period covered
- `status` (choice): pending, approved, rejected
- `approved_by` (FK → accounts.LocalUser, nullable): manager who approved/rejected
- `total_minutes` / `billable_minutes` (int): aggregated from TimeEntry records in period
- `notes` (text)

### Key flows

1. **Log time**: create TimeEntry with employee, date, duration_minutes, description. Status starts as "draft".
2. **Submit for approval**: update TimeEntry status="submitted" or create a TimesheetApproval for the period.
3. **Approve period**: manager updates TimesheetApproval status="approved", approved_by=self.
4. **Reject period**: update TimesheetApproval status="rejected" with notes.
5. **Calculate billable amount**: sum TimeEntry.total_amount for entries where is_billable=True and status="approved".

### Relationships
- TimeEntry.employee → accounts.LocalUser
- TimeEntry.hourly_rate → HourlyRate
- TimesheetApproval.employee, approved_by → accounts.LocalUser
"""
