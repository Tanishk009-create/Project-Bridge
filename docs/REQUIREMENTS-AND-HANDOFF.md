> Current provider update (27 October 2026): Gemini replaces xAI. See AI-SETUP.md for GEMINI_API_KEY, free-tier limits and Google data-use terms. Historical implementation notes below may reference the former provider.

# Requirements baseline and team handoff

> **AI increment, 27 October 2026:** See [AI setup and current requirement mapping](AI-SETUP.md). The tables below preserve the original integration baseline; AI statuses there are superseded by that mapping. Conversation modes, consent-aware retrieval, typed extraction, evidence-linked patterns, memory review and prototype safety routing now have implementations. They still require live model and stakeholder evaluation.

Source: the supplied 75-page **Group 1 (3).pdf**, copied unchanged to [sources](sources/Group%201%20(3).pdf). Page references below refer to PDF page numbers. Requirements are product input; recommendations, future plans, and estimates in that document are not evidence that a feature is implemented.

## Product baseline

Phase 1 supports emotional articulation and personal reflection, with Mind Dump, Deep Reflection, Quick Capture, optional remembered context, correctable tentative patterns, an Emotional Passport, and user control over saved data. Diagnosis, treatment, automatic therapist sharing, clinical reports, therapist matching, and claims of replacing professional care are outside scope (pp. 3–6). Interviews and professional validation are planned work, not completed evidence (pp. 23–24).

The delivered integration completes a usable account/persistence increment. The AI behavior increment remains open. A silent writing interface does not satisfy the requested AI listening or reflection behavior merely because it avoids generating a harmful answer.

## Functional traceability

Statuses: **Implemented** means the described starter capability exists; **Partial** identifies the missing part; **Pending** means no active implementation. See [Verification](VERIFICATION.md) for test evidence and limits.

| ID | Requirement (pp. 5–6) | Status and location | Next work |
|---|---|---|---|
| FR-01 | Onboarding, AI role/limits, context primer | **Implemented:** `/welcome`, `POST /onboarding`; optional primer creates a user-authored passport item | Validate wording with prospective users; capture default-mode preference in onboarding if needed |
| FR-02 | Select/switch Mind Dump and Deep Reflection | **Implemented:** conversation selector, per-message active mode, saved initial mode | Mode-specific AI behavior belongs to FR-03/04 |
| FR-03 | Low-interruption AI listening | **Pending:** writing/persistence works; no AI reply | Design prompt policy and evaluate curated listening cases |
| FR-04 | Contextual, non-diagnostic deep reflection | **Pending:** mode UI exists; no model invocation | Relevant permitted retrieval, follow-ups, alternatives, output validation |
| FR-05 | Privacy-controlled context | **Partial:** API enforces effective message/capture flags; history-off mode stays in tab | Retrieval-time permissions, consent history, distinct processing/memory flags |
| FR-06 | Emotional Context Graph extraction | **Pending:** original graph models/repositories retained | Structured extraction, source attribution, correction and deletion propagation |
| FR-07 | Separate observation, interpretation, emotion, hypothesis | **Partial:** original entity model separates graph and hypothesis; no validated extraction | Define typed extraction schema and provenance rules |
| FR-08 | Evidence threshold or explicit analysis request | **Pending:** no generator; threshold not implemented | Specify threshold, contradictions, repeat-evidence rules and tests |
| FR-09 | Tentative, evidence-linked hypotheses | **Partial:** review cards label tentative status and link permitted owned messages | Enforce evidence eligibility before surfacing and handle orphaned evidence |
| FR-10 | Yes/Partly/No/Not sure and correction | **Implemented for stored hypotheses:** Reflect cards and pattern PATCH | Add generation workflow and usability testing |
| FR-11 | Remember rejection; do not reassert as fact | **Partial:** rejection and correction persist | Make retrieval/generation honor rejection across future conversations |
| FR-12 | Quick Capture without conversation | **Implemented for text:** create/edit/delete, category, no-analysis choice | Voice input is optional future scope |
| FR-13 | Optional Reflection Preview | **Implemented as opt-in cadence:** backend checks for new eligible conversation writing and saves cited preview | Validate model quality and scheduling on deployed infrastructure |
| FR-14 | Editable Emotional Passport | **Partial:** user-authored entries and permissions work | Add confirmed patterns/goals/unresolved questions, provenance and approval states |
| FR-15 | Chronological history | **Implemented:** real conversation/capture/reflection history, counts and pagination | Topic/calendar views and full-message/semantic search later |
| FR-16 | Inspect, edit, delete stored memories/entries | **Partial:** captures/passport/reflections editable; conversations readable/deletable | Individual message edit/deletion, graph memory inspector, derived-data invalidation |
| FR-17 | Generic privacy-safe notifications | **Implemented for email:** opt-in, generic templates, background due checks, delivery status and retry; local file outbox or configured SMTP | Validate SMTP delivery and device previews; phone push remains pending |
| FR-18 | High-risk routing | **Pending:** product boundary notices exist; no classifier/router | Define reviewed policy and scenario suite before enabling AI |
| FR-19 | Light/dark customization | **Implemented:** saved appearance, text size and reduced motion | Full contrast, keyboard and assistive-technology audit; additional themes optional |
| FR-20 | Provider-neutral model gateway | **Pending:** frontend calls only Bridge API; no external LLM code | Add an interchangeable backend gateway after privacy/safety prerequisites |

