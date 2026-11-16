# Tester handoff — Project Bridge, Gemini + UI update

Date: 16 November 2026. Scope: Windows local development, FastAPI/SQLite and Next.js. AI and email tests use synthetic writing and mocked providers; they do not measure real Gemini or SMTP delivery quality.

## Report-ready summary bullets

- Reviewed the supplied requirements/design report and ER relationships; aligned the application with the purple/white visual identity, compact dashboard, neutral conversation canvas, cited reflection layout and history list.
- Reworked Quick Capture into an expandable diary/notepad. Entries persist as Notebook pages, with Thought, Idea, Moment or Note tags, editing, deletion and a 20,000-character limit.
- Corrected “Save without analysis” copy and kept it enabled by default. Saving a notebook page does not contact AI.
- Reduced excess spacing and standardized typography. Compact, Standard and Larger settings scale controls and spacing along with text.
- Added a My Space three-dot menu and categorized profile, appearance, data/AI, reminder and security settings.
- Added opt-in reminders with date/time, destination, completion and deletion. Reminders display in the application; external/background delivery remains pending.
- Separated sidebar Reflections from conversational mode. Generated reflections contain exact source quotations, explanations and links to highlighted original messages.
- Integrated Google Gemini through the backend, with server-only credentials, provider-error handling and retry without duplicating the saved message. Saved conversation messages are sent to AI by default; history-off temporary messages stay in the browser.
- Added one optional resized photo to notebook pages and conversation messages. Mind Dump processes safety quietly; Deep Reflection shows a contextual response. The backend limits photos to 750 KB and accepts JPEG, PNG or WebP data.
- Added a live camera preview for Take a snap; Upload a photo remains the file picker. Moved Open full notebook into the Quick Capture window.
- Added one-time email verification and password reset links, background generic-email reminders, and opt-in scheduled Reflection Previews with cited evidence. Local development writes messages to a file outbox; SMTP needs provider credentials.
- Enlarged login and legal text, centered History's empty state, anchored Home chip explanations under each chip, aligned Passport privacy heading, removed the inert Reflections stepper, and standardized Manage settings links.
- Added permitted-memory review, manual pattern extraction and evidence/feedback controls. Interpretations remain tentative; exact quote matching does not establish that every interpretation is correct.
- Added password-change and renewable-session revocation controls. Existing access tokens on other devices expire within 15 minutes.

## Functional test cases

