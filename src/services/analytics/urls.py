from django.urls import path
from . import views

app_name = "django_analytics"

urlpatterns = [
    path("dj-analytics/", views.dashboard, name="dashboard"),
    path("dj-analytics/content/", views.tab_content, name="tab_content"),
    path("dj-analytics/reporting/toggle/", views.toggle_reporting, name="toggle_reporting"),
    path("dj-analytics/reporting/toggle-admins/", views.toggle_django_admins, name="toggle_django_admins"),
    path("dj-analytics/reporting/add-email/", views.add_email, name="add_email"),
    path("dj-analytics/reporting/delete-email/<int:email_id>/", views.delete_email, name="delete_email"),
    path("dj-analytics/reporting/email-logs/", views.email_logs_list, name="email_logs_list"),
    path("dj-analytics/user/<int:user_id>/", views.user_detail, name="user_detail"),
]