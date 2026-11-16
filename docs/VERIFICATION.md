# Verification record

## Gemini migration — 27 October 2026

- Gemini generateContent replaces xAI; default gemini-3.5-flash-lite, GEMINI_API_KEY in the backend only. Existing writing, citations and consent workflows are preserved.
- **35 isolated backend tests passed**, including Gemini request/header/JSON format, exclusion of thought parts, strict output validation, blocked/truncated responses, quota/access/model errors and secret redaction. No paid retry, tools or fallback is enabled.
- Frontend lint and TypeScript checks passed. UI changes are provider labels and free-tier data-use notices; prior layout checks remain historical.
- No live Gemini request was made because no Gemini key was supplied. Free quota and regional/model access must be checked with the owner’s key. Real sensitive writing should not be submitted to the unpaid service.

## API billing diagnostic fix — 27 October 2026

- A live, non-generation GET to xAI’s models endpoint returned HTTP 403 indicating the configured API team had no credits. No user writing was submitted and no generation request was made.
- Missing-credit responses now produce a specific HTTP 402 message with the team/billing steps, instead of the ambiguous key/model-access message. Raw provider bodies and credentials remain excluded from errors/logs.
- **29 isolated backend tests passed**, including three new mocked credit/quota error cases and secret-redaction assertions. Live inference remains blocked until the owner resolves API billing.

## Grok + design reconciliation — final checks, 27 October 2026

- **26 backend tests passed**, including exact-quote validation, read-only generated reflections, deletion of derived citations/reminders, owner isolation, reminder time/permission validation, password change/revocation, and long tagged Notebook entries.
- **Frontend ESLint, TypeScript and production build passed.** The build includes the new Notebook page. Later small source corrections were lint/type-checked.
- Headless Edge against isolated SQLite/fake Grok passed diary expansion/draft preservation, tagged save without analysis, edit/reload, reflection creation with exact quotes, source-message highlighting, explicit AI sharing, provider-failure recovery without duplicate writing, reminder create/persist/complete, whole-interface scaling, dark preference, and My Space → Security navigation.
- A synthetic due reminder appeared on Home, opened the selected destination and disappeared after completion.
- Responsive verification waited for actual content (not loading placeholders): **32 checks** across Login, Home, History, Notebook, Reflections, Passport, Security and Conversation at **320, 375, 768 and 1366px**. No horizontal page overflow or uncaught page errors. Also checked larger dark settings on mobile, expanded mobile diary, Escape/discard behavior and Continue with Email focus.
- Visually inspected final desktop/mobile screenshots, including login, Home, cited reflections, expanded ruled-paper diary and dark settings. The report figures and ER diagram were visually reviewed before implementation.
- PostgreSQL migration SQL through **d9b41027** generated successfully offline. Live PostgreSQL/Docker upgrade, real Google OAuth and real xAI calls remain untested.
- Mocked functional success does not establish clinical safety, factual accuracy of model interpretations, actual phone usability or production readiness.


## AI increment — 27 October 2026

- 21 isolated backend tests passed (10 original plus 11 AI cases), using mocked provider responses and synthetic accounts. Coverage includes explicit consent, old unshared-message exclusion, both mode policies, duplicate/retry handling, safety routing, invalid model output, timeouts, owner checks, permission revocation, evidence thresholds, rejection, memory retrieval and deletion invalidation.
- Frontend lint and production build/TypeScript checks passed.
- Headless Edge against an isolated fake-provider API passed: default-off sharing, a failed reply preserving writing, retry with no duplicate user message, reply persistence after refresh, manual analysis, memory confirmation and pattern rejection.
- Chat and Reflect checked at 320, 375, 768 and 1366 CSS pixels: no horizontal overflow and no uncaught page errors. Mobile screenshots were visually reviewed. A new-conversation URL/refresh issue found during QA was corrected.
- No actual xAI key or paid request was used. Live Grok behavior, account quota/model access, clinical safety, and a real PostgreSQL upgrade remain unverified. The earlier record below describes the persistence-only baseline; its disabled-AI statements are superseded by [AI setup](AI-SETUP.md).


Checked on Windows, 26 October 2026, with Node 24, Python 3.12, Next.js 16.3.7, SQLite and headless Microsoft Edge. Tests used synthetic accounts and a separate QA database; the application database and delivery ZIP contain no QA accounts.

## Passed

- `npm run lint`: frontend ESLint.
- `npm run build`: optimized frontend build, TypeScript validation, and all routes generated.
- `npm ci --dry-run --ignore-scripts --no-audit --no-fund --offline --cache .npm-cache`: repaired lockfile accepted by `npm ci`.
- `npm test`: 10 isolated backend integration tests using a fresh in-memory database per test.
- Combined launcher: API connectivity check, frontend/API on alternate local ports, and shutdown/restart.
- PostgreSQL Alembic **offline SQL generation** from the initial migration through `b7d3e9a21026`.
- Source ZIP integrity and per-file SHA-256 verification during packaging.

