import importlib.util
from pathlib import Path
import tempfile
import unittest
import json

spec=importlib.util.spec_from_file_location('tppn',Path(__file__).resolve().parents[1]/'scripts/download_tppn.py')
tppn=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tppn)

class TppnTests(unittest.TestCase):
    def test_discovery_follows_year_pages_deduplicates_and_rejects_external_links(self):
        year='https://www.nyc.gov/site/buildings/codes/tppn-2000.page'
        pdf='https://www.nyc.gov/assets/buildings/pdf/tppn0100.pdf'
        pages={tppn.INDEX:b'<a href="tppn-2000.page">2000 TPPNs</a><a href="https://evil.example/tppn.pdf">TPPN</a>',
               year:b'<a href="/assets/buildings/pdf/tppn0100.pdf">TPPN 1/00</a><a href="/assets/buildings/pdf/tppn0100.pdf">Duplicate</a><a href="/assets/buildings/pdf/other.pdf">Other</a>'}
        docs,errors=tppn.discover(loader=pages.__getitem__)
        self.assertEqual(errors,[])
        self.assertEqual([d['source_url'] for d in docs],[pdf])
        self.assertEqual(docs[0]['listing_url'],year)

    def test_partial_failure_retains_prior_files_and_records_errors(self):
        pdf='https://www.nyc.gov/assets/buildings/pdf/tppn0100.pdf'
        pages={tppn.INDEX:b'<a href="/assets/buildings/pdf/tppn0100.pdf">TPPN 1/00</a>',pdf:b'%PDF-1.4 test'}
        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(tppn.archive(directory,loader=pages.__getitem__))
            index=json.loads((Path(directory)/'index.json').read_text())
            saved=Path(directory)/index['documents'][0]['filename']
            self.assertEqual(saved.read_bytes(),b'%PDF-1.4 test')
            pages[pdf]=b'<html>not a PDF</html>'
            self.assertFalse(tppn.archive(directory,loader=pages.__getitem__))
            index=json.loads((Path(directory)/'index.json').read_text())
            self.assertEqual(len(index['documents']),1)
            self.assertEqual(len(index['errors']),1)
            self.assertEqual(saved.read_bytes(),b'%PDF-1.4 test')

    def test_no_pdf_discovery_does_not_claim_success(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(tppn.archive(directory,loader=lambda url:b'<html>empty</html>'))

    def test_url_and_filename_boundaries(self):
        for url in ['https://nyc.gov.evil.example/tppn.pdf','file:///tmp/tppn.pdf','https://name:password@nyc.gov/tppn.pdf']:
            self.assertIsNone(tppn.official_url(url))
        name=tppn.filename('https://www.nyc.gov/assets/buildings/pdf/..%2fnotice.pdf')
        self.assertNotIn('/',name)
        self.assertNotIn('..',name)
