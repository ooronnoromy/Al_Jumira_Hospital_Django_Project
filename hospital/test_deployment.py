import tempfile
from pathlib import Path
from unittest.mock import patch

from django.db import OperationalError
from django.test import Client, TestCase, override_settings


class DeploymentTests(TestCase):
    def test_healthcheck_reports_database_connection(self):
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})

    def test_healthcheck_returns_unavailable_without_error_details(self):
        with patch('hospital.health.connection.cursor', side_effect=OperationalError('private database details')):
            response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})

    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r'^healthz/$'])
    def test_healthcheck_accepts_http_but_login_requires_https(self):
        self.assertEqual(self.client.get('/healthz/').status_code, 200)
        self.assertEqual(self.client.get('/login').status_code, 301)

    @override_settings(
        SECURE_PROXY_SSL_HEADER=('HTTP_X_FORWARDED_PROTO', 'https'),
        SECURE_SSL_REDIRECT=True,
        ALLOWED_HOSTS=['hospital.example.com'],
        CSRF_TRUSTED_ORIGINS=['https://hospital.example.com'],
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
    )
    def test_login_form_works_behind_https_proxy(self):
        client = Client(enforce_csrf_checks=True)
        headers = {'HTTP_HOST': 'hospital.example.com', 'HTTP_X_FORWARDED_PROTO': 'https'}
        response = client.get('/login', **headers)
        self.assertEqual(response.status_code, 200)
        token = response.cookies['csrftoken'].value
        self.assertTrue(response.cookies['csrftoken']['secure'])
        response = client.post('/login', {'username': 'invalid', 'password': 'invalid', 'csrfmiddlewaretoken': token}, HTTP_ORIGIN='https://hospital.example.com', **headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password.')

    def test_advertisements_are_served_from_persistent_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, 'banner.png').write_bytes(b'persisted-image')
            with override_settings(ADVERTISEMENT_ROOT=Path(directory)):
                response = self.client.get('/assets/advertisements/banner.png')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(b''.join(response.streaming_content), b'persisted-image')
                self.assertEqual(self.client.get('/assets/advertisements/missing.png').status_code, 404)
