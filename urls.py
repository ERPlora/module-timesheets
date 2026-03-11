from django.urls import path
from . import views

app_name = 'timesheets'

urlpatterns = [
    # My Time (index)
    path('', views.index, name='index'),

    # Time Entry CRUD
    path('entry/add/', views.time_entry_create, name='time_entry_create'),
    path('entry/<uuid:pk>/edit/', views.time_entry_edit, name='time_entry_edit'),
    path('entry/<uuid:pk>/delete/', views.time_entry_delete, name='time_entry_delete'),
    path('entry/<uuid:pk>/submit/', views.time_entry_submit, name='time_entry_submit'),

    # Approvals
    path('approvals/', views.approvals, name='approvals'),
    path('approvals/<uuid:pk>/action/', views.approval_action, name='approval_action'),

    # Reports
    path('reports/', views.reports, name='reports'),

    # Rates
    path('rates/', views.rates_list, name='rates'),
    path('rates/add/', views.rate_create, name='rate_create'),
    path('rates/<uuid:pk>/edit/', views.rate_edit, name='rate_edit'),
    path('rates/<uuid:pk>/delete/', views.rate_delete, name='rate_delete'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
