import base64
import http.client
import json
import threading
import unittest
from unittest.mock import patch

import server


class AccessTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(server.os.environ,
            {'APP_USERNAME': 'owner', 'APP_PASSWORD': 'test-only-password-123'}, clear=True)
        self.environment.start()
        self.app = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        self.thread = threading.Thread(target=self.app.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.app.shutdown()
        self.app.server_close()
        self.thread.join()
        self.environment.stop()

    def request(self, path='/', auth=None, data=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.app.server_port)
        headers = {}
        if auth is not None:
            headers['Authorization'] = auth
        connection.request('POST' if data is not None else 'GET', path,
                           body=json.dumps(data) if data is not None else None, headers=headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def auth(self, password='test-only-password-123'):
        return 'Basic ' + base64.b64encode(('owner:' + password).encode()).decode()

    def test_all_app_routes_require_login(self):
        for path in ['/', '/app.js', '/style.css', '/api/status', '/api/review']:
            status, headers, _ = self.request(path, data={} if path == '/api/review' else None)
            self.assertEqual(status, 401, path)
            self.assertIn('WWW-Authenticate', headers)

    def test_bad_and_malformed_credentials_rejected(self):
        for auth in [self.auth('wrong'), 'Basic !!!!', 'Bearer token']:
            self.assertEqual(self.request(auth=auth)[0], 401)

    def test_valid_login_allows_checklist(self):
        self.assertEqual(self.request(auth=self.auth())[0], 200)
        data = {'address': '123 Example Street', 'filename': 'plans.pdf',
                'pdf': base64.b64encode(b'%PDF-1.4\nfixture').decode()}
        status, _, body = self.request('/api/review', self.auth(), data)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['mode'], 'checklist')

    def test_missing_or_short_password_locks_app_even_with_api_key(self):
        for password in ['', 'short']:
            with patch.dict(server.os.environ, {'APP_PASSWORD': password, 'OPENAI_API_KEY': 'test-only'}):
                self.assertEqual(self.request(auth=self.auth())[0], 503)
                self.assertEqual(self.request('/api/review', self.auth(), {})[0], 503)
                self.assertEqual(self.request('/healthz')[0], 200)

    def test_unauthorized_request_never_calls_provider(self):
        with patch('server.review') as review:
            self.request('/api/review', data={})
            review.assert_not_called()

    def test_provider_failure_releases_slot(self):
        data = {'address': '123 Example Street', 'filename': 'plans.pdf',
                'pdf': base64.b64encode(b'%PDF-1.4\nfixture').decode()}
        limit = server.ReviewLimit()
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.REVIEW_LIMIT', limit), \
                patch('server.review', side_effect=RuntimeError('Provider unavailable')):
            self.assertEqual(self.request('/api/review', self.auth(), data)[0], 502)
            self.assertFalse(limit.active)
            self.assertEqual(len(limit.attempts), 1)


class LimitTests(unittest.TestCase):
    def test_serial_execution_and_hourly_cap(self):
        limit = server.ReviewLimit()
        with patch('server.time.monotonic', return_value=1000):
            self.assertTrue(limit.acquire())
            self.assertFalse(limit.acquire())
            limit.release()
            for _ in range(9):
                self.assertTrue(limit.acquire())
                limit.release()
            self.assertFalse(limit.acquire())
        with patch('server.time.monotonic', return_value=4600):
            self.assertTrue(limit.acquire())


if __name__ == '__main__':
    unittest.main()
