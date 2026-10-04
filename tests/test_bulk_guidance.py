import json
import unittest
from unittest.mock import patch

import resolution
import review_guidance
import server


class BulkGuidanceTests(unittest.TestCase):
    def test_residential_front_yard_search_routes_to_chapter_23(self):
        hits = resolution.search('R4 front yard', use_scope='residential')
        self.assertTrue(all('23-321' in h['citation'] for h in hits))
        self.assertFalse(any('24-34' in h['text'] for h in hits))
    def test_side_yard_section_includes_paragraph_c_and_conditions(self):
        hits = resolution.search('23-332 side yards')
        self.assertEqual([h['citation'].split('page ')[1] for h in hits], ['455', '456', '457'])
        self.assertIn('Other #residences#', hits[1]['text'])
        self.assertIn('not subject to', hits[1]['text'])
        self.assertIn('eight feet', hits[2]['text'])

    def test_rear_yard_section_includes_narrow_attached_lot_rule(self):
        hits = resolution.search('23-342(a)(2)(i)')
        self.assertIn('semi-detached', hits[0]['text'])
        self.assertIn('less than 40 feet', hits[1]['text'])
        self.assertIn('not less than 30 feet', hits[1]['text'])

    def test_residential_front_yard_table_and_modifications(self):
        hits = resolution.search('23-321 R4 front yard')
        self.assertEqual(len(hits), 3)
        self.assertIn('10 feet', hits[1]['text'])
        self.assertIn('R4 R4-1 R4A', hits[1]['text'])
        self.assertIn('adjacent #front yard#', hits[2]['text'])

    def test_height_table_carries_qualifying_site_applicability(self):
        hits = resolution.search('23-424')
        self.assertIn('qualifying residential sites', hits[0]['text'])
        self.assertIn('45', hits[1]['text'])
        self.assertIn('35 feet', resolution.search('23-422')[0]['text'])

    def test_extraction_preserves_datum_and_final_map_line(self):
        measurements = [
            {'kind': 'roof_elevation', 'label_as_drawn': '44\'-1"', 'datum': 'survey datum',
             'from_reference': 'datum', 'to_reference': 'roof', 'sheet_page': 'A-001', 'uncertainty': None},
            {'kind': 'front_yard', 'label_as_drawn': '10\'-1½"', 'datum': None,
             'from_reference': 'final map line', 'to_reference': 'front building wall', 'sheet_page': 'Z-001', 'uncertainty': 'governing line not verified'},
            {'kind': 'rear_yard', 'label_as_drawn': 'as labeled on plan', 'datum': None,
             'from_reference': 'rear building wall', 'to_reference': 'rear lot line', 'sheet_page': 'Z-001', 'uncertainty': None}]
        evidence = {'notes': 'Dimensions are labeled, reference applicability unverified',
                    'building_type': 'attached', 'dwelling_units': 2, 'lot_type': 'interior',
                    'lot_width_feet': 20, 'use_as_drawn': 'residential', 'measurements': measurements}
        response = {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': json.dumps(evidence)}]}]}
        with patch('server.call_provider', return_value=response) as provider:
            actual = json.loads(server.extract_drawing('plan.pdf', b'%PDF-1.4', 'test-only', 180))
        self.assertEqual(actual['measurements'], measurements)
        payload = provider.call_args.args[0]
        self.assertTrue(payload['text']['format']['strict'])
        self.assertIn('Never equate final map line', payload['instructions'])
        self.assertIn('Prioritize labeled rear-yard', payload['instructions'])

    def test_malformed_extraction_is_blocked(self):
        response = {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': '44 feet is building height'}]}]}
        with patch('server.call_provider', return_value=response):
            with self.assertRaisesRegex(RuntimeError, 'no compliance findings'):
                server.extract_drawing('plan.pdf', b'%PDF-1.4', 'test-only', 180)
