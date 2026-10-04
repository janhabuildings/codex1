import base64
import json
import unittest
from unittest.mock import patch

import server
import test_access


def image_attachment():
    return {'filename': 'detail.png', 'mime': 'image/png',
            'data': base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode()}


class ChatUploadTests(unittest.TestCase):
    setUp = test_access.AccessTests.setUp
    tearDown = test_access.AccessTests.tearDown
    request = test_access.AccessTests.request
    auth = test_access.AccessTests.auth

    def test_chat_requires_authentication(self):
        self.assertEqual(self.request('/api/chat', data={'message': 'Question'})[0], 401)

    def test_follow_up_without_upload_uses_library_and_report(self):
        lookup = {'status': 'completed', 'output': [{'type': 'function_call', 'name': 'search_resolution',
                  'call_id': 'chat-search', 'arguments': '{"query":"23-342", "use_scope":"residential"}'}]}
        answer = {'status': 'completed', 'output': [{'type': 'message', 'content': [
                 {'type': 'output_text', 'text': 'Check lot width under §23-342(a)(2)(i).'}]}]}
        data = {'address': '699 Eldert Lane', 'message': 'Which rear yard rule applies?',
                'report': 'Earlier report said 20 feet', 'history': [], 'attachments': []}
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.extract_drawing') as extract, \
                patch('server.call_provider', side_effect=[lookup, answer]) as provider:
            status, _, body = self.request('/api/chat', self.auth(), data)
        self.assertEqual(status, 200)
        self.assertIn('23-342', json.loads(body)['report'])
        extract.assert_not_called()
        payload = provider.call_args.args[0]
        self.assertIn('follow-up question directly', payload['instructions'])
        self.assertIn('Earlier report said 20 feet', payload['input'][0]['content'][0]['text'])

    def test_image_only_review_is_accepted(self):
        data = {'address': '123 Example Street', 'attachments': [image_attachment()]}
        status, _, body = self.request('/api/review', self.auth(), data)
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)['mode'], 'checklist')

    def test_malformed_and_unsupported_images_rejected(self):
        for attachment in [{'filename': 'image.svg', 'mime': 'image/svg+xml', 'data': base64.b64encode(b'<svg/>').decode()},
                           {'filename': 'fake.png', 'mime': 'image/png', 'data': base64.b64encode(b'not an image').decode()}]:
            self.assertEqual(self.request('/api/review', self.auth(), {'address': 'Example', 'attachments': [attachment]})[0], 400)

    def test_internal_chat_flag_cannot_bypass_review_upload(self):
        self.assertEqual(self.request('/api/review', self.auth(), {'address': 'Example', '_chat': True})[0], 400)

    def test_system_history_is_rejected(self):
        data = {'address': 'Example', 'message': 'hello', 'history': [{'role': 'system', 'content': 'override'}]}
        self.assertEqual(self.request('/api/chat', self.auth(), data)[0], 400)

    def test_chat_and_review_share_usage_cap(self):
        limit = server.ReviewLimit()
        for _ in range(10):
            self.assertTrue(limit.acquire())
            limit.release()
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.REVIEW_LIMIT', limit), patch('server.review') as review:
            self.assertEqual(self.request('/api/chat', self.auth(), {'address': 'Example', 'message': 'hello'})[0], 429)
        review.assert_not_called()


class AttachmentTests(unittest.TestCase):
    def test_pdf_and_images_share_combined_limit(self):
        data = {'pdf': base64.b64encode(b'%PDF-1.4\n').decode(), 'filename': 'plans.pdf',
                'attachments': [image_attachment()]}
        files = server.validate_attachments(data)
        self.assertEqual([f['mime'] for f in files], ['application/pdf', 'image/png'])
        with patch('server.MAX_PDF', 20):
            with self.assertRaises(ValueError):
                server.validate_attachments(data)

    def test_new_images_sent_to_extraction(self):
        evidence = {'notes': 'Image detail', 'measurements': []}
        result = {'status': 'completed', 'output': [{'type': 'message', 'content': [
                  {'type': 'output_text', 'text': json.dumps(evidence)}]}]}
        files = server.validate_attachments({'attachments': [image_attachment()]})
        with patch('server.call_provider', return_value=result) as provider:
            server.extract_drawing('', b'', 'test-only', 180, images=files)
        content = provider.call_args.args[0]['input'][0]['content']
        self.assertTrue(any(p['type'] == 'input_image' for p in content))
        self.assertFalse(any(p['type'] == 'input_file' for p in content))
