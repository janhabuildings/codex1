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

    def test_pagination_preserves_continuations_and_stops_at_end(self):
        pages=library.search_page('23-332','zoning-resolution')
        self.assertEqual(len(pages['excerpts']),3)
        self.assertFalse(pages['has_more'])
        first=library.search_page('23-421','zoning-resolution',0)
        second=library.search_page('23-421','zoning-resolution',1)
        third=library.search_page('23-421','zoning-resolution',2)
        self.assertTrue(first['has_more'])
        self.assertFalse(second['has_more'])
        self.assertFalse(third['has_more'])
        hits=first['excerpts']+second['excerpts']+third['excerpts']
        self.assertEqual(len(hits),8)
        self.assertEqual(len({h['citation'] for h in hits}),8)

    def test_verified_table_does_not_displace_paginated_matches(self):
        def lookup(query,**kwargs):
            rows=[{'text':str(i),'citation':str(i)} for i in range(9)]
            offset=kwargs['offset'];rows=rows[offset:offset+kwargs['limit']]
            return ([{'text':'table','citation':'verified','reference_context':True}]+rows) if offset==0 else rows
        with patch.object(library.resolution,'search',side_effect=lookup):
            pages=[library.search_page('FAR','zoning-resolution',n) for n in range(3)]
        citations=[h['citation'] for page in pages for h in page['excerpts']]
        self.assertEqual(citations,['verified']+[str(n) for n in range(9)])
        self.assertFalse(pages[-1]['has_more'])

    def test_hybrid_merges_page_matches_and_caches_paid_query(self):
        library.hybrid_bulletins.cache_clear()
        common={'text':'one','citation':'Bulletin, PDF page 1','filename':'a.pdf','collection':'buildings-bulletins'}
        other=dict(common,text='two',filename='b.pdf')
        with patch.object(library.bulletin_embeddings,'search',return_value=[common,other]) as semantic,patch.object(library.dob_references,'search',return_value=[common]):
            first=library.search_page('hybrid example','buildings-bulletins',mode='hybrid')
            library.search_page('hybrid example','buildings-bulletins',mode='hybrid')
        self.assertEqual(len(first['excerpts']),2)
        self.assertEqual(first['excerpts'][0]['match_method'],'keyword + meaning')
        semantic.assert_called_once()
        library.hybrid_bulletins.cache_clear()

    def test_hybrid_failure_returns_keyword_results(self):
        library.hybrid_bulletins.cache_clear()
        with patch.object(library.bulletin_embeddings,'search',side_effect=RuntimeError('Unavailable')),patch.object(library.dob_references,'search',return_value=[{'text':'keyword'}]):
            result=library.search_page('fallback','buildings-bulletins',mode='hybrid')
        self.assertEqual(result['excerpts'][0]['text'],'keyword')
        self.assertIn('unavailable',result['notice'])

    def test_keyword_search_never_calls_embeddings(self):
        with patch.object(library.bulletin_embeddings,'search') as semantic:
            library.search_page('egress','buildings-bulletins',mode='keyword')
            library.search_page('yards','zoning-resolution',mode='hybrid')
        semantic.assert_not_called()
