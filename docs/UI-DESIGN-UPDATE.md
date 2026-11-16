# Design reconciliation — 27 October 2026

## Reference reviewed

The supplied 75-page `docs/sources/Group 1 (3).pdf` was text-extracted, and the ER figure on page 36 plus UI figures on pages 43–49 were rendered and visually reviewed. The report is retained in the package. The following updates reconcile those designs with the working application and the latest requested changes.

| Reference | Working implementation |
|---|---|
| Login, p43 | Purple landscape/brand panel, compact sign-in pane, translucent input surfaces and readable text. Email login and configured Google flow retained. |
| Home, p44 | Narrow navigation, three compact action cards, real possible-connection preview and compact recent activity. My Space avatar/name/ellipsis account menu. |
| Conversation, p45 | Neutral chat canvas, lavender user bubbles, pale mint assistant bubbles, controls beside chat on desktop and stacked on mobile. Collapsible explicit AI-sharing controls. |
| Quick Capture, p46 + latest request | Expandable ruled diary/notepad. Expansion preserves the draft. Thought / Idea / Moment / Note are saved tags. Saves up to 20,000 characters; first line serves as list title. Notebook list, filtering, editing and deletion. Save without analysis defaults on. |
| Passport, p47 | User-authored identity/support entries with per-entry permissions. AI context review is separate and sourced. No invented personal information. |
| Reflection, p48 | Separate review screen: tentative interpretation, exact source quotes, explanation of why each was included, and links to highlighted original messages. Cross-conversation patterns have evidence, feedback, corrections and optional personal reflection. |
| History, p49 | Compact timeline/list switch, real saved records, search and type filter, source/open/edit/delete actions. No synthetic activity charts. |
| Latest account-settings request | Profile; General & appearance; Data & AI controls; Reminders; Security. Real password change and refresh-session revocation, not decorative controls. |

## Size and responsive behavior

Standard uses a 14px root size, Compact 13px, Larger 16px. Spacing and component sizes use rem units so the whole interface scales. Mobile text-entry fields remain at least 16px for readability and to avoid mobile input zoom. Cards, settings panes, notebook and review columns stack at smaller widths; mobile navigation remains available.

## ER relationship mapping

The original User → Conversation → Message, Message → NodeSource → ContextNode, ContextEdge, HypothesisEvidence → Hypothesis → Reflection, and User → Preferences relationships remain. Additions:

- **AITurn** records explicit per-message AI reply consent and retry/lease status.
- **ReflectionSource** joins Reflection to Message and stores the exact quote plus its explanation. This extends the ER model to support the latest direct-conversation citation requirement; it does not claim the report originally included this table.
- **Reminder** belongs to a User and may reference a Reflection. It stores the schedule/destination/status for in-app reminders. The original Notification model remains separate; external delivery is not implemented.
- **Capture** remains the user-authored saved entry, now presented as a Notebook page. It stores its tag and analysis permission. No duplicate notebook copy or automatic AI call is created.

## Intentional limits

The result follows the supplied visual direction, with responsive adaptations and the new diary/settings behavior; it is not a pixel-for-pixel reproduction at every size. Reminder delivery currently requires visiting/opening Bridge. No MFA, email password reset, device inventory, automatic Passport generation, full graph editor or background AI scheduler was added. Existing short-lived access tokens on other devices can remain valid for up to 15 minutes after session revocation.
