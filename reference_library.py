"""Unified browsing of supplied zoning text and archived DOB references."""
from itertools import zip_longest
import dob_references
import resolution


def search(query, collection='all'):
    if collection not in ('all','zoning-resolution','tppn','buildings-bulletins'):
        return []
    groups=[]
    if collection in ('all','zoning-resolution'):
        groups.append([dict(hit,collection='zoning-resolution',filename='Supplied NYC Zoning Resolution',
                            source_url=None,source_note='Supplied zoning text; original PDF is not stored in this repository.')
                       for hit in resolution.search(query)])
    for kind in ('tppn','buildings-bulletins'):
        if collection in ('all',kind):
            groups.append(dob_references.search(query,kind))
    # Interleave collections; their independent rankings are not comparable.
    # Preserve every returned section continuation and verified table.
    return [hit for row in zip_longest(*groups) for hit in row if hit is not None]


def status():
    dob=dob_references.metadata()
    zoning=resolution.metadata()
    return {'documents':len(dob['documents'])+1,
            'pages':sum(d['pages'] for d in dob['documents'])+zoning['pages'],
            'zoning_pages':zoning['pages'],'dob_documents':len(dob['documents']),
            'ocr_pages':sum(len(d.get('ocr_pages',[])) for d in dob['documents']),
            'low_text_pages':sum(len(d['low_text_pages']) for d in dob['documents'])+zoning['low_text_pages'],
            'extraction_errors':dob.get('errors',[]),'ocr_errors':dob.get('ocr_errors',[]),
            'coverage':'Supplied zoning text and archived DOB guidance. Diagrams, OCR and current applicability require verification.'}


def search_page(query, collection='all', page=0):
    if collection not in ('all','zoning-resolution','tppn','buildings-bulletins'):
        raise ValueError('Unknown reference collection.')
    if type(page) is not int or not 0 <= page <= 100000:
        raise ValueError('Invalid result page.')
    groups=[];has_more=False;offset=page*4
    if collection in ('all','zoning-resolution'):
        hits=resolution.search(query,limit=5,offset=offset,paginate=True)
        contexts=[h for h in hits if h.get('reference_context')]
        matches=[h for h in hits if not h.get('reference_context')]
        has_more |= len(matches)>4
        groups.append([dict(hit,collection='zoning-resolution',filename='Supplied NYC Zoning Resolution',
                            source_url=None,source_note='Supplied zoning text; original PDF is not stored in this repository.')
                       for hit in contexts+matches[:4]])
    for kind in ('tppn','buildings-bulletins'):
        if collection in ('all',kind):
            hits=dob_references.search(query,kind,limit=5,offset=offset)
            has_more |= len(hits)>4
            groups.append(hits[:4])
    return {'excerpts':[hit for row in zip_longest(*groups) for hit in row if hit is not None],
            'page':page,'has_more':has_more,'next_page':page+1 if has_more else None,
            'coverage':'Matching excerpts, not exhaustive compliance findings. OCR, diagrams and current applicability require verification.'}
