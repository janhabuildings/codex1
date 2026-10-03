# NYC Zoning Review

A local web app for uploading architectural PDFs and requesting a preliminary NYC zoning review of use, FAR, height and setbacks.

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

Set `OPENAI_API_KEY` securely in the server process environment, then restart. Do not commit credentials. The app does not load `.env` files automatically. Optional `OPENAI_MODEL` defaults to `gpt-4.1`; the model must support PDF input and the Responses API web search tool. API usage is billed to your account.

Without a key the app validates submissions and returns a preparation checklist, not a drawing analysis. With a key it sends drawings and notes to OpenAI, requests current official sources, and returns a preliminary report. Files are held in memory rather than saved locally; provider retention policies still apply. Responses use `store: false`.

Reports display model-generated Markdown as plain text, including source URLs, and can be downloaded. Source accuracy, drawing interpretation, and zoning conclusions require professional verification. This is not DOB approval, an exhaustive compliance engine, or a substitute for an architect. Image-only drawings, unclear dimensions, amendments and special districts may prevent reliable findings.

## Validate

```sh
python -m unittest discover -s tests -v
```

The tests cover submission validation and honest behavior when no API key is available. Live model analysis needs API access and a real drawing set and is not covered by these tests.
