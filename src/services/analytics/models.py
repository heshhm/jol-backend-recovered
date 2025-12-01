from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class RequestLog(models.Model):
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    view_name = models.CharField(max_length=200, blank=True)
    status_code = models.PositiveSmallIntegerField()
    duration_ms = models.FloatField()
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    body = models.JSONField(null=True, blank=True)
    request_id = models.CharField(max_length=50, unique=True)
    exception_message = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.method} {self.path} [{self.status_code}] {self.duration_ms}ms"


class ErrorReportingConfig(models.Model):
    """Configuration for error email reporting system"""
    enabled = models.BooleanField(default=False, help_text="Enable/disable email notifications for 5xx errors")
    use_django_admins = models.BooleanField(default=True, help_text="Include emails from settings.ADMINS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Error Reporting Configuration"
        verbose_name_plural = "Error Reporting Configuration"

    def __str__(self):
        return f"Error Reporting ({'Enabled' if self.enabled else 'Disabled'})"

    @classmethod
    def get_config(cls):
        """Get or create singleton config"""
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class ErrorReportEmail(models.Model):
    """Custom email addresses for error notifications"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True, help_text="Optional name for this contact")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['email']
        verbose_name = "Error Report Email"
        verbose_name_plural = "Error Report Emails"

    def __str__(self):
        return f"{self.name} <{self.email}>" if self.name else self.email


class ErrorEmailLog(models.Model):
    """Log of all error notification emails sent"""
    request_log = models.ForeignKey(RequestLog, on_delete=models.CASCADE, related_name='error_emails')
    sent_to = models.JSONField(help_text="List of email addresses this notification was sent to")
    subject = models.CharField(max_length=500)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True, help_text="Error message if sending failed")

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Error Email Log"
        verbose_name_plural = "Error Email Logs"

    def __str__(self):
        return f"Email for {self.request_log.path} ({self.sent_at.strftime('%Y-%m-%d %H:%M')})"