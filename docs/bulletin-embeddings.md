# Buildings Bulletin vector embeddings

The initial pilot covers Buildings Bulletins only, including archived attachments: 391 PDF files, 2,192 pages and 3,444 overlapping excerpts in the current corpus. TPPNs and the Zoning Resolution continue to use their existing keyword indexes.

The embedding model is `text-embedding-3-small`, with 1,536 dimensions. Each vector is linked to the excerpt, PDF page, title, original URL, OCR flag and PDF checksum. Compressed batches are committed to `references/bulletin-embeddings/`; the manifest tracks completeness. No Microsoft, Google or additional database service is needed.

## Start in GitHub

1. Open repository **Settings → Secrets and variables → Actions → New repository secret**.
2. Name it `OPENAI_API_KEY`, paste the key privately and save. The Render environment setting does not automatically supply GitHub Actions. Do not send the key in chat or commit it.
3. Open **Actions → Build Buildings Bulletin embeddings → Run workflow → main**.
4. Leave defaults for a full initial build: at most 100 API calls and 8,000,000 input tokens. The workflow first counts tokens without an embedding request, then embeds pending chunks. Running it again resumes saved batches.

The local count was a conservative upper bound of 6,577,911 UTF-8 bytes, because the tokenizer download was blocked in that environment. The workflow uses `cl100k_base` for an exact count when available, otherwise the byte upper bound. At the previously quoted example price of $0.02 per million input tokens, that upper bound corresponds to about $0.14. Confirm current model pricing and account billing; hosting and subsequent query embeddings are separate. Each request's reported usage is saved in `last-run.json`; interrupted calls may have unknown billed usage.

Batches contain at most 64 excerpts. The worker enforces both API-call and input-budget caps, validates all returned vector dimensions and refuses to retry provider failures automatically. It saves every completed batch before continuing. Requests interrupted before a checkpoint can be billed again when retried. If a token cap ends a successful run with `complete: false`, run again to continue. Credentials are never included in vector records, request logs or source metadata.

## Local commands

```sh
python -m pip install -r requirements-embedding.txt
python bulletin_embeddings.py estimate
python bulletin_embeddings.py build --max-api-calls 5 --max-tokens 200000
python bulletin_embeddings.py search --query 'requirements for an accessible entrance'
```

Set `OPENAI_API_KEY` privately for build and search. Estimate does not require a key or make a paid embedding call. Semantic searches embed the question, rank stored vectors by cosine similarity, and return page-cited excerpts. They require a complete index matching the current source version.

This initial step creates the vector index and CLI semantic search. The website continues keyword search; adding a hybrid search mode to the reference page is the next integration step. Similarity does not establish legal applicability, rescission, supersession or complete compliance. OCR and diagrams still need visual verification.

DOB References now offers Keywords + meaning for Buildings Bulletins. It fuses up to 40 matches from each search by reciprocal rank, deduplicates PDF pages, and paginates the combined list. Zoning and TPPNs retain keyword search. A small query embedding uses the Render OPENAI_API_KEY; completed vectors ship in the Docker image. Up to 32 query result sets are cached per server process until eviction or restart. API/index failures fall back to keyword results with a visible notice.
