import base64
import unittest
from unittest.mock import patch
import server


class ReviewTests(unittest.TestCase):
    def submission(self):
        return {'address': '123 Example Street, Brooklyn', 'filename': 'plans.pdf',
                'pdf': base64.b64encode(b'%PDF-1.4\nexample').decode()}

    def test_no_key_does_not_claim_analysis(self):
        with patch.dict(server.os.environ, {}, clear=True):
            result = server.review(self.submission())
        self.assertEqual(result['mode'], 'checklist')
        self.assertIn('Drawing analysis has not run', result['report'])

    def test_reject_non_pdf(self):
        data = self.submission()
        data['pdf'] = base64.b64encode(b'<script>bad</script>').decode()
        with self.assertRaises(ValueError):
            server.validate_submission(data)

    def test_reject_missing_address(self):
        data = self.submission()
        data['address'] = ' '
        with self.assertRaises(ValueError):
            server.validate_submission(data)

    def test_reject_invalid_base64(self):
        data = self.submission()
        data['pdf'] = '!!!!'
        with self.assertRaises(ValueError):
            server.validate_submission(data)


if __name__ == '__main__':
    unittest.main()
