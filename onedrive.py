"""Personal OneDrive OAuth connection and app-folder document uploads."""
import argparse
import base64
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

AUTH = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/'
GRAPH = 'https://graph.microsoft.com/v1.0'
SCOPE = 'offline_access Files.ReadWrite.AppFolder'


def configuration():
    names = ['ONEDRIVE_CLIENT_ID', 'ONEDRIVE_CLIENT_SECRET', 'ONEDRIVE_REDIRECT_URI', 'ONEDRIVE_TOKEN_KEY']
    if any(not os.getenv(n) for n in names):
        raise RuntimeError('Configure ONEDRIVE_CLIENT_ID, ONEDRIVE_CLIENT_SECRET, ONEDRIVE_REDIRECT_URI and ONEDRIVE_TOKEN_KEY in Render.')
    if not (os.getenv('MAPPING_DATABASE_URL') or os.getenv('MAPPING_DB_PATH')):
        raise RuntimeError('Configure persistent MAPPING_DATABASE_URL storage for the web app and document worker.')
    uri = urllib.parse.urlsplit(os.environ['ONEDRIVE_REDIRECT_URI'])
    if uri.scheme != 'https' or not uri.netloc or uri.path != '/onedrive/callback' or uri.query or uri.fragment or uri.username:
        raise RuntimeError('ONEDRIVE_REDIRECT_URI must be your HTTPS app URL followed by /onedrive/callback.')
    cipher()  # Validate encryption before any sign-in or API request.


def cipher():
    from cryptography.fernet import Fernet
    try:
        return Fernet(os.environ['ONEDRIVE_TOKEN_KEY'].encode())
    except (KeyError, ValueError):
        raise RuntimeError('ONEDRIVE_TOKEN_KEY must be a valid Fernet encryption key.') from None


@contextmanager
def database():
    from mapping_worker import Store
    store = Store()
    try:
        store.execute('CREATE TABLE IF NOT EXISTS onedrive_states (id TEXT PRIMARY KEY, binding TEXT NOT NULL, verifier TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL)')
        store.execute('CREATE TABLE IF NOT EXISTS onedrive_connection (id TEXT PRIMARY KEY, token TEXT NOT NULL)')
        yield store
    finally:
        store.db.close()


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class MicrosoftError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__('Microsoft request failed (HTTP %s). Check app registration, consent and connection; reconnect if necessary.' % status)


def request_json(url, data=None, token=None, method=None, raw=False, json_body=False):
    headers = {}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    if data is not None:
        if json_body:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data).encode()
        elif raw:
            headers['Content-Type'] = 'application/octet-stream'
        else:
            data = urllib.parse.urlencode(data).encode()
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=60) as response:
            content = response.read()
            return json.loads(content) if content else {}
    except urllib.error.HTTPError as error:
        raise MicrosoftError(error.code) from None
    except (urllib.error.URLError, TimeoutError, ValueError):
        raise RuntimeError('Microsoft could not be reached or returned an invalid response. Try again.') from None


def start():
    configuration()
    state, binding, verifier = (secrets.token_urlsafe(32) for _ in range(3))
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    with database() as db:
        db.execute('DELETE FROM onedrive_states WHERE expires<?', (time.time(),))
        db.execute('INSERT INTO onedrive_states(id,binding,verifier,expires) VALUES(?,?,?,?)',
                   (digest(state), digest(binding), cipher().encrypt(verifier.encode()).decode(), time.time()+600))
    query = {'client_id':os.environ['ONEDRIVE_CLIENT_ID'], 'response_type':'code',
             'redirect_uri':os.environ['ONEDRIVE_REDIRECT_URI'], 'scope':SCOPE,
             'state':state, 'code_challenge':challenge, 'code_challenge_method':'S256', 'response_mode':'query'}
    return AUTH+'authorize?'+urllib.parse.urlencode(query), binding


def complete(query, binding):
    configuration()
    state = query.get('state', [''])[0]
    if not state or not binding:
        raise RuntimeError('Sign-in state is missing. Start Connect OneDrive again.')
    with database() as db:
        row = db.execute('DELETE FROM onedrive_states WHERE id=? AND binding=? AND expires>? RETURNING verifier',
                         (digest(state), digest(binding), time.time())).fetchone()
    if not row:
        raise RuntimeError('Sign-in expired or was already used. Start Connect OneDrive again.')
    if query.get('error') or not query.get('code', [''])[0]:
        raise RuntimeError('Microsoft sign-in was not completed. Start Connect OneDrive again.')
    verifier = cipher().decrypt(row[0].encode()).decode()
    body = request_json(AUTH+'token', {'client_id':os.environ['ONEDRIVE_CLIENT_ID'],
        'client_secret':os.environ['ONEDRIVE_CLIENT_SECRET'], 'grant_type':'authorization_code',
        'code':query['code'][0], 'redirect_uri':os.environ['ONEDRIVE_REDIRECT_URI'], 'code_verifier':verifier, 'scope':SCOPE})
    save_token(body)


