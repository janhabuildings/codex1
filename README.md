# NYC Zoning Review

A local web app for uploading architectural PDFs and requesting a preliminary NYC zoning review of use, FAR, height and setbacks.

## Run

Requires Python 3.10+; no package installation is needed.

```sh
cd /workspace/codex1
python server.py
```

Open the app on port 8000 in your own browser. It binds to loopback by default. `PORT` and `HOST` can override the listener. This prototype has no authentication: keep it local rather than exposing it publicly.

## Enable drawing analysis

Set `OPENAI_API_KEY` securely in the server process environment, then restart. Do not commit credentials. The app does not load `.env` files automatically. Optional `OPENAI_MODEL` defaults to `gpt-4.1`; the model must support PDF input and the Responses API web search tool. API usage is billed to your account.

Without a key the app validates submissions and returns a preparation checklist, not a drawing analysis. With a key it sends drawings and notes to OpenAI, requests current official sources, and returns a preliminary report. Files are held in memory rather than saved locally; provider retention policies still apply. Responses use `store: false`.

Reports display model-generated Markdown as plain text, including source URLs, and can be downloaded. Source accuracy, drawing interpretation, and zoning conclusions require professional verification. This is not DOB approval, an exhaustive compliance engine, or a substitute for an architect. Image-only drawings, unclear dimensions, amendments and special districts may prevent reliable findings.

## Validate

```sh
python -m unittest discover -s tests -v
```

The tests cover submission validation and honest behavior when no API key is available. Live model analysis needs API access and a real drawing set and is not covered by these tests.
