"""Search the supplied resolution locally. No external zoning retrieval."""
import json
import re
import sqlite3
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).parent
SOURCE = ROOT / 'references' / 'resolution.json'
DATABASE = ROOT / 'references' / 'resolution.sqlite'

# Verified continuations: a heading-only hit must not omit the next page's rule.
SECTION_PAGES = {'23-321': (452, 453, 454), '23-332': (455, 456, 457),
                 '23-333': (457, 458), '23-342': (464, 465),
                 '23-42': (498,), '23-421': tuple(range(498, 506)),
                 '23-422': (505, 506), '23-424': (507, 508),
                 '24-01': (564,)}


@lru_cache(maxsize=1)
def source_pages():
    return json.loads(SOURCE.read_text())['parts'][0]['pages']


def far_tables():
    return json.loads((ROOT / 'references' / 'far_tables.json').read_text())


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


def search(query, use_scope='unknown', *, limit=4, offset=0, paginate=False):
    tokens = re.findall(r'[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*', str(query))[:24]
    if not tokens:
        return []
    if use_scope == 'residential' and not any(re.fullmatch(r'\d{2,3}-\d{2,4}', word) for word in tokens):
        subject = str(query).lower()
        for phrase, section in [('front yard', '23-321'), ('side yard', '23-332'),
                                ('rear yard', '23-342'), ('height', '23-42')]:
            if phrase in subject:
                return search(section, limit=limit, offset=offset, paginate=paginate)
    requested = [word for word in tokens if word in SECTION_PAGES]
    if requested:
        pages = source_pages()
        selected = {}
        for section in requested:
            for page in SECTION_PAGES[section]:
                selected.setdefault(page, []).append(section)
        hits = [{'text': pages[page-1],
                 'citation': f'ZR {", ".join(sections)}: Split 1, PDF page {page}',
                 'scope': 'community facility applicability' if page == 564 else 'residential bulk'}
                for page, sections in selected.items()]
        return hits[offset:offset+limit] if paginate else hits
    expression = ' OR '.join('"' + word + '"' for word in tokens)
    sections = [word for word in tokens if re.fullmatch(r'\d{2,3}-\d{2,4}', word)]
    districts = [word for word in tokens if re.fullmatch(r'[RCM]\d[A-Z0-9-]*', word, re.I)]
    if sections:
        expression = ' OR '.join('"' + word + '"' for word in sections)
    elif districts:
        district_expression = '(' + ' OR '.join('"' + word + '"' for word in districts) + ')'
        terms = [word for word in tokens if word not in districts and word.lower() not in ('and', 'or', 'the', 'for', 'in', 'of', 'far')]
        expression = district_expression
        if terms:
            expression += ' AND (' + ' OR '.join('"' + word + '"' for word in terms) + ')'
    db = sqlite3.connect(f'file:{DATABASE}?mode=ro', uri=True)
    try:
        rows = db.execute('SELECT text,part,page,global_page FROM excerpts WHERE excerpts MATCH ? ORDER BY bm25(excerpts), rowid LIMIT ? OFFSET ?', (expression, limit, offset)).fetchall()
    finally:
        db.close()
    hits = [{'text': text, 'citation': f'Split {part}, PDF page {page}, combined page {global_page}'}
            for text, part, page, global_page in rows]
    # Merged table cells can scramble row/value associations in PDF text.
    # Supply the visually verified rows whenever a low-density FAR query is made.
    if offset == 0 and re.search(r'\b(?:FAR|floor|R[1-5][A-Z0-9-]*|23-21|23-71[12])\b', str(query), re.I):
        tables = far_tables()
        hits.insert(0, {'text': json.dumps(tables), 'reference_context':True,
                        'citation': 'ZR 23-21: Split 1, PDF pages 436–437; ZR 23-711: pages 541–542; ZR 23-712: page 542'})
    return hits


if __name__ == '__main__':
    build_index()
    print(json.dumps(metadata()))
