"""Download NYC DOB TPPN PDFs and record provenance; standard library only."""
import argparse
from collections import deque
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request

INDEX = 'https://www.nyc.gov/site/buildings/codes/technical-policy-and-procedure-notices.page'
MAX_FILE = 30 * 1024 * 1024


def official_url(value, base=INDEX):
    url = urllib.parse.urljoin(base, value)
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ('http','https') or parsed.username or parsed.password or parsed.port not in (None,80,443):
        return None
    host = (parsed.hostname or '').lower()
    if host != 'nyc.gov' and not host.endswith('.nyc.gov'):
        return None
    return urllib.parse.urlunsplit(('https',parsed.netloc.replace(':80',''),parsed.path,parsed.query,''))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.href = dict(attrs).get('href')
            self.parts = []

    def handle_data(self, data):
        if self.href is not None:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.href is not None:
            self.links.append((self.href, re.sub(r'\s+',' ',' '.join(self.parts)).strip()))
            self.href = None


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe = official_url(newurl,req.full_url)
        if not safe:
            raise ValueError('Redirect left NYC official websites')
        return super().redirect_request(req,fp,code,msg,headers,safe)


def fetch(url):
    req = urllib.request.Request(url,headers={'User-Agent':'NYC-DOB-reference-archive/1.0'})
    with urllib.request.build_opener(OfficialRedirect()).open(req,timeout=60) as response:
        body = response.read(MAX_FILE+1)
        if len(body)>MAX_FILE:
            raise ValueError('Source exceeds 30 MB download limit')
        return body


def discover(start=INDEX, loader=fetch, max_pages=150):
    queue = deque([start])
    seen = set()
    documents = {}
    errors = []
    while queue:
        url = queue.popleft()
        if url in seen:
            continue
        if len(seen)>=max_pages:
            errors.append({'url':url,'error':'Archive page limit reached; collection may be incomplete'})
            break
        seen.add(url)
        try:
            parser = Links()
            parser.feed(loader(url).decode('utf-8',errors='replace'))
        except Exception as error:
            errors.append({'url':url,'error':str(error)})
            continue
        for href,label in parser.links:
            target = official_url(href,url)
            if not target:
                continue
            path = urllib.parse.urlsplit(target).path.lower()
            relevant = 'tppn' in path or 'tppn' in label.lower() or 'technical policy' in label.lower()
            if path.endswith('.pdf'):
                if relevant:
                    documents.setdefault(target,{'source_url':target,'title':label,'listing_url':url})
            elif relevant and target not in seen:
                queue.append(target)
    return list(documents.values()),errors


def filename(url):
    stem = Path(urllib.parse.unquote(urllib.parse.urlsplit(url).path)).stem
    stem = re.sub(r'[^A-Za-z0-9_-]+','-',stem).strip('-')[:100] or 'tppn'
    return stem+'-'+hashlib.sha256(url.encode()).hexdigest()[:10]+'.pdf'


def archive(output, start=INDEX, loader=fetch):
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    documents,errors = discover(start,loader)
    old = {}
    index = output/'index.json'
    if index.exists():
        old = {d['source_url']:d for d in json.loads(index.read_text()).get('documents',[])}
    # Retain previously collected PDFs when a listing or download temporarily fails.
    saved = dict(old)
    now = datetime.now(timezone.utc).isoformat()
    for doc in sorted(documents,key=lambda d:d['source_url']):
        try:
            body = loader(doc['source_url'])
            if len(body)>MAX_FILE or not body.lstrip().startswith(b'%PDF-'):
                raise ValueError('Response is not a PDF or exceeds the size limit')
            name = filename(doc['source_url'])
            path = output/name
            if not path.exists() or path.read_bytes()!=body:
                temporary = path.with_suffix('.pdf.tmp')
                temporary.write_bytes(body)
                temporary.replace(path)
            checksum = hashlib.sha256(body).hexdigest()
            previous = old.get(doc['source_url'],{})
            saved[doc['source_url']] = dict(doc,filename=name,bytes=len(body),sha256=checksum,
                downloaded_at=previous.get('downloaded_at',now) if previous.get('sha256')==checksum else now)
        except Exception as error:
            errors.append({'url':doc['source_url'],'error':str(error)})
    if not documents:
        errors.append({'url':start,'error':'No TPPN PDF links found; verify the official archive URL and page structure'})
    index.write_text(json.dumps({'source_index':start,'last_checked':now,
        'coverage':'Linked official TPPN PDFs only. Current applicability, rescission and supersession require verification.',
        'discovered_documents':len(documents),'documents':sorted(saved.values(),key=lambda d:d['filename']),
        'errors':errors},indent=2)+'\n')
    print(json.dumps({'discovered':len(documents),'saved':len(saved),'errors':len(errors),'folder':str(output)}))
    return not errors


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('references/tppn'))
    parser.add_argument('--index-url',default=INDEX)
    args = parser.parse_args()
    start = official_url(args.index_url)
    if not start:
        parser.error('Index URL must be an official NYC HTTPS webpage')
    sys.exit(0 if archive(args.output,start) else 1)
