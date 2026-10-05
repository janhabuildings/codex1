# Zoning mapping worker

The worker maps the supplied resolution into structured **drafts**, one bounded task at a time. The initial queue has 19 residential FAR tasks, including definitions, ordinary FAR tables and predominantly built-up area provisions. It records conditions, exceptions, required evidence, cross-references, exact quotations and split-PDF page citations. This is an initial mapping queue, not a complete residential compliance rule set.

## Local use

```sh
python -m pip install -r requirements-worker.txt
python mapping_worker.py dry-run
python mapping_worker.py init
python mapping_worker.py run --batch-size 2 --max-api-calls 2
python mapping_worker.py status
python mapping_worker.py export --output /tmp/far-drafts.json
```

Set `OPENAI_API_KEY` privately in the environment before `run`. `MAPPING_MODEL` defaults to `gpt-4.1`. Dry runs and queue inspection do not call OpenAI. Local storage defaults to `/tmp/zoning-mapping.sqlite`; set `MAPPING_DB_PATH` to a durable location when progress must survive cleanup or redeployment.

Each default batch processes at most two tasks and makes at most two API calls. Source excerpts are limited to 20,000 characters per task and generated output to 2,500 tokens per call. Oversized tasks require review rather than being truncated. These are workload limits, not a dollar spending cap; instructions and JSON schema also consume input tokens. Recorded usage includes a count of calls whose billed usage could not be recovered.

## Render setup

1. Create a Render PostgreSQL database. Database and scheduled job services may incur hosting charges.
2. Create a **Cron Job** from this repository using the Docker runtime and the repository-root Dockerfile.
3. Set its Docker command to:

   ```sh
   python mapping_worker.py run --batch-size 2 --max-api-calls 2 --max-input-chars 20000 --max-output-tokens 2500
   ```

4. Set the job's `OPENAI_API_KEY` and `MAPPING_DATABASE_URL`. Use the PostgreSQL **internal database URL** when the services are in the same Render region. Optionally set `MAPPING_MODEL`.
5. Set `MAPPING_DATABASE_URL` to the same database URL on the existing web service and redeploy it. Keep its existing username, password and API key settings.
6. Run the job manually once, inspect the drafts, then choose a schedule. For example, `0 13 * * *` runs daily at 13:00 UTC. Each run resumes pending work. When the queue is exhausted, no further OpenAI calls are made.

Open `/mapping` on the app to see protected progress, draft results and recent token usage, or download the saved JSON. The same app login protects this page. Cron jobs should use PostgreSQL: their temporary filesystem does not preserve SQLite progress between executions. No hosted database or scheduled service is created automatically by this code.

## Review and approval

Drafts are never automatically approved or added to the app's active rules. Citation validation checks that quotations occur on the supplied pages; it does not prove that the legal interpretation is correct. A reviewer must verify applicability, paragraph identifiers, exceptions, tables and dependencies against the actual PDF, including diagrams absent from text extraction.

Use the task ID shown by `status` or the dashboard:

```sh
python mapping_worker.py approve --id TASK_ID --reviewer 'Reviewer name'
python mapping_worker.py approve --id TASK_ID --reviewer 'Reviewer name' --mapping-file /tmp/corrected-task.json
python mapping_worker.py retry --id TASK_ID
```

The corrected file must contain the individual mapping object, not the complete exported queue. Approval rejects missing or invalid citations and unresolved open questions. It records reviewer identity and time, but does not activate rules in the review app. Activation remains a separate implementation and review step. Failed tasks require an explicit retry; the worker stops its batch after provider failures rather than repeatedly retrying paid requests.

## Expanding the queue

Edit `mapping/far_queue.json` to add reviewed page ranges and targets. Record unresolved cross-references as additional tasks; the initial worker does not automatically expand every dependency. Use a new task key when changing an existing task's scope. Queue initialization preserves existing work, and a changed resolution file receives a new source hash so old approvals are not reused.

Claims use expiring leases to prevent overlapping runs from processing the same task. Interrupted work becomes available again after ten minutes. Keep credentials in environment settings; exported mapping data contains no API keys or database connection strings.
