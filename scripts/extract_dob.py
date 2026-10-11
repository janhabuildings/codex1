"""Extract archived DOB PDFs with Poppler, retaining PDF page boundaries."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def extract(root=ROOT):
    root=Path(root)
    output=root/'references/dob-text';output.mkdir(parents=True,exist_ok=True)
    documents=[];errors=[];archive_errors=[]
    for collection in ('tppn','buildings-bulletins'):
        folder=root/'references'/collection
        index=folder/'index.json'
        if not index.exists():
            errors.append({'collection':collection,'error':'Archive index is missing; run its download workflow first.'});continue
        archive=json.loads(index.read_text())
        archive_errors.extend(dict(error,collection=collection) for error in archive.get('errors',[]))
        for item in archive['documents']:
            filename=item['filename']
            if Path(filename).name!=filename:
                errors.append({'collection':collection,'filename':filename,'error':'Unsafe archive filename'});continue
            destination=output/collection/(filename+'.json')
            try:
                pdf=folder/filename
                checksum=hashlib.sha256(pdf.read_bytes()).hexdigest()
                if checksum!=item['sha256']:raise ValueError('PDF checksum does not match its source index')
                cached=json.loads(destination.read_text()) if destination.exists() else None
                if cached and cached.get('sha256')==checksum and cached.get('extractor')=='pdftotext-layout-v1':
                    record=cached
                else:
                    result=subprocess.run(['pdftotext','-layout','-enc','UTF-8',str(pdf),'-'],capture_output=True,timeout=120)
                    if result.returncode:raise ValueError('Poppler could not extract this PDF; check encryption or file integrity')
                    pages=result.stdout.decode('utf-8').split('\f')
                    if pages and not pages[-1].strip():pages.pop()
                    if not pages:raise ValueError('No PDF pages extracted')
                    record={'collection':collection,'filename':filename,'title':item.get('title') or Path(filename).stem,
                            'source_url':item['source_url'],'listing_url':item.get('listing_url'), 'sha256':checksum,
                            'extractor':'pdftotext-layout-v1','pages':pages,
                            'low_text_pages':[number for number,text in enumerate(pages,1) if len(text.strip())<80]}
                    destination.parent.mkdir(parents=True,exist_ok=True)
                    destination.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
                documents.append({k:record[k] for k in ('collection','filename','title','source_url','sha256','low_text_pages')} |
                    {'pages':len(record['pages']),'text_file':str(destination.relative_to(output)), 'ocr_pages':record.get('ocr_pages',[]), 'ocr_attempted_pages':record.get('ocr_attempted_pages',[])})
            except Exception as error:
                errors.append({'collection':collection,'filename':filename,'error':str(error)})
    manifest={'generated_at':datetime.now(timezone.utc).isoformat(),'documents':documents,'errors':errors,'archive_errors':archive_errors,
              'coverage':'Page text may include explicitly identified OCR. Low-text pages and all diagrams require visual review; current applicability/supersession is not inferred.'}
    (output/'index.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'documents':len(documents),'pages':sum(d['pages'] for d in documents),
                     'low_text_pages':sum(len(d['low_text_pages']) for d in documents),'extraction_errors':len(errors),'archive_errors':len(archive_errors)}))
    for error in errors:print(json.dumps(error),file=sys.stderr)
    return not errors


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    sys.exit(0 if extract() else 1)