### API integration coverage

1. Real password signup/login, incorrect login, authenticated profile, cookie attributes, refresh and logout.
2. Duplicate signup, weak password and invalid username validation.
3. Default/saved preferences, invalid preference payloads, profile edits and idempotent onboarding.
4. Conversation/messages, message pagination, effective memory permissions, history-off rejection, ended-conversation rejection and deletion cascade.
5. Capture/passport/reflection CRUD, real combined history, pagination and escaped search wildcard handling.
6. Cross-account reads/writes/deletes rejected for conversations, messages, captures, passport items, reflections and hypothesis references.
7. Permitted evidence filtering and persisted rejected-pattern correction.
8. Refresh rotation, concurrent-refresh grace handling and stale-token replay revocation.
9. Allowed versus disallowed request origins.
10. Google-to-Bridge session exchange, stable subject identity, existing-email conflict, invalid token and missing configuration. **The identity verifier is stubbed in this test; it is not a live Google OAuth test.**

### Browser coverage

- Email button focuses the login field; unconfigured Google button displays actionable feedback.
- Real signup → onboarding → dashboard; logout → real password login.
- Capture, conversation message, passport item and profile writes; reload confirms stored capture/message/profile data.
- Personal reflection save and reload.
- Explicit Mind Dump link overrides a saved Deep Reflection default.
- Dark mode and larger text persist through settings API updates.
- With history off, temporary writing makes **zero conversation POST requests**; no conversation is created in the database. Ending/restarting temporary writing works, and reload clears temporary content.
- Login at 320, 375, 768 and 1366 CSS-pixel widths.
- Home, History, Passport, Settings, Reflect and Conversation at all four widths: **24 authenticated layout checks with no horizontal document overflow**, plus four login checks. No uncaught browser page errors in this run.
- Focused dashboard tooltip and Quick Capture dialog fit the narrow viewport. Representative screenshots were visually reviewed, including desktop conversation and mobile settings/capture.

A discovered hidden-tooltip overflow at 320 and 768 pixels was corrected and the complete width check rerun. Dark-mode status contrast was also corrected after screenshot review. These checks cover browser viewport layouts, not every physical device or accessibility requirement.

## Not verified / not implemented

- Live Google consent and account chooser: requires the project's OAuth credentials and configured redirect URI.
- Actual PostgreSQL migration/data preservation and Docker Compose startup: neither PostgreSQL nor Docker was installed. Offline SQL generation does not prove a live upgrade.
- Public deployment, HTTPS/proxy configuration, encrypted production storage, rate limiting, recovery email, email ownership verification and account export/deletion.
- AI response quality, safety routing, extraction, evidence thresholds, rejection-aware generation and notification privacy: those services are disabled.
- Full screen-reader/keyboard/modal-focus audit; real mobile keyboards, Safari/iOS, Firefox, 200% zoom, slow-network mutation idempotency, load/concurrency and backup restoration.

## Repeatable manual acceptance checklist

1. From a freshly extracted project run `npm run setup`, `npm test`, `npm run lint`, `npm run build`, and `npm run dev`.
2. Create two different accounts. Save data with the first; verify the second sees an empty workspace and cannot fetch the first account's UUIDs using the API.
3. Save a capture, conversation, passport item and personal reflection. Reload, sign out/in, and restart the services; confirm they persist.
4. Edit and delete captures/passport/reflections. Delete a conversation and verify its messages are gone. Confirm deletion only after the API succeeds.
5. Turn off memory/context/reflection permissions. Attempt direct API writes with permission flags true; verify the effective stored flags are false.
6. Turn off conversation history. Write temporary messages, inspect the network tab for absence of conversation-save requests, and reload to verify the messages disappear. Existing saved history should remain readable.
7. Try invalid credentials, duplicate signup, missing backend, failed save, ended conversation and invalid item IDs. Verify clear errors, no false success, and preserved unsaved text when a request fails.
8. Test all routes and dialogs at phone/tablet/desktop widths, with keyboard-only navigation, dark mode, large text and reduced motion. Check focus visibility/restoration and mobile keyboard behavior.
9. Configure Google on both services and complete a real login. Verify Bridge `/users/me`, logout, and a same-email password-account conflict. Never use a verifier stub in a running application.
10. Before a shared beta, execute the PostgreSQL upgrade against a backup copy and test concurrent usage, session expiry/replay, backup restoration, consent revocation, deletion propagation and the approved safety scenarios.

## Packaging

Run `backend/.venv/Scripts/python.exe scripts/package.py` from the project root on Windows (use `.venv/bin/python` on Unix). It creates `Project-Bridge-Integrated.zip` and a checksum file in the parent directory. A manifest inside the ZIP records each included file's SHA-256. Actual environment files, databases, dependencies, builds and caches are excluded. Setup generates new environment files/secrets for the recipient.
