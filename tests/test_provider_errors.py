import base64
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import server


def error(status=429, code=None, message='', headers=None, body=None):
    content = body if body is not None else json.dumps(
        {'error': {'code': code, 'message': message}}).encode()
    return urllib.error.HTTPError('https://api.openai.com/v1/responses', status,
                                  'provider error', headers or {}, io.BytesIO(content))


class ProviderErrorTests(unittest.TestCase):
    def test_quota_distinct_from_rate_limit(self):
        result = server.provider_error_message(error(code='insufficient_quota'))
        self.assertIn('quota unavailable', result)
        self.assertIn('organization/project', result)

    def test_oversized_token_request(self):
        result = server.provider_error_message(error(code='rate_limit_exceeded',
            message='Request too large for this model on tokens per min'))
        self.assertIn('fewer sheets', result)
        self.assertIn('Waiting alone may not resolve', result)

    def test_retry_after_for_transient_rate_limit(self):
        result = server.provider_error_message(error(code='rate_limit_exceeded',
                                                     headers={'Retry-After': '30'}))
        self.assertIn('Wait at least 30 seconds', result)

    def test_unrecognized_error_does_not_guess(self):
        result = server.provider_error_message(error(body=b'<html>Proxy error</html>'))
        self.assertIn('without a recognized', result)

    def test_secrets_and_user_content_never_returned(self):
        for status in (400, 401, 403, 404, 413, 429, 500):
            result = server.provider_error_message(error(status=status,
                code='secret-marker', message='secret-marker key and private drawing data',
                headers={'Retry-After': 'secret-marker'}))
            self.assertNotIn('secret-marker', result)
            self.assertNotIn('private drawing', result)

    def test_review_surfaces_classified_provider_failure(self):
        data = {'address': '123 Example Street', 'filename': 'plans.pdf',
                'pdf': base64.b64encode(b'%PDF-1.4\nfixture').decode()}
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.urllib.request.urlopen', side_effect=error(code='insufficient_quota')):
            with self.assertRaisesRegex(RuntimeError, 'quota unavailable'):
                server.review(data)


if __name__ == '__main__':
    unittest.main()
