# Zoning and DOB reference library

The `/references` page offers All collections, Zoning Resolution, TPPNs and Buildings Bulletins filters. Zoning search uses the existing supplied-resolution index and preserves its split/PDF citations, verified FAR tables and section continuation pages. The original zoning PDFs are not stored, so those results show their supplied-text source without inventing a PDF download link. All-collection results interleave independent searches rather than claiming a common relevance score. The Show more results button loads the next four ranked excerpts per selected collection and appends them. Section continuation pages remain accessible across batches, and verified FAR context appears once at the start. Browse pagination does not increase AI review retrieval budgets.

The DOB library stores page-separated text from the archived TPPNs and Buildings Bulletins in `references/dob-text/`. Each JSON record retains its source URL, original filename, PDF checksum and page numbering. The index tracks extraction failures, pages with little text and pages improved by OCR.

Extraction uses local Poppler tools; low-text pages use Tesseract OCR. No OpenAI API calls are used for extraction or indexing. Install Poppler and Tesseract locally (Ubuntu: `sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-eng`), then run from the repository root:

```sh
python scripts/extract_dob.py
python scripts/ocr_dob.py
python dob_references.py
```

The SQLite FTS index is generated locally and during Docker builds rather than committed. Docker includes the extracted text, not the archived PDF binaries. A Render deployment rebuilds the index and provides the protected `/references` search page. Both review and follow-up chat can use `search_dob_references` alongside the supplied Zoning Resolution search. Search is selective and does not prove exhaustive compliance; no-result searches do not prove absence of applicable guidance.

The **Extract and index DOB references** GitHub workflow can be run manually and runs after either archive download workflow. It processes the latest `main`, commits page text and metadata, and provides an artifact containing text and a searchable SQLite database. Extraction/OCR failures are reported separately; a partial library can remain searchable while missing pages require review. Archive download errors also remain in the metadata.

Citations identify the collection, document title/filename, PDF page and official source URL. OCR can misread digits, fractions, diagrams and merged tables. Short or blank pages remain flagged even after OCR. Current status, applicability, supersession and rescission are not inferred from download dates or search ranking. DOB guidance does not replace the Zoning Resolution, and retrieved text is evidence rather than model instructions.
