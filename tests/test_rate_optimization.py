import base64
import io
import json
import unittest
import urllib.error
from unittest.mock import patch

import resolution
import server


def provider_error(code='rate_limit_exceeded', message='Rate limit reached', delay='20'):
    return urllib.error.HTTPError('https://api.openai.com/v1/responses', 429, 'error',
        {'Retry-After': delay}, io.BytesIO(json.dumps({'error': {'code': code, 'message': message}}).encode()))


class RetryTests(unittest.TestCase):
    def test_retry_honors_delay_then_succeeds(self):
        with patch('server.urllib.request.urlopen', side_effect=[provider_error(), io.BytesIO(b'{"status":"completed"}')]) as request, \
                patch('server.time.sleep') as sleep:
            self.assertEqual(server.call_provider({}, 'test-only')['status'], 'completed')
        sleep.assert_called_once_with(20)
        self.assertEqual(request.call_count, 2)

    def test_no_retry_for_quota_or_oversize(self):
        for error in [provider_error(code='insufficient_quota'), provider_error(message='Request too large')]:
            with patch('server.urllib.request.urlopen', side_effect=error) as request, \
                    patch('server.time.sleep') as sleep:
                with self.assertRaises(RuntimeError):
                    server.call_provider({}, 'test-only')
            sleep.assert_not_called()
            self.assertEqual(request.call_count, 1)

    def test_retries_are_bounded(self):
        with patch('server.urllib.request.urlopen', side_effect=[provider_error() for _ in range(3)]) as request, \
                patch('server.time.sleep') as sleep:
            with self.assertRaisesRegex(RuntimeError, 'rate limit reached'):
                server.call_provider({}, 'test-only')
        self.assertEqual(request.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_no_retry_if_deadline_cannot_honor_provider_delay(self):
        with patch('server.urllib.request.urlopen', side_effect=provider_error()), \
                patch('server.time.sleep') as sleep:
            with self.assertRaises(RuntimeError):
                server.call_provider({}, 'test-only', timeout=10)
        sleep.assert_not_called()

    def test_drawing_only_sent_during_extraction(self):
        result = {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': 'Sheet A1: lot 2000 sf.'}]}]}
        with patch('server.call_provider', return_value=result) as provider:
            self.assertEqual(server.extract_drawing('plans.pdf', b'%PDF-1.4', 'test-only', 180), 'Sheet A1: lot 2000 sf.')
        payload = provider.call_args.args[0]
        self.assertEqual(payload['input'][0]['content'][0]['type'], 'input_file')
        self.assertEqual(payload['max_output_tokens'], 2000)
        self.assertNotIn('tools', payload)


class RetrievalTests(unittest.TestCase):
    def test_queries_use_district_and_subject(self):
        floor = resolution.search('R4 floor area ratio')
        height = resolution.search('R4 height setback')
        self.assertNotEqual([h['text'] for h in floor[1:]], [h['text'] for h in height[1:]])
        self.assertLessEqual(len(height), 5)

    def test_duplicate_excerpts_not_resent(self):
        lookup = lambda call_id: {'status': 'completed', 'output': [{'type': 'function_call',
            'name': 'search_resolution', 'call_id': call_id, 'arguments': '{"query":"R4"}'}]}
        final = {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': 'Preliminary report.'}]}]}
        data = {'address': '699 Eldert Lane', 'filename': 'plans.pdf',
                'pdf': base64.b64encode(b'%PDF-1.4').decode()}
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.extract_drawing', return_value='R4, dimensions unverified'), \
                patch('server.call_provider', side_effect=[lookup('first'), lookup('second'), final]) as provider:
            server.review(data)
        outputs = [json.loads(item['output']) for item in provider.call_args.args[0]['input']
                   if item.get('type') == 'function_call_output']
        self.assertTrue(outputs[0]['excerpts'])
        self.assertEqual(outputs[1]['excerpts'], [])
        self.assertLessEqual(sum(len(h['text']) for output in outputs for h in output['excerpts']), 18000)
