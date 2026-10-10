import json
import os
import tempfile
import time
import unittest
import urllib.parse
from pathlib import Path
from unittest.mock import patch
from cryptography.fernet import Fernet
import onedrive


class OneDriveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.environment = patch.dict(os.environ, {
            'MAPPING_DB_PATH':self.temp.name+'/connection.sqlite',
            'ONEDRIVE_CLIENT_ID':'test-client', 'ONEDRIVE_CLIENT_SECRET':'test-secret',
            'ONEDRIVE_REDIRECT_URI':'https://example.com/onedrive/callback',
            'ONEDRIVE_TOKEN_KEY':Fernet.generate_key().decode()}, clear=True)
        self.environment.start()

    def tearDown(self):
        self.environment.stop()
        self.temp.cleanup()

    def begin(self):
        url, binding = onedrive.start()
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        return query['state'][0], binding, query

    def token(self):
        return {'access_token':'private-access','refresh_token':'private-refresh','expires_in':3600}

    def test_pkce_offline_appfolder_scope_and_encrypted_state(self):
        state,binding,query = self.begin()
        self.assertEqual(query['code_challenge_method'], ['S256'])
        self.assertEqual(query['scope'], ['offline_access Files.ReadWrite.AppFolder'])
        self.assertNotIn('client_secret',query)
        with onedrive.database() as db:
            row = db.execute('SELECT id,binding,verifier FROM onedrive_states').fetchone()
        self.assertNotEqual(row[0],state)
        self.assertNotEqual(row[1],binding)
        self.assertNotEqual(row[2],onedrive.cipher().decrypt(row[2].encode()).decode())

    def test_callback_bound_to_browser_and_single_use(self):
        state,binding,_ = self.begin()
        query = {'state':[state], 'code':['private-code']}
        with patch('onedrive.request_json',return_value=self.token()) as request:
            with self.assertRaises(RuntimeError):
                onedrive.complete(query,'wrong-browser')
            request.assert_not_called()
            onedrive.complete(query,binding)
            with self.assertRaises(RuntimeError):
                onedrive.complete(query,binding)
            self.assertEqual(request.call_count,1)
        self.assertTrue(onedrive.status()['connected'])
        with onedrive.database() as db:
            encrypted = db.execute('SELECT token FROM onedrive_connection').fetchone()[0]
        self.assertNotIn('private-access',encrypted)
        self.assertNotIn('private-refresh',encrypted)

    def test_expired_state_never_exchanges_code(self):
        state,binding,_ = self.begin()
        with onedrive.database() as db:
            db.execute('UPDATE onedrive_states SET expires=0')
        with patch('onedrive.request_json') as request:
            with self.assertRaises(RuntimeError):
                onedrive.complete({'state':[state],'code':['code']},binding)
            request.assert_not_called()

    def test_refresh_rotates_and_persists_encrypted_token(self):
        onedrive.save_token(self.token())
        with onedrive.database() as db:
            row = db.execute('SELECT token FROM onedrive_connection').fetchone()
            token = json.loads(onedrive.cipher().decrypt(row[0].encode()))
            token['expires_at']=0
            db.execute('UPDATE onedrive_connection SET token=?',(onedrive.cipher().encrypt(json.dumps(token).encode()).decode(),))
        with patch('onedrive.request_json', return_value={'access_token':'new-access','refresh_token':'new-refresh','expires_in':3600}) as request:
            self.assertEqual(onedrive.access_token(),'new-access')
            self.assertEqual(onedrive.access_token(),'new-access')
            self.assertEqual(request.call_count,1)
        onedrive.disconnect()
        self.assertFalse(onedrive.status()['connected'])

    def test_upload_creates_categories_and_encodes_filename(self):
        file = Path(self.temp.name)/'notice #1.pdf'
        file.write_bytes(b'%PDF-test')
        responses = [{'id':'root'}, onedrive.MicrosoftError(404), {'id':'references','folder':{}},
                     onedrive.MicrosoftError(404), {'id':'category','folder':{}}, {'id':'document','name':file.name}]
        with patch('onedrive.access_token',return_value='token'), patch('onedrive.request_json',side_effect=responses) as request:
            result = onedrive.upload(file,'TPPN')
            self.assertEqual(result['id'],'document')
            args,kwargs = request.call_args
            self.assertIn('notice%20%231.pdf',args[0])
            self.assertEqual(kwargs['method'],'PUT')
            self.assertEqual(kwargs['data'],b'%PDF-test')
        with patch('onedrive.access_token') as token:
            with self.assertRaises(RuntimeError):
                onedrive.upload(file,'arbitrary-folder')
            token.assert_not_called()

    def test_configuration_requires_https_and_encryption_key(self):
        with patch.dict(os.environ, {'ONEDRIVE_REDIRECT_URI':'http://example.com/onedrive/callback'}):
            with self.assertRaises(RuntimeError): onedrive.start()
        with patch.dict(os.environ, {'ONEDRIVE_TOKEN_KEY':'invalid'}):
            with self.assertRaises(RuntimeError): onedrive.start()
