# Deploy Project Bridge

The current app has two services: a Next.js frontend and a FastAPI backend. Deploy the frontend on Vercel and the backend on an always-running Python web service. Use managed PostgreSQL for saved accounts and writing. The backend's scheduler checks reminders and Reflection Previews every 30 seconds while its process is running; a sleeping or request-only backend will not deliver these on time.

These instructions use Render as an example backend host. Do not commit `.env`, `.env.local`, database files, API keys, SMTP passwords, or `node_modules`. The repository's `.gitignore` excludes local copies.

## 1. Create the database and backend

1. Create a managed PostgreSQL database. If using Render, place the database and web service in the same region and use its **internal** connection details for the web service. A free Render PostgreSQL database expires after 30 days, so use durable storage before storing real user data.
2. Create a Render **Web Service** from this repository with Root Directory `backend`, Language `Python`, Build Command `pip install -r requirements.txt`, and Start Command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Select compute that stays running if scheduled reminders/previews must work.
3. Set these backend environment variables in the host dashboard. Use new, private random values for secrets:

   | Variable | Value |
   | --- | --- |
   | `DB_DRIVER` | `postgresql+asyncpg` |
   | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Individual **internal** PostgreSQL connection fields; do not paste a whole URL into one field |
   | `JWT_SECRET_KEY` | New random secret of at least 32 characters |
   | `COOKIE_SECURE` | `true` |
   | `ALLOWED_ORIGINS` | JSON array containing the exact frontend origin, e.g. `["https://your-site.vercel.app"]` |
   | `PUBLIC_URL` | The exact frontend origin, e.g. `https://your-site.vercel.app` |
   | `LLM_PROVIDER` | `gemini` |
   | `GEMINI_API_KEY` | Gemini key, on the backend only |

4. Run `alembic upgrade head` **from the `backend` directory with those database variables set** before accepting users. A paid Render web service can use this as a Pre-Deploy Command. Do not run migrations concurrently from multiple instances. Check `https://your-backend-host/api/v1/health/db` after deployment.

Local SQLite accounts and writing are **not** copied into the new database by Alembic. If those records must be retained, export and migrate them separately before opening the deployed app.

## 2. Deploy the frontend on Vercel

1. Import the same GitHub repository into Vercel. Set Framework Preset `Next.js` and Root Directory `frontend`. Keep the default install/build commands; the root-level `npm run setup` is for local development only.
2. Set these Vercel environment variables for Production:

   | Variable | Value |
   | --- | --- |
   | `BACKEND_URL` | Backend HTTPS origin, without trailing slash, e.g. `https://your-backend.onrender.com` |
   | `NEXTAUTH_URL` | Exact Vercel site origin, e.g. `https://your-site.vercel.app` |
   | `NEXTAUTH_SECRET` | New random secret of at least 32 characters |

3. Deploy. The existing Next.js rewrite forwards browser `/api/v1/*` requests to the backend. Next.js server routes also use `BACKEND_URL` for Google account exchange. Set `NEXTAUTH_URL`, `PUBLIC_URL`, and `ALLOWED_ORIGINS` to the final stable domain, then redeploy after changing any environment variable. A custom domain is preferable before configuring production OAuth.

## 3. Enable Google sign-in

1. In Google Cloud's Google Auth platform, configure the app's audience and create a **Web application** OAuth client. For a regular public app, choose External. Use only the basic identity scopes needed for sign-in.
2. Add `https://your-site.vercel.app` as an authorized JavaScript origin and `https://your-site.vercel.app/api/auth/callback/google` as an authorized redirect URI. The URI must match exactly. Add localhost equivalents only to a development OAuth client if needed.
3. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in Vercel. Set the **same** `GOOGLE_CLIENT_ID` in the backend host; the backend does not need the client secret. Redeploy both services.
4. Password accounts are not automatically linked to Google accounts with the same email. Use password sign-in for an existing password account.

## 4. Enable verification and password-recovery mail

The reset form asks for the **Bridge account email**. The sending mailbox is configured separately on the backend. Local `MAIL_MODE=file` writes links to `backend/.tmp/mail-outbox`, which is not suitable for hosted deployments.

For Gmail SMTP, change any mailbox password previously shared outside the Google account, enable 2-Step Verification, and create a **Google App Password**. Put only that App Password in the backend host's `SMTP_PASSWORD` variable. Set:

```text
MAIL_MODE=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_STARTTLS=true
SMTP_USERNAME=<sending Gmail address>
SMTP_PASSWORD=<Google App Password>
SMTP_FROM=<sending Gmail address>
```

Keep these values out of GitHub and Vercel's frontend environment. `PUBLIC_URL` must point to the deployed frontend so email links open the right site. After changing host environment variables, redeploy the backend.

## 5. Release checks

When the team is ready to test: check database health, email signup/verification, password reset, Google sign-in, a saved conversation, Gemini response, and a scheduled reminder/reflection. Do not invite people to write sensitive real-life material until the prototype's AI data handling, safety behavior, and privacy language have been reviewed.

Free Render web services sleep when idle; background scheduling pauses during sleep. Free Render PostgreSQL databases expire after 30 days. Choose a persistent service and database before relying on reminders or saved user data.
