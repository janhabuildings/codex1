# NYC Zoning Review

A web app for uploading architectural PDFs and requesting a preliminary NYC zoning review of use, FAR, height and setbacks using the supplied resolution library.

## Zoning reference library

The five user-supplied resolution parts are retained as extracted page text in
`references/resolution.json`, with original PDF SHA-256 hashes and part/page order.
The export title is NYC Zoning Resolution, generated September 21, 2026.
Section amendment dates are preserved in the text. This does not establish that
every section became effective on December 5, 2024 or guarantee applicability to
a particular project date. The original PDFs are not included in GitHub.

Run `python resolution.py` before local startup or tests to build the SQLite FTS
index. Docker builds do this automatically. No new Render secrets are needed.
The model can search this local index during a review; web search is disabled.
Reports cite Split number and PDF page, plus the combined page number.
Only relevant text excerpts are sent to OpenAI alongside the uploaded drawing.
Search is lexical and selective, not an exhaustive legal analysis.

Drawing extraction now returns structured evidence including building/lot type,
dwelling count, lot width, exact dimension labels, endpoints, datum, sheet/page
and uncertainty. Roof datum elevations must not be treated as base-plane heights.
Final map lines are preserved as distinct references; their legal role must be
verified. Explicit rear-yard dimensions take precedence over derived arithmetic.
Residential yard searches are routed to Chapter 23 when residential scope is
identified. Selected sections include verified continuation pages so retrieval
does not omit applicability clauses or the following page's table/paragraph.
Guidance distinguishes 23-332(c) from qualifying-site modifications, applies
23-342(a)(2)(i) only to the appropriate narrow attached/semi-detached interior
lots, and distinguishes the qualifying-site height table from basic envelopes.
These controls reduce known interpretation errors but do not guarantee model
extraction accuracy or professional compliance review.

To reduce rate-limit pressure, a separate model call extracts drawing evidence
with sheet references and uncertainty. Subsequent review/search calls use those
notes instead of resending the PDF. Extraction can miss information; the review
must flag uncertain or missing evidence rather than claim visual verification.
Searches combine district and subject, return at most four text chunks plus a
verified table when relevant, and omit duplicate chunks already in the review.
Reference excerpts are capped at 18,000 characters per review; omitted rules
must be reported as unverified. Report output is capped at 3,000 tokens.

Recognized temporary OpenAI 429 rate limits are retried up to twice. Numeric
Retry-After delays up to 60 seconds are honored if the shared 180-second review
deadline permits; otherwise the app returns the error. Without a delay header,
backoff is 20 then 40 seconds. Quota errors and oversized requests are not
retried. Retries do not create additional app-level review attempts. This cannot
guarantee a request fits the provider's account-specific token allowance.

Merged PDF table cells can lose row alignment during text extraction. The
residential FAR table in Section 23-21 (Split 1, pages 436–437) and conditional
Section 23-712 values (page 542) are also retained as visually verified structured
rows in `references/far_tables.json`. R4 standard FAR is 1.00, not 0.75.
The model receives these rows on every review and with relevant searches.
Conditional eligibility and other applicable modifications still require review.

There are 5,306 pages; 408 have fewer than 80 extracted text characters.
Map/diagram content (especially Appendix F) is not visually indexed. Even pages
with text may contain omitted images. The app must flag image-dependent findings
for visual review. No address-to-zoning lookup is implemented; supply known zoning
districts and overlays in project details. Replacing reference documents requires
re-extraction, index rebuild, and deployment.

## Run

Requires Python 3.10+; no package installation is needed.

```sh
cd /workspace/codex1
python server.py
```

Set `APP_PASSWORD` in the server environment to a unique password of at least
16 characters before starting. `APP_USERNAME` defaults to `owner`. The browser
will show a username/password sign-in prompt. All pages, assets and review API
routes require authentication. Without a valid password configuration, access is
locked with HTTP 503, even if an API key is set. Never commit either password or
API key. Browsers remember Basic authentication until the browser session ends;
use a private window on shared devices. Rotate the password to revoke access.

For Render, add `APP_USERNAME` and `APP_PASSWORD` under Environment, save and
redeploy. Use the HTTPS service URL. `/healthz` is the only public route and can
be set as Render's health check path; it exposes no drawings or configuration.

AI review requests are limited to one concurrent review and 10 attempts per
rolling hour per running process. Provider failures count toward this limit.
The counters reset on restart and are not shared across instances; this is not
a durable billing cap. Keep the service at one instance and configure project
usage alerts in OpenAI. There is no per-user account management in this version.

Open the app on port 8000 in your own browser. It binds to loopback by default. `PORT` and `HOST` can override the listener. Use HTTPS for hosted access so browser credentials are encrypted in transit.

## Enable drawing analysis

Set `OPENAI_API_KEY` securely in the server process environment, then restart. Do not commit credentials. The app does not load `.env` files automatically. Optional `OPENAI_MODEL` defaults to `gpt-4.1`; the model must support PDF input and Responses API function tools. API usage is billed to your account. A review can make several model calls to retrieve references.

Without a key the app validates submissions and returns a preparation checklist, not a drawing analysis. With a key it sends drawings, notes and retrieved library excerpts to OpenAI and returns a preliminary report. Files are held in memory rather than saved locally; provider retention policies still apply. Responses use `store: false`.

Reports display model-generated Markdown as plain text, including source URLs, and can be downloaded. Source accuracy, drawing interpretation, and zoning conclusions require professional verification. This is not DOB approval, an exhaustive compliance engine, or a substitute for an architect. Image-only drawings, unclear dimensions, amendments and special districts may prevent reliable findings.

## Validate

```sh
python -m unittest discover -s tests -v
```

The tests cover submission validation and honest behavior when no API key is available. Live model analysis needs API access and a real drawing set and is not covered by these tests.
