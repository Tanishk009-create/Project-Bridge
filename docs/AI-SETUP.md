# Gemini integration and team handoff

## Enable it locally

Edit **`backend/.env` in the project you run**. For the current extracted copy this is:

`C:\Users\TANISHK TIWARI\Downloads\Project-Bridge-Integrated\bridge-integrated\backend\.env`

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=paste_your_gemini_key_here
LLM_MODEL=gemini-3.5-flash-lite
```

Keep the other values in that file. Do not use `frontend/.env.local`, `NEXT_PUBLIC_*`, or a source-code file for this key. Do not share the key in chat or commit it. The `.env.example` files are templates, not the files the server reads. Docker Compose uses the root `.env` instead.

Stop the running app with Ctrl+C. From the folder containing the root `package.json`:

```powershell
cd 'C:\Users\TANISHK TIWARI\Downloads\Project-Bridge-Integrated\bridge-integrated'
npm run setup
npm run dev
```

Setup preserves existing secrets and database rows. The SQLite upgrade adds missing tables and columns for AI, photos, email links and scheduled delivery without replacing existing writing. PostgreSQL uses `alembic upgrade head` (latest revision `f1a51116`).

Sign in and open Conversation, then send a message. Saved conversation messages, including an optional photo, are sent to Gemini automatically. Mind Dump saves eligible context quietly and only interrupts for urgent safety concerns; Deep Reflection can offer a tentative interpretation and one follow-up question. History-off conversations remain local and have no AI processing.

To try context/pattern extraction, enable History, Memory, Context extraction and Reflection in Settings, then keep both conversation memory/context controls on while saving new messages. In **Reflections → Memory & analysis**, consent to analysis and click **Analyse eligible writing**. Review the context suggestions and their supporting writing. Confirm, edit, reject or delete them. Review patterns with Yes / Partly / No / Not sure and an optional correction.

## Free-tier setup

1. Create a Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey). Use a project on the Free Tier; do not enable billing if you want to remain on free quota.
2. Paste it into **GEMINI_API_KEY** in the backend `.env` shown above. The previous Grok/xAI key is not used by this version. No frontend key or extra SDK installation is needed.
3. Restart `npm run dev` and send a message. Test with fictional, non-sensitive writing.

Default: **gemini-3.5-flash-lite**, currently listed with free input/output on Google's [pricing page](https://ai.google.dev/gemini-api/docs/pricing). Free quota is limited and varies by model, project and region. Check actual limits in AI Studio; no fixed requests/day is promised. The app never enables billing, chooses a fallback model or automatically retries. If your project is already paid, its configured requests may be billed; the API key alone does not reveal the billing tier.

**Privacy:** Google's unpaid-service terms say inputs/outputs can be used to improve products and reviewed by humans, and instruct users not to submit personal, confidential or sensitive information. This matters for Bridge's reflective writing: use fictional data during free-tier testing. Review the [Gemini terms](https://ai.google.dev/gemini-api/terms) before using real user content. Bridge's consent controls do not override Google's terms.

No live Gemini generation was performed during this update. Deep Reflection normally makes two model calls (safety classification, then reply); Mind Dump normally makes one safety call. Extraction and cited reflections use separate model calls. Local urgent-signal handling can avoid a provider call. Safety classification is retained even with free quota.

## Permission contract

| Action | Data that may leave Bridge |
|---|---|
| Send a saved conversation message | Current text and optional photo, plus up to six previously AI-shared turns in this same conversation |
| Retry a failed reply | The latest saved message and eligible prior turns in that conversation |
| Reply with memory enabled | Also up to eight confirmed, relevant context nodes; up to eight Passport items marked for conversations; previous interpretation corrections |
| Explicitly request analysis | Up to 30 recent eligible user messages (2,000 characters each), plus previous pattern reviews/corrections |
| Explicitly request a conversation reflection | Up to 20 eligible messages from the chosen conversation (4,000 characters each) |
| Temporary writing, history off | None; no backend persistence or model requests |

Current-turn sharing and long-term memory are separate: the conversation UI requests AI processing after saving each message. `Message.memory_allowed=false` excludes a message from later cross-conversation retrieval/analysis. Old messages that were never processed by AI are excluded from reply context.

Memory retrieval additionally requires current global memory/context permissions, the current message's stored permission, and `use_memory=true` on the reply request. Analysis requires current history/memory/context/reflection permissions. Turning a global permission off prevents subsequent use without deleting saved entries. A request already sent to Google Gemini cannot be recalled; the backend rechecks controls and discards generated output when relevant controls/context change during the request.

Gemini calls use `generateContent` without tools, explicit caching or paid fallback. Google's data-use terms still apply; this is not a zero-retention promise. Keys are sent only in the backend request header to Google, never in URLs or browser code.

## Implementation mapped to the report

| Report requirement | Implementation / practical limit |
|---|---|
| FR-03 / FR-04 | Distinct listening/reflection prompt policies; non-diagnostic boundary, at most one reflection question. Live model behavior still needs evaluation. |
| FR-05 | Owner-scoped queries, explicit sharing, separate memory eligibility, post-request control rechecks. |
| FR-06 / FR-07 | Validated typed graph nodes, source IDs and relationship edges; observations, interpretations, reported emotions and hypotheses remain distinct. Nodes start unreviewed. |
| FR-08 / FR-09 | Manual analysis; at least three distinct messages across two conversations per pattern, with owned permitted source IDs. Counts alone do not prove a meaningful pattern. |
| FR-10 / FR-11 | Existing feedback UI; corrections enter analysis/retrieval; duplicates and close textual repeats are suppressed. Semantic paraphrase suppression also depends on the model and requires evaluation. |
| FR-14 | Only Passport items explicitly allowed for conversation use can be retrieved. Automatic Passport population and Passport-based pattern generation are not implemented. |
| FR-16 | Context inspector with sources, edits, confirmation, rejection and deletion. Deleting a source conversation invalidates its derived nodes/patterns. Deleting only a node allows later re-extraction from retained writing; reject it to retain the decision. |
| FR-18 | Direct urgent-signal routing plus a model safety classifier before ordinary replies. Failure blocks the ordinary reply. Generic immediate-support response; no diagnosis or invented helpline number. Prototype safeguards require clinical/cultural evaluation. |
| FR-20 | Provider-neutral gateway protocol and an Gemini generateContent adapter. Keys and calls stay on the backend. No vendor SDK in the frontend. |

Manual, cited conversation reflection is now available under **Reflections**. Choose a saved conversation and explicitly consent; every returned quote must exactly match an eligible message or the output is rejected. A link opens and highlights the cited message. At most 20 messages, 4,000 characters each, are submitted. Generated reflections cannot be edited into uncited claims. Deleting a source conversation removes its derived reflection and linked reminder.

User-scheduled reminders are available through **Home → Reminders** or **My Space (…) → Reminders**. Home refreshes due reminders once per minute; the backend also checks due generic email delivery in the background. SMTP requires configuration; local development uses `backend/.tmp/mail-outbox`. **Remind me later** can link to a reflection. Optional scheduled Reflection Preview (FR-13) now checks new eligible conversation writing at a chosen cadence, creates a cited draft and optionally sends a generic “ready” email (FR-17). Phone push remains pending. Quick Captures and personal reflection notes are not sent for AI analysis. Graph edges are persisted; a visual graph editor is not included. Individual message editing, account export/deletion, and production operations remain separate work.

## Reliability and developer details

- `POST /conversations/{id}/messages` saves writing; `POST /conversations/{id}/reply` uses its ID and explicit consent. A failed reply leaves the writing intact. Retry returns an already completed reply without another model call.
- A durable per-message lease prevents duplicate replies across workers. Failed leases can retry; abandoned pending leases expire after three minutes. The service commits the claim before network I/O and the generated reply afterwards. Repository methods do not commit.
- Per-process limits allow one active AI operation per account, four globally, and ten requests per account per minute. Multiple production workers need a shared limiter and analysis job coordination.
- Provider calls have bounded timeouts and output budgets. The UI/rewrite allow up to 190/200 seconds for a safety call followed by generation. No automatic paid retries or model tools/search are enabled.
- Google Gemini JSON output is parsed and validated locally against strict Pydantic schemas. Unknown source IDs, invalid graph indices, incomplete responses and extra fields are rejected. Some diagnostic/dependency language is screened locally; this is not comprehensive semantic safety verification.
- Only confirmed context is retrieved, through bounded lexical matching. This is a simple initial retrieval strategy, not an embedding search system. Analysis examines at most 30 messages and will not scan a whole large archive.
- Error responses omit raw provider bodies and credentials. Credentials use `SecretStr`. No conversation/prompt logging was added.
- New endpoints: `GET /ai/status`, `POST /conversations/{id}/reply`, `POST /ai/analyze`, `GET /ai/memories`, `PATCH/DELETE /ai/memories/{id}`. All require authentication. `/ai/status` checks configuration presence, not provider connectivity.

## Troubleshooting

| Message | Action |
|---|---|
| AI not configured | Set `GEMINI_API_KEY` in the running project's backend `.env`, save, restart both servers and refresh the page. |
| Key/model access rejected | Check GEMINI_API_KEY, project/API restrictions, region and model availability in Google AI Studio. |
| Quota/rate limit reached | Check your free-tier limits in AI Studio; wait for the relevant limit to reset. Zero available quota can mean that the selected model or region is unavailable for your project. |
| Incomplete/invalid output | Retry once; if recurrent, check model structured-output support and increase `LLM_MAX_OUTPUT_TOKENS` up to 8192. |
| Provider timed out | Retry the saved message; optionally increase `LLM_TIMEOUT_SECONDS` from 40 to at most 90. |
| No eligible messages | Enable permissions before saving new messages. Old opt-out messages are not silently made eligible. |
| No new pattern | Add varied eligible writing across conversations. Sparse/repeated evidence may legitimately produce none. |

## Next team checks

Analyst: approve the explicit sharing/memory distinction and configurable evidence threshold. Designer: test consent, evidence/correction and small-screen usability with users. Developer: exercise a real Gemini API key and PostgreSQL upgrade; add shared rate limiting, backup/restore and account lifecycle before deployment. Reviewer: evaluate indirect crisis language, Hindi-English phrasing, negation, diagnosis avoidance, sycophancy, rejection paraphrases and prompt injection using consented/synthetic examples. Passing functional tests does not establish clinical safety or full SRS acceptance.

## UI and tester handoff

See [UI-DESIGN-UPDATE.md](UI-DESIGN-UPDATE.md) for the report figure and ER mapping, and [TESTER-HANDOFF.md](TESTER-HANDOFF.md) for test steps and report-ready findings. Quick Capture now saves to Notebook with a Thought, Idea, Moment or Note tag; expanding it preserves the draft. Settings contains appearance/whole-interface sizing, profile, data controls, reminders and password/session security.
