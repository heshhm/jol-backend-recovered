import time
import json
import traceback
import logging
from django.core.mail import EmailMessage
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve, Resolver404
from django.conf import settings

logger = logging.getLogger("django.errors")


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._error_middleware_start = time.time()

    def process_exception(self, request, exception):
        # Store traceback for later
        request._error_traceback = traceback.format_exc()
        request._error_exception = exception
        return None

    def process_response(self, request, response):
        start = getattr(request, "_error_middleware_start", None)
        duration = (time.time() - start) if start else 0.0

        if 200 <= response.status_code < 300:
            return response

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

        tb = getattr(request, "_error_traceback", None)

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
            f"Duration: {duration:.3f}s\n"
            f"Request data: {data}\n"
            f"View: {view_name} (Line {line_no})\n"
            f"Traceback:\n{tb or 'No traceback available'}"
        )

        # Log the error
        logger.error(report)

        # Send email with full report in body
        try:
            email = EmailMessage(
                subject=f"[Django Error] [COMMONS / MIDDLEWARE ] {response.status_code} {path}",
                body=report,
                to=[admin[1] for admin in settings.ADMINS]
            )
            email.send(fail_silently=False)
        except Exception as mail_err:
            logger.exception("Sending error email failed: %s", mail_err)

        return response
