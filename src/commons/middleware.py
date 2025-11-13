import traceback
import logging
import time

from django.core.mail import mail_admins
from django.conf import settings

logger = logging.getLogger("django.errors")

class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time

            tb = traceback.format_exc()
            path = request.path
            method = request.method
            user = getattr(request, "user", "Anonymous")
            data = getattr(request, "POST", {})
            msg = (
                f"Exception in path: {path}\n"
                f"Method: {method}\n"
                f"User: {user}\n"
                f"Duration: {duration:.3f}s\n"
                f"POST data: {data}\n\n"
                f"Traceback:\n{tb}"
            )

            # log locally
            logger.error(msg)

            # send email to admins
            mail_admins(
                subject=f"[Django Error] {path} ({method})",
                message=msg,
                fail_silently=False
            )

            raise
