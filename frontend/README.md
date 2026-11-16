# Bridge frontend

This is the connected Next.js frontend. It requires the FastAPI service; password entry no longer bypasses authentication.

Use the [root quick start](../README.md) to set up and run both services. See [Architecture](../docs/ARCHITECTURE.md) for the API/session contract and [Requirements and handoff](../docs/REQUIREMENTS-AND-HANDOFF.md) for implemented versus pending features.

## Commands from this folder

```powershell
npm ci
npm run dev
npm run lint
npm run build
```

The separate API must be running for `npm run dev`. Prefer the root `npm run dev` for combined startup and port configuration.

Browser requests use same-origin `/api/v1`, proxied to the server-only `BACKEND_URL`. Google setup uses `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `NEXTAUTH_SECRET`, and `NEXTAUTH_URL`; the backend must also have the matching Google client ID. See the root guide for redirect URIs. Never put secrets in `NEXT_PUBLIC_*` variables.

Key routes: `/login`, `/welcome`, `/home`, `/conversation`, `/history`, `/passport`, `/reflection`, `/profile`. AI generation, automatic extraction, notifications, uploads, and email recovery are explicitly unavailable. Terms/privacy pages remain prototype drafts and require product/legal review before publication.
