"""Resumable, page-cited Buildings Bulletin embedding index and vector search."""
import argparse
from functools import lru_cache
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'references/dob-text'
OUTPUT=ROOT/'references/bulletin-embeddings'
MODEL='text-embedding-3-small'
DIMENSIONS=1536


def chunks(source=SOURCE):
    documents=json.loads((Path(source)/'index.json').read_text())['documents']
    result=[]
    for doc in documents:
        if doc['collection']!='buildings-bulletins':continue
        record=json.loads((Path(source)/doc['text_file']).read_text())
        for page,text in enumerate(record['pages'],1):
            if not text.strip():continue
            for start in range(0,len(text),2500):
                excerpt=text[start:start+3000]
                item={'text':excerpt,'title':record['title'],'filename':record['filename'],
                      'page':page,'source_url':record['source_url'],'ocr_page':page in record.get('ocr_pages',[]),
                      'input':record['title'][:160]+'\n'+excerpt,'pdf_sha256':record['sha256']}
                if len(item['input'].encode())>7500:
                    raise RuntimeError('An excerpt exceeds the conservative token limit; split it before embedding.')
                item['id']=hashlib.sha256((MODEL+str(DIMENSIONS)+json.dumps(item,sort_keys=True)).encode()).hexdigest()
                result.append(item)
    return result


def token_counter():
    try:
        import tiktoken
        encoding=tiktoken.get_encoding('cl100k_base')
        return lambda text:len(encoding.encode(text,disallowed_special=())), 'cl100k_base exact tokens'
    except Exception:
        # Each token consumes at least one byte; this is a safe budget upper bound.
        return lambda text:len(text.encode()), 'UTF-8 byte upper bound; exact tokenizer unavailable'


def read_cache(output=OUTPUT):
    saved={}
    for path in Path(output).glob('batch-*.jsonl.gz'):
        with gzip.open(path,'rt',encoding='utf-8') as file:
            for line in file:
                item=json.loads(line)
                if item.get('model')!=MODEL or item.get('dimensions')!=DIMENSIONS:continue
                validate_vector(item['vector']);saved[item['id']]=item
    return saved


def validate_vector(vector):
    if not isinstance(vector,list) or len(vector)!=DIMENSIONS or not all(type(x) in (int,float) and math.isfinite(x) for x in vector):
        raise RuntimeError('Embedding response or cache has invalid vector dimensions/values.')
    if not sum(x*x for x in vector):raise RuntimeError('Embedding vector has zero magnitude.')


def embed(inputs,key):
    request=urllib.request.Request('https://api.openai.com/v1/embeddings',
        data=json.dumps({'model':MODEL,'dimensions':DIMENSIONS,'input':inputs,'encoding_format':'float'}).encode(),
        headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    try:
        with urllib.request.urlopen(request,timeout=120) as response:body=json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f'OpenAI embeddings request failed (HTTP {error.code}); check billing, access or rate limits. No automatic retry was made.') from None
    except (urllib.error.URLError,TimeoutError):
        raise RuntimeError('OpenAI embeddings could not be reached; saved batches remain available.') from None
    rows=body.get('data',[])
    if len(rows)!=len(inputs) or sorted(row.get('index',-1) for row in rows)!=list(range(len(inputs))):
        raise RuntimeError('OpenAI returned incomplete or invalid embedding results.')
    vectors=[row['embedding'] for row in sorted(rows,key=lambda row:row['index'])]
    for vector in vectors:validate_vector(vector)
    return vectors,body.get('usage',{}).get('total_tokens')


def save_manifest(expected,saved,output):
    ready=[item['id'] for item in expected if item['id'] in saved]
    manifest={'model':MODEL,'dimensions':DIMENSIONS,'expected_chunks':len(expected),'embedded_chunks':len(ready),
              'complete':bool(expected) and len(ready)==len(expected),'chunk_ids':ready,
              'source_hash':hashlib.sha256(''.join(item['id'] for item in expected).encode()).hexdigest(),
              'coverage':'Buildings Bulletins only. OCR, diagrams, legal applicability and supersession need verification.'}
    path=Path(output)/'index.json';temporary=path.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(manifest,indent=2)+'\n');temporary.replace(path)
    return manifest


