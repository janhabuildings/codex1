# Personal OneDrive connection

This connection uses Microsoft's authorization code flow with PKCE and browser-bound, single-use state. You sign in on Microsoft, never supply a Microsoft password to this app. Access and refresh tokens are encrypted in PostgreSQL. This is a single-owner connection protected by the app's existing login.

## 1. Register a Microsoft application

Open https://entra.microsoft.com/ and find **App registrations → New registration**. If your personal account has no directory for app registration, create an Azure account/directory or register through a directory you administer first. This is separate from having a OneDrive subscription.

- Name: `NYC DOB Reference Worker`.
- Supported account types: **Personal Microsoft accounts only**, or **Accounts in any organizational directory and personal Microsoft accounts**. The integration uses the `consumers` endpoint for personal accounts.
- Redirect URI platform: **Web**.
- Redirect URI: `https://codex1-2hat.onrender.com/onedrive/callback`.
- Save the **Application (client) ID**.
- Under **Certificates & secrets**, create a client secret and securely copy its **Value**, not its secret ID. Set an expiry reminder.
- Under **API permissions**, add Microsoft Graph **delegated** `Files.ReadWrite.AppFolder`. The sign-in request also asks for `offline_access` so scheduled jobs can refresh the connection.

Do not configure application permissions, public-client implicit flow or broad `Files.ReadWrite.All` permissions. Consent is granted by the personal account owner during sign-in.

## 2. Configure Render

A persistent database is required. Use the same PostgreSQL database as the mapping worker or another dedicated database; set `MAPPING_DATABASE_URL` on the website and the future document worker.

Set these variables privately in the existing Render web service:

| Variable | Value |
| --- | --- |
| `ONEDRIVE_CLIENT_ID` | Application (client) ID |
| `ONEDRIVE_CLIENT_SECRET` | Client secret Value |
| `ONEDRIVE_REDIRECT_URI` | `https://codex1-2hat.onrender.com/onedrive/callback` |
| `ONEDRIVE_TOKEN_KEY` | A generated Fernet key |
| `MAPPING_DATABASE_URL` | PostgreSQL internal connection URL |

Generate the encryption key on your own computer or in a private Render shell after dependencies are installed:

```sh
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

Copy it directly into the Render environment setting. Keep a private backup. Never commit the key or paste it, the client secret, database URL or Microsoft password into chat. Keep the encryption key unchanged across deployments and use the same key on the document worker. Replacing it makes saved tokens unreadable until you reconnect. Set the other connection variables on that worker too.

Save and redeploy the website. Existing app username/password and OpenAI settings remain required for their existing functions.

## 3. Connect

Open https://codex1-2hat.onrender.com/onedrive, log in to the review app, click **Connect or reconnect OneDrive**, and complete Microsoft sign-in and consent. The callback must match the registered URI exactly. The page reports whether the encrypted connection was saved; actual uploads also require a working OneDrive account and API access.

The destination is inside the app's limited-access OneDrive folder:

```text
OneDrive / Apps / NYC DOB Reference Worker / NYC DOB References /
  TPPN /
  Buildings Bulletins /
```

Microsoft controls the app folder's display name. This setup deliberately uses the app folder rather than an arbitrary folder in the root of your OneDrive. Subfolders are created on the first upload. Access is limited to the app folder, not the rest of your drive.

## 4. Upload from a worker

The storage helper can upload PDFs, extracted TXT files and JSON metadata (maximum 25 MB per file):

```sh
python onedrive.py status
python onedrive.py upload --file /tmp/tppn-01-2020.pdf --category TPPN
python onedrive.py upload --file /tmp/bulletin-2024-001.txt --category 'Buildings Bulletins'
```

Deterministic filenames replace the existing file of the same name in the same category. Extracted text and source metadata should use matching names with `.txt` and `.json` extensions. The helper does not scrape DOB pages, extract PDF text or run on a schedule yet; it provides the connection and storage layer for that collector. No files are uploaded until an upload command or a future collector calls it.

## Disconnect and recovery

**Disconnect** removes saved tokens and pending sign-ins, leaving uploaded documents untouched. To revoke Microsoft's grant as well, remove the app's consent in your Microsoft account's app permissions. Expired secrets or revoked consent require configuration updates and reconnecting. Refresh-token updates are serialized in the database to avoid overlapping jobs overwriting rotated tokens.

If Microsoft sign-in reports a redirect or account-type error, compare the registration with the settings above. No Microsoft password belongs in Render. Authorization codes and token values are excluded from application access logs and API responses.
