from django.utils.translation import gettext_lazy as _

MODULE_ID = "timesheets"
MODULE_NAME = _("Timesheets")
MODULE_ICON = "time-outline"
MODULE_VERSION = "1.0.0"
MODULE_CATEGORY = "operations"

MODULE_INDUSTRIES = ["consulting", "law_firm", "tax_advisory", "design_studio", "marketing", "admin_agency", "freelancer"]

MENU = {
    "label": _("Timesheets"),
    "icon": "time-outline",
    "order": 55,
    "show": True,
}

NAVIGATION = [
    {"id": "my_time", "label": _("My Time"), "icon": "time-outline", "view": ""},
    {"id": "approvals", "label": _("Approvals"), "icon": "checkmark-circle-outline", "view": "approvals"},
    {"id": "reports", "label": _("Reports"), "icon": "bar-chart-outline", "view": "reports"},
    {"id": "rates", "label": _("Rates"), "icon": "cash-outline", "view": "rates"},
    {"id": "settings", "label": _("Settings"), "icon": "settings-outline", "view": "settings"},
]

DEPENDENCIES = ['projects', 'invoicing', 'staff']

SETTINGS = {
    "default_billable": True,
    "require_approval": True,
    "approval_period": "weekly",
}

PERMISSIONS = [
    ("view_time_entry", _("Can view time entries")),
    ("add_time_entry", _("Can add time entries")),
    ("change_time_entry", _("Can change time entries")),
    ("delete_time_entry", _("Can delete time entries")),
    ("approve_timesheet", _("Can approve timesheets")),
    ("manage_rates", _("Can manage hourly rates")),
    ("view_reports", _("Can view reports")),
    ("view_settings", _("Can view settings")),
    ("change_settings", _("Can change settings")),
]

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "view_time_entry", "add_time_entry", "change_time_entry",
        "approve_timesheet", "manage_rates", "view_reports", "view_settings",
    ],
    "employee": ["view_time_entry", "add_time_entry", "change_time_entry"],
}