## Acceptance and non-functional requirements

| Requirement group | Current evidence | Remaining gate |
|---|---|---|
| AC-01 / NFR-03: modes and discoverability | Three home actions and persistent conversation mode fields | Observe users switching modes without confusion |
| AC-02/03/04/05/07: model behavior and evidence | Only stored pattern review exists | Curated evaluations for low interruption, reflection, evidence, uncertainty and rejection |
| AC-06 / NFR-05: corrections | API test persists rejected status/correction | Graph correction and generation consumption |
| AC-08 / NFR-01: memory control | Owner-scoped CRUD, permission AND checks, no model data transfer | Inspectable extracted memory, full deletion propagation, consent audit |
| AC-09: notification privacy | Delivery absent | Verify templates and device-level previews once implemented |
| AC-10/11 / NFR-06: boundaries and safety | UI communicates role and missing AI | Safety routing, professional review and model behavior tests |
| AC-12: training consent | No training/export pipeline or LLM transmission exists | Separate explicit consent if such use is ever introduced |
| AC-13/14 / NFR-11: usability/accessibility | Responsive screens and appearance controls | Real-device keyboards, screen readers, modal focus, contrast, 200% zoom |
| AC-15 / NFR-07/08/14: beta reliability | Integration tests and browser persistence checks | PostgreSQL upgrade, concurrent-user/load tests, retries/idempotency, backup/restore |
| NFR-02: security | Password hashing, HttpOnly sessions, refresh rotation, ownership, origin validation | HTTPS, encryption at rest, rate limits, email ownership/reset, security review |
| NFR-09/10: maintainability/portability | Separate UI/API/data layers; typed request schemas | Configurable model, safety and evidence policies; provider substitution test |
| NFR-12/13: cultural fit/ethical design | No fabricated clinical claims or engagement score | Indian code-mixed evaluation, neutral wording, dependency-risk review with stakeholders |

Do not mark the complete SRS or planned 15–20 person sensitive-data beta accepted based only on the current passing tests.

## Reconciliation of supplied artifacts

1. **Identity:** the UI previously navigated after password entry without backend authentication. It now creates/logs in real accounts. Google now exchanges identity for the same Bridge session; missing credentials have clear UI feedback.
2. **Persistence:** local-only UI data was replaced with backend calls for supported features. Existing browser mock/localStorage records are not automatically imported into accounts; the identity/ownership of those records is unknown. The only remaining optional localStorage item is the remembered login identifier, not a password or content store.
3. **Missing domain APIs:** captures, passport items, personal reflections, combined history, onboarding, pattern review, and new preferences were added. Original graph/hypothesis/notification models remain for later increments.
4. **Schema difference:** the original reflection required a hypothesis. Personal reflection now permits a null hypothesis reference. Existing hypothesis-linked records remain valid.
5. **Privacy defaults:** new accounts opt out of AI memory/context/reflections. Existing PostgreSQL preferences are preserved rather than silently reset. New permission columns default conservatively.
6. **Design fidelity:** existing branding/assets, navigation, colors, and cards are retained. Fixed viewport sizing was relaxed and grids/form widths adapted. Mock counts, evidence claims, success messages and unavailable services were replaced with real data or explicit availability states.
7. **Technology:** Tailwind, Radix, React Hook Form, TanStack Query, Zustand, Framer Motion and pgvector are recommendations in the design report, not requirements to add every dependency now. Current CSS, React state, typed API client and SQLAlchemy keep the starter close to both archives. Revisit those choices when their complexity is justified.
8. **Session choice:** the PDF flow describes Remember Me changing session duration. The current backend has a fixed refresh lifetime; the UI honestly labels its checkbox **Remember username**. Variable session duration is a future product decision.
9. **Current scope:** Reflect supports personal writing and stored-pattern review. The home Reflection action starts a conversation in reflection mode; generated reflection behavior remains unavailable.

