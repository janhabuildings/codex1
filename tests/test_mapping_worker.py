import json
import os
import tempfile
import unittest
from unittest.mock import patch

import mapping_worker as worker


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {'MAPPING_DB_PATH': self.temp.name+'/mapping.sqlite', 'OPENAI_API_KEY':'test-only'}, clear=True)
        self.environment.start()
        self.store = worker.Store()
        self.source = {'parts':[{'part':1,'pages':['The maximum FAR for a standard R4 lot is 1.00.']} ]}
        self.task = {'key':'23-21','section':'23-21','target':'FAR','pages':[{'part':1,'page':1}]}
        self.manifest = {'tasks':[self.task]}
        self.store.seed(self.manifest,'source-test')

    def tearDown(self):
        self.store.db.close()
        self.environment.stop()
        self.temp.cleanup()

    def mapping(self):
        return {'target':'23-21','summary':'Standard allowance', 'rules':[
            {'id':'r4-standard','condition':'Verified standard R4 lot','requirement':'FAR at most 1.00',
             'evidence_needed':['district and site status'],'exceptions':[], 'cross_references':[],
             'citations':[{'section':'23-21','paragraph':'table','part':1,'page':1,
                           'quote':'The maximum FAR for a standard R4 lot is 1.00.'}]}],
             'dependencies':['12-10'],'open_questions':[]}

    def test_seed_is_repeatable_and_preserves_drafts(self):
        job, _ = self.store.claim('source-test','test')
        self.store.finish(job,'test','drafted',self.mapping())
        self.store.seed(self.manifest,'source-test')
        self.assertEqual(self.store.execute('SELECT COUNT(*) FROM mapping_tasks').fetchone()[0],1)
        self.assertEqual(self.store.execute('SELECT status FROM mapping_tasks').fetchone()[0],'drafted')

    def test_claim_excludes_active_lease_and_recovers_expired_lease(self):
        first = self.store.claim('source-test','first')
        second_store = worker.Store()
        try:
            self.assertIsNone(second_store.claim('source-test','second'))
            self.store.execute('UPDATE mapping_tasks SET lease_until=0')
            self.assertEqual(second_store.claim('source-test','second')[0],first[0])
            with self.assertRaises(RuntimeError):
                self.store.finish(first[0],'first','drafted',self.mapping())
        finally:
            second_store.db.close()

    def test_draft_is_saved_with_usage_but_not_approved(self):
        with patch('mapping_worker.map_section',return_value=(self.mapping(),{'input_tokens':100,'output_tokens':200},[])) as mapper:
            worker.run_batch(self.store,self.source,'source-test',2,1,2000,1000)
        self.assertEqual(mapper.call_count,1)
        self.assertEqual(self.store.execute('SELECT status FROM mapping_tasks').fetchone()[0],'drafted')
        self.assertEqual(self.store.execute('SELECT api_calls,input_tokens,output_tokens,unknown_usage_calls FROM mapping_runs').fetchone(),(1,100,200,0))
        with patch('mapping_worker.map_section') as mapper:
            worker.run_batch(self.store,self.source,'source-test',2,2,2000,1000)
        mapper.assert_not_called()

    def test_api_budget_stops_before_second_task(self):
        other = dict(self.task,key='23-22')
        self.store.seed({'tasks':[other]},'source-test')
        with patch('mapping_worker.map_section',return_value=(self.mapping(),{},[])) as mapper:
            worker.run_batch(self.store,self.source,'source-test',20,1,2000,1000)
        self.assertEqual(mapper.call_count,1)
        self.assertEqual(self.store.execute("SELECT COUNT(*) FROM mapping_tasks WHERE status='pending'").fetchone()[0],1)

    def test_false_citation_and_unresolved_questions_require_review(self):
        result = self.mapping()
        result['rules'][0]['citations'][0]['quote'] = 'The standard R4 FAR is actually 0.75.'
        result['open_questions'] = ['Which special district applies?']
        with patch('mapping_worker.map_section',return_value=(result,{},[])):
            worker.run_batch(self.store,self.source,'source-test',1,1,2000,1000)
        status, flags = self.store.execute('SELECT status,flags FROM mapping_tasks').fetchone()
        self.assertEqual(status,'needs_review')
        self.assertIn('citation quote not found',flags)
        self.assertIn('open questions',flags)

    def test_source_budget_does_not_truncate_or_call_api(self):
        with patch('mapping_worker.map_section') as mapper:
            worker.run_batch(self.store,self.source,'source-test',1,1,10,1000)
        mapper.assert_not_called()
        self.assertEqual(self.store.execute('SELECT status FROM mapping_tasks').fetchone()[0],'needs_review')

    def test_provider_failure_is_saved_and_stops_batch(self):
        with patch('mapping_worker.map_section',side_effect=RuntimeError('Rate limit reached')):
            with self.assertRaisesRegex(RuntimeError,'progress is saved'):
                worker.run_batch(self.store,self.source,'source-test',2,2,2000,1000)
        self.assertEqual(self.store.execute('SELECT status,error FROM mapping_tasks').fetchone(),('failed','Rate limit reached'))
        self.assertEqual(self.store.execute('SELECT unknown_usage_calls FROM mapping_runs').fetchone()[0],1)

    def test_changed_source_does_not_reuse_approval(self):
        self.store.seed(self.manifest,'new-source')
        self.assertEqual(self.store.execute('SELECT COUNT(*) FROM mapping_tasks').fetchone()[0],2)
        self.assertIsNotNone(self.store.claim('new-source','other'))