| ID | Steps | Expected result |
|---|---|---|
| AUTH-01 | Sign up, log in with email/password, reload, log out | Protected account pages; persistence; session cleared on logout |
| AUTH-02 | Continue with Email; Continue with Google without credentials | Email form receives focus; Google gives setup guidance, not false success |
| AUTH-03 | Security: wrong current password, weak new password, valid change | Errors for invalid inputs; valid change signs out; old password fails and new password works |
| AUTH-04 | Sign out all; attempt refresh with old token | Renewable sessions rejected; current browser signed out |
| AUTH-05 | Sign up with file mail mode; open verification link; log in | Login is blocked before verification, then succeeds; link cannot be reused |
| AUTH-06 | Forgot password; open reset link; set a strong new password | Old password fails, new password works; reset link cannot be reused |
| NOTE-01 | Enter multiline capture, pick Moment, expand/minimize | Same draft/tag remain, ruled-paper editor expands |
| NOTE-02 | Save with Save without analysis on; open Notebook, edit, reload | Content/tag persisted, analysis_allowed=false; edit retained |
| NOTE-03 | Search/filter notebook; New page; delete selected entry | Matching pages only; new clean draft; confirmed deletion reflected in list/history |
| UI-01 | Open Home, History, Notebook, Reflections, Passport, Settings, Conversation at 320/375/768/1366px | No horizontal page overflow; controls remain reachable |
| UI-02 | My Space (…) → Settings → Compact/Standard/Larger | Text, controls and spacing scale together; preference survives reload |
| UI-03 | Toggle dark appearance and reduced motion | Appropriate surfaces/text; reduced transitions |
| AI-01 | Send in Mind Dump, then in Deep Reflection | Mind Dump saves and normally stays quiet; Deep Reflection gives a contextual response. Both submit saved writing to Gemini. |
| AI-05 | Attach a photo to a conversation and to a notebook page, reload both | Photos persist; conversation photo is sent as an image part to Gemini, notebook photo remains in Bridge. |
| AI-02 | Simulate provider timeout; retry latest saved message | Writing stays saved; retry does not duplicate it |
| AI-03 | Enable global and per-message memory/context, create eligible writing | Only permitted sources enter manually requested analysis |
| AI-04 | Try missing consent, invalid source ID or fabricated quotation | Request/output rejected; no invalid reflection stored |
| REF-01 | Reflections → choose conversation → consent → Create reflection | Tentative interpretation, exact excerpts and explanations, no general chat composer |
| REF-02 | Open this message from evidence | Original conversation loads and cited message is highlighted |
| REF-03 | Edit generated reflection via API; delete source conversation | Generated reflection read-only; source deletion removes derived reflection and linked reminder |
| REF-04 | Review a possible connection; correct/reject; inspect context memory | Feedback persisted; source-backed context can be confirmed/edited/rejected/deleted |
| REM-01 | Enable reminders, choose future local date/time and destination, reload | Reminder persisted; timezone conversion correct; done/delete work |
| REM-02 | Try disabled reminders, past time or timezone-less API timestamp | Invalid request rejected |
| REM-03 | Open Home with a due reminder; open its destination | Due banner and correct link; completed reminders excluded |
| REM-04 | Enable generic email, set due reminder, keep browser closed | Background worker sends only a neutral message; status records sent/local-file/failed and retry works |
| PREVIEW-01 | Enable History/Memory/Context/Reflection and 7-day preview; make new eligible writing | Background check creates a cited reflection at the due time; link opens exact source quotes |
| PREVIEW-02 | Disable preview or revoke a required permission before generation finishes | New generated content is discarded or scheduling pauses |
| OWN-01 | Access another account’s reflection/reminder/conversation IDs | 404/empty owner-scoped list; no data leakage |

## Verification record

- Backend automated integration suite: **43 tests passed**, including account links, SMTP transport, generic delivery, scheduled preview, photo persistence, SQLite upgrade and Gemini image-part serialization. Uses isolated databases with foreign keys enabled for API tests.
- Frontend ESLint: no errors (two advisory warnings about preview images). Production webpack build and TypeScript checks: passed.
- PostgreSQL migration chain now reaches `f1a51116`. No live PostgreSQL/Docker migration has been performed. Existing local SQLite databases receive additive account, photo and delivery columns at startup.
- Earlier browser flows passed with fake Gemini; 32 loaded-screen viewport checks passed at 320/375/768/1366px before this page-by-page update. Repeat the visual checks on a real device for this revision. See `VERIFICATION.md`.

## Pending acceptance and limitations

- Real Gemini key/model access, paid response latency/quotas and output quality need the owner’s live acceptance test. No key was entered or paid model call made during development.
- Real Google OAuth needs configured client credentials and a live consent-flow test. Email/password tests do not validate Google OAuth.
- Verify Hindi-English input, indirect crisis language, negation, prompt injection, biased/unsupported interpretations and repeated rejected paraphrases with synthetic/consented examples. Functional tests do not establish clinical safety.
- Mobile checks use emulated viewports; actual phone keyboards, screen readers, zoom and touch usability need device testing.
- In-app reminders refresh while Home is open. The backend checks opted-in generic emails and scheduled previews while its process is running. SMTP, actual-device previews, multi-worker scheduling and shutdown/restart timing still need live testing; phone push is not implemented.
- Notebook analysis permission is stored for future use; current extraction uses conversation messages only. Notebook search filters the current page of 50 entries; History searches saved entries.
- Reflection review lists up to 100 items and analysis uses bounded source windows. Large archive pagination, full export/account deletion, MFA and device inventory remain future work.

## Reproduce automated backend checks

From the extracted `bridge-integrated` folder after setup:

```powershell
npm test
npm run lint
npm run build
```

See `AI-SETUP.md` for key placement, permissions and the live Gemini smoke test. Keep test credentials and synthetic writing separate from real user data.
