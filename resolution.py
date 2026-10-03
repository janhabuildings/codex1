"""Search the supplied resolution locally. No external zoning retrieval."""
import json
import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = ROOT / 'references' / 'resolution.json'
DATABASE = ROOT / 'references' / 'resolution.sqlite'


def build_index():
    source = json.loads(SOURCE.read_text())
    db = sqlite3.connect(DATABASE)
    db.execute('DROP TABLE IF EXISTS excerpts')
    db.execute('CREATE VIRTUAL TABLE excerpts USING fts5(text, part UNINDEXED, page UNINDEXED, global_page UNINDEXED)')
    offset = 0
    for part in source['parts']:
        for page, text in enumerate(part['pages'], 1):
            if text.strip():
                for start in range(0, len(text), 2500):
                    db.execute('INSERT INTO excerpts VALUES (?,?,?,?)',
                               (text[start:start+3000], part['part'], page, offset + page))
        offset += len(part['pages'])
    db.commit()
    db.close()


def metadata():
    source = json.loads(SOURCE.read_text())
    return {'title': source['title'], 'generated_date': source['generated_date'],
            'pages': sum(len(p['pages']) for p in source['parts']),
            'low_text_pages': sum(len(t.strip()) < 80 for p in source['parts'] for t in p['pages']),
            'coverage': 'Extracted text only; maps, diagrams and image-only provisions require visual review.'}


def search(query):
    tokens = re.findall(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', str(query))[:24]
    if not tokens:
        return []
    expression = ' OR '.join('"' + word + '"' for word in tokens)
    anchors = [word for word in tokens if re.fullmatch(r'\d{2,3}-\d{2,4}|[RCM]\d[A-Z0-9-]*', word, re.I)]
    if anchors:
        expression = ' OR '.join('"' + word + '"' for word in anchors)
    db = sqlite3.connect(f'file:{DATABASE}?mode=ro', uri=True)
    try:
        rows = db.execute('SELECT text,part,page,global_page FROM excerpts WHERE excerpts MATCH ? ORDER BY bm25(excerpts) LIMIT 8', (expression,)).fetchall()
    finally:
        db.close()
    return [{'text': text, 'citation': f'Split {part}, PDF page {page}, combined page {global_page}'}
            for text, part, page, global_page in rows]


if __name__ == '__main__':
    build_index()
    print(json.dumps(metadata()))
