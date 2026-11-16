# Project Bridge — integrated development starter

This project combines the supplied updated Next.js frontend, FastAPI backend, and the Phase 1 requirements/design report. It provides a working account and persistence foundation for the team to build on.

**Gemini free-tier setup:** [Where to paste your key and how to use AI](docs/AI-SETUP.md)

**UI update and testing:** [Design mapping](docs/UI-DESIGN-UPDATE.md) · [Tester handoff](docs/TESTER-HANDOFF.md)

**Start here:** [Requirements and role handoff](docs/REQUIREMENTS-AND-HANDOFF.md) · [Architecture and API](docs/ARCHITECTURE.md) · [Verification](docs/VERIFICATION.md)

**Deploy:** [Vercel frontend, persistent backend, database, Google sign-in, and email](docs/DEPLOYMENT.md)

**Azure VM alternative:** [Run the full stack on one Ubuntu VM with HTTPS](docs/AZURE-VM-DEPLOYMENT.md)

## Run locally on Windows

Requirements: Node.js 20.9+ (22 LTS recommended), Python 3.11+, and internet access for the first dependency installation. PostgreSQL and Docker are optional for local development.

Open a terminal in this `bridge-integrated` folder:

```powershell
npm run setup
npm run dev
```

Open **http://localhost:3000**. Choose **Sign Up**, create your own account, and complete the welcome screen. There is no default account or shared password.

Setup installs frontend dependencies and an isolated Python environment, creates random local secrets without overwriting existing environment files, and creates a SQLite database at `backend/bridge.db`. Restarting preserves saved data. Stop the app with Ctrl+C. The launcher starts both services and checks database connectivity before starting the website.

If Python is not on PATH:

```powershell
$env:BRIDGE_PYTHON = 'C:\path\to\python.exe'
npm run setup
```

If a port is occupied:

```powershell
$env:WEB_PORT = '3100'
$env:API_PORT = '8100'
npm run dev
```

Use the displayed website URL consistently; `localhost` and `127.0.0.1` have separate browser cookies. The API documentation is at **http://127.0.0.1:8000/docs** with default ports. Backend code changes require restarting `npm run dev`; frontend changes refresh automatically.

## What works

- Email/username signup and password login, HttpOnly session cookies, token refresh, logout, protected screens, and onboarding.
- Google OAuth to the same backend account/session system, once credentials are configured below.
- Saved conversations with mode selection, message retrieval, ending, and deletion.
- Expandable diary-style Quick Capture and saved Notebook pages with Thought / Idea / Moment / Note tags, editing, deletion, history, and one optional photo per page.
- Editable, user-authored Emotional Passport entries with per-item future-use permissions.
- Personal reflections, history search/pagination, and real activity counts.
- My Space account menu, profile, whole-interface scaling, appearance, data controls, password change and session revocation.
- In-app scheduled reminders, optional generic email delivery, and completion/deletion controls.
- Opt-in scheduled Reflection Previews from new eligible conversation writing, with exact source quotes and a review link.
- One-time email verification and password-reset links; local development uses a private outbox folder.
- Conversation reflections with verified exact source quotes and links to the original messages.
- Privacy settings enforced by the API. With conversation history off, new writing stays only in the current browser tab and is lost on navigation/reload.
- Pattern review/corrections and permitted evidence display for hypotheses already present in the backend. No sample hypotheses are fabricated.
- Layouts that scroll and adapt to phone, tablet, and desktop widths.

**AI integration:** saved conversation messages and their optional photos are sent to Gemini on Send. Mind Dump quietly processes a turn and only interrupts for urgent safety concerns; Deep Reflection shows a conversational reply. Historical context remains controlled by memory and context permissions. Manual graph/pattern extraction, evidence review, editable memories, and prototype safety routing remain separate. See [AI setup and limits](docs/AI-SETUP.md).

**Not enabled:** phone push notifications, other attachment types, and production-grade clinical safety validation. Each capture or message supports one resized JPEG photo. Background email delivery requires SMTP configuration and opt-in; local development writes messages to a file outbox instead.

## Email verification, recovery, previews and notifications

Local development defaults to `MAIL_MODE=file`. New password accounts receive a one-time verification link in `backend/.tmp/mail-outbox`; open the latest message there before logging in. **Forgot password?** sends a one-time reset link to the same outbox. Existing accounts are preserved as verified during the additive schema upgrade. Google accounts use Google's verified email claim.

For real email delivery, set these values in `backend/.env` and restart the app: `MAIL_MODE=smtp`, `PUBLIC_URL` (the site URL), `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM`, and `SMTP_STARTTLS`. Use your email provider's SMTP credentials; never put them in frontend files. The templates in `.env.example` contain no credentials. In Docker, set the same variables in the root `.env`.

For a Gmail sending address, enable 2-Step Verification and generate a Google App Password. Put that App Password in `SMTP_PASSWORD`, **never the normal Gmail sign-in password**. Use `SMTP_HOST=smtp.gmail.com`, `SMTP_PORT=587`, `SMTP_STARTTLS=true`, and set `SMTP_USERNAME` and `SMTP_FROM` to the sending address. Switch to `MAIL_MODE=smtp` only after those values are present. The reset form asks for the *Bridge account's* email; the sending address is configured separately. If the reset form says the route is unavailable, restart the backend so its current routes load.

