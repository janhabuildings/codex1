import gzip
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import bulletin_embeddings as embeddings

class EmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.items=[{'id':str(i),'input':'example','text':'excerpt','title':'Bulletin','filename':'bb.pdf','page':1,'source_url':'https://www.nyc.gov/bb.pdf','ocr_page':False} for i in range(65)]
        self.vector=[1.0]+[0.0]*(embeddings.DIMENSIONS-1)

    def tearDown(self):self.temp.cleanup()

    def test_budget_and_resume_do_not_repeat_completed_inputs(self):
        with patch.dict(embeddings.os.environ,{'OPENAI_API_KEY':'test-only'}),patch.object(embeddings,'chunks',return_value=self.items),patch.object(embeddings,'token_counter',return_value=(lambda text:1,'test tokens')),patch.object(embeddings,'embed',side_effect=lambda inputs,key:([self.vector for _ in inputs],len(inputs))) as embed:
            first=embeddings.build(1,1000,output=self.root)
            self.assertEqual(first['embedded_chunks'],64);self.assertFalse(first['complete'])
            second=embeddings.build(1,1000,output=self.root)
            self.assertTrue(second['complete']);self.assertEqual(second['embedded_chunks'],65)
            embeddings.build(1,1000,output=self.root)
            self.assertEqual(embed.call_count,2)
            self.assertEqual(len(embed.call_args.args[0]),1)

    def test_token_budget_prevents_paid_request(self):
        with patch.dict(embeddings.os.environ,{'OPENAI_API_KEY':'test-only'}),patch.object(embeddings,'chunks',return_value=self.items),patch.object(embeddings,'token_counter',return_value=(lambda text:100,'test tokens')),patch.object(embeddings,'embed') as embed:
            result=embeddings.build(2,100,output=self.root)
        embed.assert_not_called();self.assertEqual(result['embedded_chunks'],0)

    def test_failure_keeps_completed_batches_for_resume(self):
        with patch.dict(embeddings.os.environ,{'OPENAI_API_KEY':'test-only'}),patch.object(embeddings,'chunks',return_value=self.items),patch.object(embeddings,'token_counter',return_value=(lambda text:1,'test tokens')),patch.object(embeddings,'embed',side_effect=[([self.vector]*64,64),RuntimeError('Rate limit')]):
            with self.assertRaises(RuntimeError):embeddings.build(2,1000,output=self.root)
        self.assertEqual(len(embeddings.read_cache(self.root)),64)
        usage=json.loads((self.root/'last-run.json').read_text());self.assertEqual(usage['calls_with_unknown_usage'],1)

    def test_invalid_vectors_are_rejected(self):
        for vector in [[],[math.nan]*embeddings.DIMENSIONS,[0.0]*embeddings.DIMENSIONS]:
            with self.assertRaises(RuntimeError):embeddings.validate_vector(vector)

    def test_semantic_ranking_retains_pdf_citations(self):
        strongest=dict(self.items[0],vector=self.vector,page=3)
        other_vector=[0.0,1.0]+[0.0]*(embeddings.DIMENSIONS-2)
        weaker=dict(self.items[1],vector=other_vector,page=8)
        with patch.dict(embeddings.os.environ,{'OPENAI_API_KEY':'test-only'}),patch.object(embeddings,'index',return_value=[(weaker,1.0),(strongest,1.0)]),patch.object(embeddings,'embed',return_value=([self.vector],2)):
            hits=embeddings.search('different wording',limit=1)
        self.assertEqual(len(hits),1);self.assertIn('PDF page 3',hits[0]['citation'])
        self.assertEqual(hits[0]['source_url'],'https://www.nyc.gov/bb.pdf')

    def test_incomplete_index_does_not_spend_on_query_embedding(self):
        with patch.dict(embeddings.os.environ,{'OPENAI_API_KEY':'test-only'}),patch.object(embeddings,'index',side_effect=RuntimeError('Index incomplete')),patch.object(embeddings,'embed') as embed:
            with self.assertRaises(RuntimeError):embeddings.search('question')
        embed.assert_not_called()
