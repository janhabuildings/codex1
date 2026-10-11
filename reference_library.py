"""Unified browsing of supplied zoning text and archived DOB references."""
from itertools import zip_longest
from functools import lru_cache
import bulletin_embeddings
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


@lru_cache(maxsize=32)
def hybrid_bulletins(query):
    semantic=bulletin_embeddings.search(query,limit=40)
    lexical=dob_references.search(query,'buildings-bulletins',limit=40)
    scores={};records={};methods={}
    for method,hits in [('keyword',lexical),('meaning',semantic)]:
        seen=set()
        for rank,hit in enumerate(hits,1):
            identity=(hit['filename'],hit['citation'].split('PDF page')[-1].strip())
            if identity in seen:continue
            seen.add(identity)
            scores[identity]=scores.get(identity,0)+1/(60+rank)
            records.setdefault(identity,hit);methods.setdefault(identity,set()).add(method)
    return [dict(records[key],match_method=' + '.join(sorted(methods[key])))
            for key in sorted(scores,key=lambda key:scores[key],reverse=True)]


def search_page(query, collection='all', page=0, mode='keyword'):
    if collection not in ('all','zoning-resolution','tppn','buildings-bulletins'):
        raise ValueError('Unknown reference collection.')
    if type(page) is not int or not 0 <= page <= 100000:
        raise ValueError('Invalid result page.')
    if mode not in ('keyword','hybrid') or len(query)>300:
        raise ValueError('Invalid search mode or query.')
    groups=[];has_more=False;offset=page*4;notice=''
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
            if kind=='buildings-bulletins' and mode=='hybrid' and query.strip():
                try:
                    hits=hybrid_bulletins(query)[offset:offset+5]
                    notice='Bulletins combine up to 40 keyword and 40 meaning matches. Zoning and TPPNs use keywords.'
                except Exception:
                    hits=dob_references.search(query,kind,limit=5,offset=offset)
                    notice='Meaning search unavailable; showing keyword results. Check the embedding index and OpenAI API access.'
            else:hits=dob_references.search(query,kind,limit=5,offset=offset)
            has_more |= len(hits)>4
            groups.append(hits[:4])
    return {'excerpts':[hit for row in zip_longest(*groups) for hit in row if hit is not None],
            'page':page,'has_more':has_more,'next_page':page+1 if has_more else None,
            'notice':notice,
            'coverage':'Matching excerpts, not exhaustive compliance findings. OCR, diagrams and current applicability require verification.'}
