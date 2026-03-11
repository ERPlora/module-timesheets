from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TimesheetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timesheets'
    label = 'timesheets'
    verbose_name = _('Timesheets')

    def ready(self):
        pass
