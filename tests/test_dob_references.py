import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import dob_references
import server

spec=importlib.util.spec_from_file_location('extract_dob_test',Path(__file__).resolve().parents[1]/'scripts/extract_dob.py')
extractor=importlib.util.module_from_spec(spec);spec.loader.exec_module(extractor)

class DobSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.database=self.root/'search.sqlite'
        documents=[]
        for kind,text in [('tppn','Attic floor area calculations'),('buildings-bulletins','Buildings Bulletin 2025-001: attic floor area interpretation')]:
            path=self.root/(kind+'.json')
            path.write_text(json.dumps({'pages':[text,'Second page accessible egress guidance'], 'title':kind+' reference',
                'collection':kind,'filename':kind+'.pdf','source_url':'https://www.nyc.gov/document.pdf','ocr_pages':[1]}))
            documents.append({'text_file':path.name})
        (self.root/'index.json').write_text(json.dumps({'documents':documents}))
        dob_references.build_index(self.root,self.database)

    def tearDown(self):self.temp.cleanup()

    def test_page_citations_filters_and_ocr_provenance(self):
        hits=dob_references.search('attic floor',database=self.database)
        self.assertEqual(len(hits),2)
        self.assertTrue(all('PDF page 1' in hit['citation'] and hit['ocr_page'] for hit in hits))
        filtered=dob_references.search('attic',collection='tppn',database=self.database)
        self.assertEqual(len(filtered),1)
        self.assertEqual(filtered[0]['collection'],'tppn')
        self.assertEqual(dob_references.search('2025-001',database=self.database)[0]['collection'],'buildings-bulletins')
        self.assertEqual(dob_references.search('',database=self.database),[])
        self.assertEqual(dob_references.search('absentword',database=self.database),[])

    def test_review_routes_dob_lookup_with_source_link(self):
        calls=[{'status':'completed','output':[{'type':'function_call','name':'search_resolution','call_id':'zr','arguments':'{"query":"23-21"}'}]},
               {'status':'completed','output':[{'type':'function_call','name':'search_dob_references','call_id':'dob','arguments':'{"query":"attic","collection":"tppn"}'}]},
               {'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':'Needs professional verification.'}]}]}]
        original=dob_references.search
        data={'address':'Test site','filename':'test.pdf','pdf':base64.b64encode(b'%PDF-1.4 fixture').decode()}
        with patch.dict(server.os.environ,{'OPENAI_API_KEY':'test-only'}),patch('server.extract_drawing',return_value='Drawing notes'),patch('server.call_provider',side_effect=calls) as provider,patch('server.dob_references.DATABASE',self.database),patch('server.dob_references.search',side_effect=lambda q,c:original(q,c,self.database)):
            report=server.review(data)
        self.assertIn('https://www.nyc.gov/document.pdf',report['report'])
        self.assertTrue(any(tool['name']=='search_dob_references' for tool in provider.call_args.args[0]['tools']))

    def test_extraction_preserves_blank_page_numbers_and_rejects_changed_pdf(self):
        import hashlib
        from subprocess import CompletedProcess
        for collection in ['tppn','buildings-bulletins']:
            folder=self.root/'references'/collection;folder.mkdir(parents=True)
            pdf=folder/'test.pdf';pdf.write_bytes(b'%PDF-fixture')
            (folder/'index.json').write_text(json.dumps({'documents':[{'filename':'test.pdf','title':'Notice','source_url':'https://www.nyc.gov/test.pdf','sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}]}))
        with patch.object(extractor.subprocess,'run',return_value=CompletedProcess([],0,stdout=b'First page\f\fThird page\f')):
            self.assertTrue(extractor.extract(self.root))
        detail=json.loads((self.root/'references/dob-text/tppn/test.pdf.json').read_text())
        self.assertEqual(len(detail['pages']),3)
        self.assertEqual(detail['pages'][1],'')
        (self.root/'references/tppn/test.pdf').write_bytes(b'changed')
        with patch.object(extractor.subprocess,'run') as process:
            self.assertFalse(extractor.extract(self.root))
            process.assert_not_called()
