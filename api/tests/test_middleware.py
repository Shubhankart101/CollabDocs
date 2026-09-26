from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from collabdocs.middleware import RequestLoggingMiddleware


class RequestLoggingMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.get_response = lambda req: HttpResponse("OK", status=200)
        self.middleware = RequestLoggingMiddleware(self.get_response)

    def test_middleware_logging(self):
        request = self.factory.get('/api/users/')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
