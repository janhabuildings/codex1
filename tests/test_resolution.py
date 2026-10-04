import base64
import unittest
from unittest.mock import patch

import resolution
import server


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        extraction = patch('server.extract_drawing', return_value='Sheet A-001: R4; lot 2,000 sf; proposed ZFA 2,000 sf. Dimensions not verified.')
        extraction.start()
        self.addCleanup(extraction.stop)

    def test_r4_far_table_keeps_rows_and_eligibility_distinct(self):
        tables = resolution.far_tables()
        rows = tables['basic_table']['rows']
        r4 = next(row for row in rows if 'R4' in row['districts'])
        r3 = next(row for row in rows if 'R3-2' in row['districts'])
        self.assertEqual(r4['standard_lot_far'], 1.0)
        self.assertEqual(r4['qualifying_residential_site_far'], 1.5)
        self.assertEqual(2000 * r4['standard_lot_far'], 2000)
        self.assertEqual(r3['standard_lot_far'], 0.75)
        self.assertEqual(tables['basic_table']['section'], '23-21')
        self.assertEqual(tables['predominantly_built_up']['eligibility_section'], '23-711')
        hits = resolution.search('R4 floor area ratio')
        self.assertIn('23-21', hits[0]['citation'])
        self.assertIn('436–437', hits[0]['citation'])
        self.assertIn('"standard_lot_far": 1.0', hits[0]['text'])
    def test_supplied_library_metadata(self):
        metadata = resolution.metadata()
        self.assertEqual(metadata['pages'], 5306)
        self.assertEqual(metadata['generated_date'], '2026-09-21')
        self.assertEqual(metadata['low_text_pages'], 408)

    def test_known_section_found_with_page_citation(self):
        hits = resolution.search('11-01 Long Title')
        self.assertTrue(any('11-01' in hit['text'] and 'Long Title' in hit['text'] for hit in hits))
        self.assertTrue(all('PDF page' in hit['citation'] for hit in hits))
        self.assertEqual(resolution.search(''), [])
        self.assertIsInstance(resolution.search('" OR *; DROP TABLE excerpts;'), list)

    def test_model_retrieves_sources_without_web_tool(self):
        data = {'address': '123 Example Street', 'filename': 'plans.pdf',
                'pdf': base64.b64encode(b'%PDF-1.4\nfixture').decode()}
        first = {'status': 'completed', 'output': [{'type': 'function_call',
                 'name': 'search_resolution', 'call_id': 'test-call',
                 'arguments': '{"query":"11-01 Long Title"}'}]}
        second = {'status': 'completed', 'output': [{'type': 'message',
                  'content': [{'type': 'output_text', 'text': 'Insufficient information for a compliance conclusion.'}]}]}
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.call_provider', side_effect=[first, second]) as provider:
            report = server.review(data)
        payload = provider.call_args.args[0]
        self.assertEqual(payload['tools'][0]['name'], 'search_resolution')
        self.assertIn('standard R4 FAR is 1.00, not 0.75', payload['instructions'])
        self.assertIn('section number AND Split/PDF page', payload['instructions'])
        self.assertFalse(any('web_search' in tool['type'] for tool in payload['tools']))
        outputs = [item for item in payload['input'] if item.get('type') == 'function_call_output']
        self.assertFalse(any(part.get('type') == 'input_file' for item in payload['input']
                             for part in item.get('content', []) if isinstance(part, dict)))
        self.assertIn('PDF page', outputs[0]['output'])
        self.assertIn('Pages retrieved', report['report'])

    def test_no_source_retrieval_rejects_ungrounded_report(self):
        data = {'address': '123 Example Street', 'filename': 'plans.pdf',
                'pdf': base64.b64encode(b'%PDF-1.4\nfixture').decode()}
        result = {'status': 'completed', 'output': [{'type': 'message',
                  'content': [{'type': 'output_text', 'text': 'Everything passes.'}]}]}
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.call_provider', return_value=result):
            with self.assertRaisesRegex(RuntimeError, 'review-processing failure'):
                server.review(data)

    def test_search_is_forced_and_recovers_from_skipped_lookup(self):
        data = {'address': '699 Eldert Lane', 'details': 'Brooklyn, Block 4274 Lot 10, R4',
                'filename': 'plans.pdf', 'pdf': base64.b64encode(b'%PDF-1.4\nfixture').decode()}
        skipped = {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': 'Premature answer'}]}]}
        lookup = {'status': 'completed', 'output': [{'type': 'function_call',
                  'name': 'search_resolution', 'call_id': 'lookup',
                  'arguments': '{"query":"R4"}'}]}
        final = {'status': 'completed', 'output': [{'type': 'message', 'content': [
            {'type': 'output_text', 'text': 'Preliminary R4 review with source references.'}]}]}
        choices = []
        responses = iter([skipped, lookup, final])
        def provider(payload, *args):
            choices.append(payload['tool_choice'])
            return next(responses)
        with patch.dict(server.os.environ, {'OPENAI_API_KEY': 'test-only'}), \
                patch('server.call_provider', side_effect=provider):
            result = server.review(data)
        self.assertEqual(choices[:2], [{'type': 'function', 'name': 'search_resolution'}] * 2)
        self.assertEqual(choices[2], 'auto')
        self.assertIn('Preliminary R4 review', result['report'])
