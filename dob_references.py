"""Page-cited search of locally extracted NYC DOB notices and bulletins."""
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT/'references/dob-text'
DATABASE = ROOT/'references/dob.sqlite'


def metadata(source=SOURCE):
    path=Path(source)/'index.json'
    return json.loads(path.read_text()) if path.exists() else {'documents':[], 'errors':[], 'coverage':'DOB extraction has not run.'}


def build_index(source=SOURCE, database=DATABASE):
    db=sqlite3.connect(database)
    try:
        db.execute('DROP TABLE IF EXISTS dob_excerpts')
        db.execute('CREATE VIRTUAL TABLE dob_excerpts USING fts5(text,title,collection UNINDEXED,filename UNINDEXED,page UNINDEXED,url UNINDEXED,low_text UNINDEXED,ocr UNINDEXED)')
        for document in metadata(source)['documents']:
            detail=json.loads((Path(source)/document['text_file']).read_text())
            for page,text in enumerate(detail['pages'],1):
                if not text.strip(): continue
                for start in range(0,len(text),2500):
                    db.execute('INSERT INTO dob_excerpts VALUES(?,?,?,?,?,?,?,?)',
                        (text[start:start+3000],detail['title'],detail['collection'],detail['filename'],page,detail['source_url'],int(len(text.strip())<80),int(page in detail.get("ocr_pages",[]))))
        db.commit()
    finally: db.close()


def search(query, collection='all', database=DATABASE, *, limit=4, offset=0):
    if collection not in ('all','tppn','buildings-bulletins'): return []
    words=re.findall(r'[A-Za-z0-9]+',str(query))[:20]
    if not words or not Path(database).exists(): return []
    # Exact phrases for notice identifiers; AND joins focused terms to avoid unrelated hits.
    identifier=re.search(r'\b(20\d{2})[-/](\d{3})\b',str(query))
    if identifier:
        words=[identifier.group(1),identifier.group(2)]
    expression=' AND '.join('"'+word+'"' for word in words)
    db=sqlite3.connect(f'file:{database}?mode=ro',uri=True)
    try:
        sql='SELECT text,title,collection,filename,page,url,low_text,ocr FROM dob_excerpts WHERE dob_excerpts MATCH ?'
        args=[expression]
        if collection!='all':
            sql+=' AND collection=?';args.append(collection)
        rows=db.execute(sql+' ORDER BY bm25(dob_excerpts), rowid LIMIT ? OFFSET ?',args+[limit,offset]).fetchall()
    finally: db.close()
    return [{'text':text,'citation':f'{kind}: {title or filename} ({filename}), PDF page {page}', 'collection':kind,
             'filename':filename,'source_url':url,'low_text_page':bool(low),'ocr_page':bool(ocr),
             'coverage':'Extracted text only; diagrams and current applicability/supersession require verification.'}
            for text,title,kind,filename,page,url,low,ocr in rows]


if __name__=='__main__':
    build_index()
    print(json.dumps({'indexed_documents':len(metadata()['documents'])}))
