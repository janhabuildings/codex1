"""OCR low-text DOB pages locally with Poppler/Tesseract; no paid API calls."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
import hashlib
from pathlib import Path
import subprocess
import tempfile
from extract_dob import ROOT,extract


def process(document):
    path=ROOT/'references/dob-text'/document['text_file']
    record=json.loads(path.read_text())
    todo=[page for page in record['low_text_pages'] if page not in record.get('ocr_attempted_pages',[])]
    if not todo:return []
    pdf=ROOT/'references'/record['collection']/record['filename']
    if hashlib.sha256(pdf.read_bytes()).hexdigest()!=record['sha256']:
        return [{'filename':record['filename'],'error':'PDF changed before OCR'}]
    errors=[]
    record.setdefault('ocr_pages',[]);record.setdefault('ocr_attempted_pages',[])
    for page in todo:
        try:
            with tempfile.TemporaryDirectory() as directory:
                prefix=Path(directory)/'page'
                subprocess.run(['pdftoppm','-f',str(page),'-l',str(page),'-r','180','-singlefile','-png',str(pdf),str(prefix)],
                               check=True,capture_output=True,timeout=120)
                result=subprocess.run(['tesseract',str(prefix)+'.png','stdout','-l','eng'],check=True,capture_output=True,timeout=120,env=dict(os.environ,OMP_THREAD_LIMIT='1'))
                text=result.stdout.decode('utf-8').strip()
                if len(text)>len(record['pages'][page-1].strip()):
                    record['pages'][page-1]=text+'\n';record['ocr_pages'].append(page)
                record['ocr_attempted_pages'].append(page)
        except Exception:
            errors.append({'filename':record['filename'],'page':page,'error':'Page OCR failed; inspect PDF and retry OCR.'})
    record['low_text_pages']=[page for page,text in enumerate(record['pages'],1) if len(text.strip())<80]
    path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(record['filename']+': OCR attempted '+str(len(todo))+' pages',flush=True)
    return errors


if __name__=='__main__':
    index=ROOT/'references/dob-text/index.json'
    documents=json.loads(index.read_text())['documents']
    errors=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(process,documents):errors.extend(result)
    extract()
    result=json.loads(index.read_text());result['ocr_errors']=errors
    result['coverage']='Text extraction plus Tesseract OCR on low-text pages. OCR may misread text, numbers and tables; diagrams and legal applicability still require visual verification.'
    index.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'ocr_errors':len(errors),'remaining_low_text_pages':sum(len(d['low_text_pages']) for d in result['documents'])}))
    raise SystemExit(1 if errors else 0)