def save_token(body):
    if not body.get('access_token') or not body.get('refresh_token'):
        raise RuntimeError('Microsoft did not return an offline connection. Reconnect and grant consent.')
    body['expires_at'] = time.time()+int(body.get('expires_in', 3600))
    encrypted = cipher().encrypt(json.dumps(body).encode()).decode()
    with database() as db:
        db.execute('INSERT INTO onedrive_connection(id,token) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET token=excluded.token', ('owner', encrypted))


def status():
    configuration()
    with database() as db:
        row = db.execute('SELECT token FROM onedrive_connection WHERE id=?', ('owner',)).fetchone()
    if row:
        try:
            cipher().decrypt(row[0].encode())
        except Exception:
            raise RuntimeError('Saved OneDrive connection cannot be decrypted. Restore the encryption key or reconnect.') from None
    return {'connected':bool(row), 'folder':'Apps / your Microsoft app / NYC DOB References'}


def disconnect():
    configuration()
    with database() as db:
        db.execute('DELETE FROM onedrive_connection')
        db.execute('DELETE FROM onedrive_states')


def access_token():
    configuration()
    # Hold a database write lock while refreshing to serialize rotating refresh tokens.
    with database() as db:
        db.execute('BEGIN' if db.postgres else 'BEGIN IMMEDIATE')
        try:
            sql = 'SELECT token FROM onedrive_connection WHERE id=?' + (' FOR UPDATE' if db.postgres else '')
            row = db.execute(sql, ('owner',)).fetchone()
            if not row:
                raise RuntimeError('Connect OneDrive through the website first.')
            try:
                body = json.loads(cipher().decrypt(row[0].encode()))
            except Exception:
                raise RuntimeError('Saved connection cannot be decrypted. Restore the token key or reconnect.') from None
            if body['expires_at'] < time.time()+120:
                fresh = request_json(AUTH+'token', {'client_id':os.environ['ONEDRIVE_CLIENT_ID'],
                    'client_secret':os.environ['ONEDRIVE_CLIENT_SECRET'], 'grant_type':'refresh_token',
                    'refresh_token':body['refresh_token'], 'scope':SCOPE})
                if not fresh.get('access_token'):
                    raise RuntimeError('Microsoft did not renew the connection. Reconnect OneDrive.')
                fresh['refresh_token'] = fresh.get('refresh_token') or body['refresh_token']
                fresh['expires_at'] = time.time()+int(fresh.get('expires_in',3600))
                db.execute('UPDATE onedrive_connection SET token=? WHERE id=?',
                           (cipher().encrypt(json.dumps(fresh).encode()).decode(), 'owner'))
                body = fresh
            db.execute('COMMIT')
            return body['access_token']
        except Exception:
            db.execute('ROLLBACK')
            raise


def upload(path, category):
    path = Path(path)
    if category not in ('TPPN', 'Buildings Bulletins') or path.suffix.lower() not in ('.pdf','.txt','.json'):
        raise RuntimeError('Use TPPN or Buildings Bulletins and a PDF, TXT or JSON file.')
    if not path.is_file() or path.stat().st_size > 25*1024*1024:
        raise RuntimeError('Upload requires an existing file of at most 25 MB.')
    token = access_token()
    root = request_json(GRAPH+'/me/drive/special/approot', token=token)
    def folder(parent, name):
        parent_id = urllib.parse.quote(parent['id'], safe='')
        lookup = GRAPH+'/me/drive/items/'+parent_id+':/'+urllib.parse.quote(name,safe='')
        try:
            found = request_json(lookup, token=token)
        except MicrosoftError as error:
            if error.status != 404:
                raise
            try:
                found = request_json(GRAPH+'/me/drive/items/'+parent_id+'/children',
                    data={'name':name,'folder':{},'@microsoft.graph.conflictBehavior':'fail'},
                    token=token, method='POST', json_body=True)
            except MicrosoftError as create_error:
                if create_error.status != 409:
                    raise
                found = request_json(lookup, token=token)
        if 'folder' not in found:
            raise RuntimeError('OneDrive destination exists but is not a folder.')
        return found
    destination = folder(folder(root, 'NYC DOB References'), category)
    name = urllib.parse.quote(path.name, safe='')
    folder_id = urllib.parse.quote(destination['id'], safe='')
    url = GRAPH+'/me/drive/items/'+folder_id+':/'+name+':/content'
    result = request_json(url, data=path.read_bytes(), token=token, method='PUT', raw=True)
    return {'name':result.get('name'), 'id':result.get('id'), 'webUrl':result.get('webUrl')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['status','upload'])
    parser.add_argument('--file', type=Path)
    parser.add_argument('--category', choices=['TPPN','Buildings Bulletins'])
    args = parser.parse_args()
    try:
        if args.command == 'upload' and (not args.file or not args.category):
            parser.error('upload requires --file and --category')
        print(json.dumps(status() if args.command == 'status' else upload(args.file,args.category)))
    except Exception as error:
        print(str(error) if isinstance(error,RuntimeError) else 'OneDrive operation failed; check configuration. Credentials are not displayed.')
        raise SystemExit(1)
