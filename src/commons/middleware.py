# src/commons/middleware.py
import time
import json
import traceback
from django.core.mail import mail_admins
from django.utils.deprecation import MiddlewareMixin
from django.db.models import F
import logging

logger = logging.getLogger("django.errors")


class ExceptionLoggingMiddleware(MiddlewareMixin):
    """
    - Catches every exception (process_exception)
    - Logs / emails only real error responses (process_response)
    - Stores start_time on the request for duration
    - Works with DRF, allauth, plain Django views
    """

    # noinspection PyMethodMayBeStatic
    def process_request(self, request):
        # Store start time for duration measurement
        request._error_middleware_start = time.time()

    # noinspection PyMethodMayBeStatic
    def process_exception(self, request, exception):
        """
        Called when a view raises an exception.
        Store the traceback for later use in process_response.
        """
        request._error_traceback = traceback.format_exc()
        request._error_exception = exception
        return None  # let Django continue

    # noinspection PyMethodMayBeStatic
    def process_response(self, request, response):
        start = getattr(request, "_error_middleware_start", None)
        duration = (time.time() - start) if start else 0.0

        # Skip logging for successful responses
        if 200 <= response.status_code < 300:
            return response

        # Build full report for client/server errors
        tb = getattr(request, "_error_traceback", traceback.format_exc())
        exc = getattr(request, "_error_exception", None)

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

        msg = (
            f"ERROR {response.status_code} – {path}\n"
            f"Method: {method}\n"
            f"User: {user}\n"
            f"Duration: {duration:.3f}s\n"
            f"Request data: {data}\n\n"
            f"Traceback:\n{tb}"
        )

        # Log the error
        logger.error(msg)

        # Send email to admins
        try:
            mail_admins(
                subject=f"[Django Error] {response.status_code} {path} ({method})",
                message=msg,
                fail_silently=False,
            )
        except Exception as mail_err:
            logger.exception("mail_admins failed: %s", mail_err)


        return response