def build(max_calls=5,max_tokens=200000,source=SOURCE,output=OUTPUT):
    key=os.getenv('OPENAI_API_KEY')
    if not key:raise RuntimeError('OPENAI_API_KEY is missing; add it privately to the GitHub workflow secret or worker environment.')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    expected=chunks(source);saved=read_cache(output);counter,mode=token_counter()
    pending=[item for item in expected if item['id'] not in saved]
    calls=budget=actual=unknown=0
    save_manifest(expected,saved,output)
    for start in range(0,len(pending),64):
        batch=pending[start:start+64];cost=sum(counter(item['input']) for item in batch)
        if calls>=max_calls or budget+cost>max_tokens:break
        # Record attempts before sending; usage may be unknown after an interrupted request.
        run_path=output/'last-run.json'
        calls+=1;budget+=cost;unknown+=1
        run={'api_calls':calls,'input_budget_used':budget,'budget_count_mode':mode,'reported_tokens':actual,'calls_with_unknown_usage':unknown}
        run_path.write_text(json.dumps(run,indent=2)+'\n')
        vectors,usage=embed([item['input'] for item in batch],key)
        batch_id=hashlib.sha256(''.join(item['id'] for item in batch).encode()).hexdigest()
        path=output/('batch-'+batch_id+'.jsonl.gz');temporary=path.with_suffix('.gz.tmp')
        with gzip.open(temporary,'wt',encoding='utf-8') as file:
            for item,vector in zip(batch,vectors):
                record=dict(item,model=MODEL,dimensions=DIMENSIONS,vector=vector)
                file.write(json.dumps(record,separators=(',',':'))+'\n');saved[item['id']]=record
        temporary.replace(path)
        if type(usage) is int:actual+=usage;unknown-=1
        run.update(reported_tokens=actual,calls_with_unknown_usage=unknown)
        run_path.write_text(json.dumps(run,indent=2)+'\n')
        manifest=save_manifest(expected,saved,output)
        print(json.dumps({'embedded_chunks':manifest['embedded_chunks'],'expected_chunks':len(expected),'reported_tokens':actual}),flush=True)
    return save_manifest(expected,saved,output)


@lru_cache(maxsize=1)
def index():
    manifest=json.loads((OUTPUT/'index.json').read_text())
    if not manifest['complete']:raise RuntimeError('Bulletin embedding index is incomplete; finish its build first.')
    current=hashlib.sha256(''.join(item['id'] for item in chunks()).encode()).hexdigest()
    if current!=manifest['source_hash']:raise RuntimeError('Bulletin sources changed; update their embedding index before semantic search.')
    saved=read_cache();items=[saved[key] for key in manifest['chunk_ids']]
    return [(item,math.sqrt(sum(v*v for v in item['vector']))) for item in items]


def search(query,limit=4):
    if not str(query).strip():return []
    key=os.getenv('OPENAI_API_KEY')
    if not key:raise RuntimeError('Semantic search requires OPENAI_API_KEY.')
    items=index()  # Verify availability before spending on the query.
    vector,_=embed([str(query)[:2000]],key);vector=vector[0]
    norm=math.sqrt(sum(v*v for v in vector))
    ranked=sorted(((sum(a*b for a,b in zip(vector,item['vector']))/(norm*magnitude),item) for item,magnitude in items),key=lambda pair:pair[0],reverse=True)
    return [{'text':item['text'],'citation':f"Buildings Bulletin: {item['title']} ({item['filename']}), PDF page {item['page']}",
             'source_url':item['source_url'],'filename':item['filename'],'collection':'buildings-bulletins',
             'ocr_page':item['ocr_page'],'similarity':score} for score,item in ranked[:limit]]


def record_build_failure(error,output=OUTPUT):
    # Only our controlled errors are safe to persist; unexpected exceptions can contain secrets.
    message=str(error) if isinstance(error,RuntimeError) else 'Embedding operation failed; check source files and configuration. Secret values are not logged.'
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    (output/'last-error.json').write_text(json.dumps({'status':'failed','message':message},indent=2)+'\n')
    return message


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['estimate','build','search'])
    parser.add_argument('--max-api-calls',type=int,default=5)
    parser.add_argument('--max-tokens',type=int,default=200000)
    parser.add_argument('--query')
    args=parser.parse_args()
    try:
        if not 1<=args.max_api_calls<=100 or not 1<=args.max_tokens<=10000000:parser.error('Budget out of bounds.')
        if args.command=='estimate':
            items=chunks();counter,mode=token_counter();total=sum(counter(item['input']) for item in items)
            print(json.dumps({'model':MODEL,'dimensions':DIMENSIONS,'chunks':len(items),'input_tokens_or_upper_bound':total,'count_mode':mode,'api_calls_made':0},indent=2))
        elif args.command=='build':
            result=build(args.max_api_calls,args.max_tokens)
            (OUTPUT/'last-error.json').unlink(missing_ok=True)
            print(json.dumps({k:v for k,v in result.items() if k!='chunk_ids'},indent=2))
        else:
            if not args.query:parser.error('--query is required')
            print(json.dumps(search(args.query),indent=2))
    except Exception as error:
        if args.command=='build':print(record_build_failure(error))
        else:print(str(error) if isinstance(error,RuntimeError) else 'Embedding operation failed; check source files and configuration. Secret values are not logged.')
        raise SystemExit(1)
