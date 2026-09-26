import time
import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware that records and logs request timing and details:
    HTTP method, Endpoint path, Response status code, Time taken in milliseconds.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()

        response = self.get_response(request)

        end_time = time.perf_counter()
        duration_ms = (end_time - start_time) * 1000.0

        log_message = (
            f"[{request.method}] {request.path} - Status: {response.status_code} - "
            f"Time taken: {duration_ms:.2f}ms"
        )
        print(log_message)
        logger.info(log_message)

        return response