## Source-document issues to resolve

- **Page 15:** 99 of 125 respondents are labelled 84.8% students; the arithmetic is 79.2%. 106 of 125 (the age figure) is 84.8%. Verify the source response sheet before editing the report.
- **Pages 20–24:** pattern/privacy denominators are inconsistent (122/125 in earlier descriptions versus 114/116 in the limitations). Recalculate from the survey workbook; it was not supplied.
- **Pages 53 and 56–63:** the methodology says to count user-recognizable processes once, but later tables count fields, buttons, navigation links and repeated logical data separately. External providers are also counted as EIFs without an established external logical file. Rebuild the estimate from an agreed application-wide process/data inventory; do not treat slide totals as a validated project size.
- **Page 54:** “three conversation modes” conflicts with the two-mode SRS. Quick Capture is a separate action, not a third conversational mode.
- **Pages 64–75:** supplied flow-graph complexity is a design estimate. Recompute against actual implemented control flow and planned paths; it is not measured code coverage.
- Screens use both “Patterns” and “Reflect/Reflection”; decide the final navigation taxonomy in the next design review. Current navigation uses Reflect with pattern review in the same screen.

The source PDF remains unchanged. These are review notes for the responsible authors, not rewritten research results.

## Work by role

### Requirement analyst

Own this traceability table and decision log. Confirm the two-mode vocabulary; define history versus memory versus current-message processing, consent revocation/deletion effects, evidence thresholds, and notification triggers. Reconcile survey/estimation discrepancies using original data. Schedule the planned interviews and professional review with explicit participant agreement; record findings and update acceptance criteria. Deliver an approved next-increment backlog and testable policy examples.

### Designer

Start from the connected screens and PDF pages 41–49. Validate signup, unavailable Google, long errors, onboarding, empty/loading/error states, temporary writing, delete confirmation, mobile navigation, and permission explanations. Resolve Patterns/Reflect naming. Design future evidence/provenance, correction and memory-inspection flows before coding the AI. Include keyboard focus order, dialog focus restoration/trapping, screen-reader labels, touch target sizes, dark-mode contrast and 200% zoom. Deliver flows for default, loading, empty, success, and failure states at 320/375/768/1366+ CSS pixels.

### Frontend developer

Use `BridgeProvider`, `apiRequest`, `useResource`, and the API types. Keep secrets and model calls server-side. Do not reinstate mocked storage/success paths. Extend the common dialog/accessibility pattern, preserve drafts through errors, add mutation idempotency/duplicate-send handling with the backend, and implement the approved evidence/memory screens. Use real backend responses for user-visible confirmations.

### Backend developer

Begin with PostgreSQL migration execution and schema/data regression tests. Maintain owner scoping in every lookup. Add explicit consent/processing semantics, account lifecycle/rate limiting, migration discipline and backup/restore. Implement the model gateway, safety policy, context extraction, evidence rules, rejection-aware generation and deletion invalidation in that order. Validate structured model output before persistence/display; never trust generated IDs or claims as authorization.

### Tester / reviewer

Run `npm test`, `npm run lint`, `npm run build`, then follow the manual checklist in Verification. Add tests tied to acceptance criteria as features arrive. Separate functional success, usability evidence, security assurance and model/safety evaluation. Track regressions by requirement ID, device, steps, expected/actual outcome, and reproducible test data without including private user text.

## Suggested next increments

1. **Close the persistence baseline:** PostgreSQL/Docker execution, production session settings, accessible dialogs, destructive-action/draft UX, account lifecycle and backup checks.
2. **Specify and enforce AI permissions/safety:** distinct consent flags, safety routing, structured output validation, provider-neutral gateway; no public AI yet.
3. **Deliver mode-aware conversation:** evaluated listening/reflection behavior, relevant permitted retrieval, failures/timeouts/cost limits.
4. **Deliver correctable memory and patterns:** graph extraction, provenance, evidence threshold, contradictions, rejection handling, user inspection/deletion and derived-data invalidation.
5. **Add opt-in Reflection Preview/notifications:** generic external content, scheduling, dismissal, delivery failure and revocation tests.
6. **Validate beta readiness:** stakeholder/user review, real-device accessibility, concurrency/load, security and recovery checks; then approve the planned beta scope.
