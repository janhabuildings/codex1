import unittest
from unittest.mock import patch
import reference_library as library

class ReferenceLibraryTests(unittest.TestCase):
    def test_zoning_filter_preserves_all_continuation_pages(self):
        pages=[{'text':str(i),'citation':f'Split 1, PDF page {i}'} for i in range(7)]
        with patch.object(library.resolution,'search',return_value=pages),patch.object(library.dob_references,'search') as dob:
            hits=library.search('23-321','zoning-resolution')
        self.assertEqual(len(hits),7)
        self.assertTrue(all(h['collection']=='zoning-resolution' and h['source_url'] is None for h in hits))
        dob.assert_not_called()

    def test_all_collections_are_interleaved_without_losing_citations(self):
        with patch.object(library.resolution,'search',return_value=[{'text':'ZR','citation':'Split 1, PDF page 455'}]),patch.object(library.dob_references,'search',side_effect=lambda q,c:[{'text':c,'citation':c}]):
            hits=library.search('yards')
        self.assertEqual([h['text'] for h in hits],['ZR','tppn','buildings-bulletins'])
        self.assertEqual(hits[0]['citation'],'Split 1, PDF page 455')

    def test_dob_filter_does_not_search_zoning(self):
        with patch.object(library.resolution,'search') as zr,patch.object(library.dob_references,'search',return_value=[]) as dob:
            library.search('2025-001','buildings-bulletins')
        zr.assert_not_called();dob.assert_called_once_with('2025-001','buildings-bulletins')