In **Settings → Reminders**, enable in-app reminders and, separately, generic email notifications. Emails contain only a neutral reminder or “reflection ready” link, with no private text. The backend checks due reminders in the background and records delivery status; failed deliveries can be retried from Settings. Scheduled Reflection Preview is another opt-in control there, with 7/14/30-day cadence. It requires History, Memory, Context extraction and Reflection permissions; only new eligible writing is considered. Generated previews appear in Reflections with exact citations. The app checks while the backend is running; it does not wake a shut-down computer.

## Google sign-in setup (optional)

Email/password works without Google credentials. To enable Google:

1. Create a Google OAuth client of type **Web application** in your Google Cloud project. Configure the consent screen and permitted test users if the project is in testing.
2. Register the local origin `http://localhost:3000` and redirect URI `http://localhost:3000/api/auth/callback/google` (use your actual port).
3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `frontend/.env.local`.
4. Set the **same** `GOOGLE_CLIENT_ID` in `backend/.env`. The backend does not need the Google client secret.
5. Set `NEXTAUTH_URL` to your website URL and keep the generated `NEXTAUTH_SECRET`. Restart both services.

The backend verifies Google's signed ID token and its intended client. Existing password accounts are never automatically linked by matching email; sign in with the password in that case. A future account-linking flow requires explicit authenticated approval. Live Google consent/login was not exercised because the supplied files contain no OAuth credentials.

## Commands

| Command from this folder | Purpose |
|---|---|
| `npm run setup` | Install dependencies, generate missing environment files, prepare local database |
| `npm run dev` | Run frontend and API together |
| `npm run lint` | Frontend ESLint checks |
| `npm run build` | Production frontend build including TypeScript validation |
| `npm test` | Isolated backend integration tests; no application data is used |

For separate terminals after setup:

```powershell
# Terminal 1
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2, from bridge-integrated
npm --prefix frontend run dev
```

On macOS/Linux, the Python executable is `backend/.venv/bin/python`; root npm commands are portable. Those platforms have not been exercised here.

## PostgreSQL and Docker

The supplied PostgreSQL architecture and migrations are retained. SQLite is an added local development option. The server applies the additive photo column upgrade to existing local SQLite databases on startup; PostgreSQL deployments must run Alembic. Do not use `alembic stamp` to skip migration checks.

For local PostgreSQL, set `DB_DRIVER=postgresql+asyncpg` and the database fields in `backend/.env`, then run from `backend`:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Existing supplied PostgreSQL databases upgrade from revision `d5150e6c6eb3` through `b7d3e9a21026` to `c8a41027`. Back up existing data first. The integration migration is forward-only; rollback requires restoring the backup. Existing preferences are retained, and new accounts receive the new opt-in defaults.

Alternatively, install Docker Desktop, generate/configure the root `.env` using setup or the template, then run **from this root**:

```powershell
docker compose up --build
```

This starts PostgreSQL, runs migrations, and starts API/web containers. Database state persists in `bridge_pgdata`. The root compose file is authoritative; the backend archive's old database-only compose file is retained only as source reference. Docker/PostgreSQL execution was not available on this machine; generated migration SQL was checked, but container startup and a real PostgreSQL upgrade remain to be tested.

## Folder map

```text
bridge-integrated/
  frontend/       Next.js screens, shared session state, API client, Google OAuth
  backend/        FastAPI routes, schemas, SQLAlchemy models/repositories, Alembic, tests
  scripts/        Setup, combined local launcher, test runner
  docs/           Architecture, requirement mapping, team handoff, verification, source PDF
  docker-compose.yml
  .env.example    Docker configuration template (no real credentials)
```

## Troubleshooting

- **Cannot reach server:** use the root `npm run dev`, check its API errors, and open `/api/v1/health/db` on the API port. An unstarted API no longer results in a pretend login.
- **Google unavailable:** configure both environment files and restart. Until then use Sign Up and password login.
- **Verification or recovery mail missing:** the backend issues one-time links, but delivery depends on SMTP configuration. Check the API logs and the [Azure VM mail troubleshooting steps](docs/AZURE-VM-DEPLOYMENT.md#if-verification-or-recovery-mail-does-not-arrive); local file mode writes links to `backend/.tmp/mail-outbox`.
- **Port in use:** stop the old server or choose `WEB_PORT`/`API_PORT` as above.
- **Dependency install fails:** check Node/Python versions and network/proxy access; use the checked-in frontend lockfile with `npm ci`.
- **Existing local SQLite schema differs:** preserve its database file and migrate/export it deliberately. Setup will not erase it or rewrite existing tables.

The deliverable ZIP excludes local secrets, credentials, databases, test accounts, dependencies, caches, and build output. The supplied source archives and the earlier frontend workspace remain separate from this integrated project.
