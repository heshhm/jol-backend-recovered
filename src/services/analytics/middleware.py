import time
import uuid
import json
import traceback
import logging
from django.utils.deprecation import MiddlewareMixin
from django.core.mail import EmailMessage
from django.urls import resolve, Resolver404
from django.conf import settings
from .models import RequestLog

logger = logging.getLogger("django.errors")


class AnalyticsMiddleware(MiddlewareMixin):
    """
    Combined Analytics + Error Reporting Middleware
    - Logs all requests to RequestLog
    - Sends email notifications on 5xx errors when enabled
    """
    def process_request(self, request):
        request_id = str(uuid.uuid4())[:12]
        request._analytics = {
            "start_time": time.time(),
            "request_id": request_id,
        }
        # Store request_id for error reporting to use
        request._analytics_request_id = request_id

        # Determine client IP (respect X-Forwarded-For if present) and print it
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            ip = xff.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        print(ip)
        logger.info("Request %s IP: %s", request_id, ip)

    def process_exception(self, request, exception):
        analytics = getattr(request, "_analytics", {})
        analytics["exception"] = exception
        analytics["traceback"] = traceback.format_exc()
        return None

    def process_response(self, request, response):
        analytics = getattr(request, "_analytics", None)
        if not analytics:
            return response

        duration_ms = (time.time() - analytics["start_time"]) * 1000

        # Parse body
        try:
            if request.content_type and "json" in request.content_type.lower():
                body = json.loads(request.body) if request.body else None
            else:
                body = dict(request.POST) or None
        except Exception:
            body = None

        view_name = "unknown"
        if hasattr(request, "resolver_match") and request.resolver_match:
            view_name = request.resolver_match.view_name or "unknown"

        # Create RequestLog entry
        request_log = RequestLog.objects.create(
            path=request.path,
            method=request.method,
            view_name=view_name,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            user=request.user if request.user.is_authenticated else None,
            ip=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            body=body,
            request_id=analytics["request_id"],
            exception_message=str(analytics.get("exception", "")) if analytics.get("exception") else None,
            traceback=analytics.get("traceback"),
        )

        # === ERROR REPORTING: Send emails on 5xx errors ===
        if response.status_code >= 500:
            self._send_error_notification(request, response, request_log, analytics, duration_ms)

        return response

    def _send_error_notification(self, request, response, request_log, analytics, duration_ms):
        """Send email notification for 5xx errors"""
        try:
            from .models import ErrorReportingConfig, ErrorReportEmail, ErrorEmailLog
            
            # Check if error reporting is enabled
            config = ErrorReportingConfig.get_config()
            if not config.enabled:
                return

            # Build error report
            path = request.path
            method = request.method
            user = getattr(request.user, "pk", "Anonymous") if hasattr(request, "user") else "Anonymous"

            try:
                if request.content_type and "json" in request.content_type:
                    data = json.loads(request.body) if request.body else {}
                else:
                    data = request.POST.dict()
            except Exception:
                data = "<unparseable>"

            tb = analytics.get("traceback", None)

            # Attempt to resolve the view name and line number
            try:
                view_func = resolve(path).func
                view_name = f"{view_func.__module__}.{view_func.__name__}"
                code_line = getattr(view_func, "__code__", None)
                line_no = code_line.co_firstlineno if code_line else "Unknown"
            except Resolver404:
                view_name = "Could not resolve view"
                line_no = "Unknown"

            report = (
                f"ERROR {response.status_code} – {path}\n"
                f"Method: {method}\n"
                f"User - PK: {user}\n"
                f"Duration: {duration_ms/1000:.3f}s\n"
                f"Request data: {data}\n"
                f"View: {view_name} (Line {line_no})\n"
                f"Traceback:\n{tb or 'No traceback available'}"
            )

            # Log the error
            logger.error(report)

            # Collect recipient emails
            recipients = []
            
            if config.use_django_admins:
                admin_emails = [admin[1] for admin in getattr(settings, 'ADMINS', [])]
                recipients.extend(admin_emails)
            
            # Add custom emails
            custom_emails = ErrorReportEmail.objects.filter(active=True).values_list('email', flat=True)
            recipients.extend(custom_emails)
            
            # Remove duplicates
            recipients = list(set(recipients))

            if not recipients:
                logger.warning("Error reporting enabled but no recipients configured")
                return

            # Send email
            subject = f"[Django Error] {response.status_code} {path}"
            success = True
            error_message = None
            
            try:
                email = EmailMessage(
                    subject=subject,
                    body=report,
                    to=recipients
                )
                email.send(fail_silently=False)
            except Exception as mail_err:
                logger.exception("Sending error email failed: %s", mail_err)
                success = False
                error_message = str(mail_err)

            # Log to database
            try:
                ErrorEmailLog.objects.create(
                    request_log=request_log,
                    sent_to=recipients,
                    subject=subject,
                    body=report,
                    success=success,
                    error_message=error_message
                )
            except Exception as log_err:
                logger.exception("Failed to log error email to database: %s", log_err)

        except Exception as e:
            # Don't let error reporting break the request
            logger.exception("Error in error reporting system: %s", e)