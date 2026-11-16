"use client";

import { ChevronDown, CircleHelp, MessageSquareText, Network, ShieldCheck, Sparkles, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { BridgeBrand } from "@/components/brand/BridgeBrand";

export type AppInfoDialogType = "help" | "about";

const faqs = [
  ["How do I start?", "Choose Mind Dump or Reflect to write in a conversation, or Quick Capture to save a short thought. Saved conversation messages go to Gemini when you press Send; Mind Dump stays mostly quiet while Deep Reflection replies."],
  ["What are possible connections?", "In Reflect, request analysis of eligible messages. Suggestions need evidence from at least three messages across two conversations and remain yours to confirm or reject."],
  ["What do Reflections and Passport do?", "Reflections shows tentative interpretations with exact cited messages and lets you review patterns. Passport stores your own communication preferences, helpful context and boundaries, each with separate permissions."],
  ["Quick Capture or Notebook?", "Quick Capture is the small diary window. Notebook is the full-page place to revisit, edit, tag, search and delete the same saved pages."],
  ["Can I control what Bridge uses?", "Yes. Privacy and Passport controls are designed to let you decide what is saved and what may support conversations, patterns, or reflections."],
  ["Is Bridge therapy or a diagnosis?", "No. Bridge supports expression and reflection, but it does not diagnose conditions or replace professional mental-health care."],
  ["Where can I find earlier entries?", "Open History to review or delete conversations, captures, and reflections. Use Reflect to write a personal reflection and Passport to manage personal context."],
];

export function AppInfoDialog({ type, onClose }: { type: AppInfoDialogType; onClose: () => void }) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="modal-backdrop info-modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className={`info-modal info-modal--${type}`} role="dialog" aria-modal="true" aria-labelledby={`${type}-dialog-title`} onMouseDown={(event) => event.stopPropagation()}>
        <button ref={closeButtonRef} type="button" className="modal-close" aria-label={`Close ${type}`} onClick={onClose}><X /></button>

        {type === "help" ? (
          <>
            <header className="info-modal-header">
              <span><CircleHelp /></span>
              <div><p className="eyebrow">Help centre</p><h2 id="help-dialog-title">How can we help?</h2><p>Quick answers about using your Bridge space.</p></div>
            </header>
            <div className="faq-grid">
              {faqs.map(([question, answer]) => (
                <details key={question}>
                  <summary>{question}<ChevronDown /></summary>
                  <p>{answer}</p>
                </details>
              ))}
            </div>
            <div className="support-note"><ShieldCheck /><p><strong>Your safety matters.</strong><span>Bridge is not an emergency service. If you are in immediate danger, contact local emergency services or a trusted person nearby.</span></p></div>
          </>
        ) : (
          <>
            <header className="about-modal-header">
              <BridgeBrand compact />
            </header>
            <div className="about-intro">
              <p className="eyebrow">About the platform</p>
              <h2 id="about-dialog-title">A private space to turn conversations into clarity.</h2>
              <p>Project Bridge is designed to help people express what is on their mind, preserve useful context, and revisit possible patterns at their own pace.</p>
            </div>
            <div className="about-pillars">
              <article><span><MessageSquareText /></span><div><h3>Express freely</h3><p>Use Mind Dump, guided reflection, or quick captures without pressure.</p></div></article>
              <article><span><Network /></span><div><h3>Notice connections</h3><p>Review tentative patterns alongside the conversations that support them.</p></div></article>
              <article><span><ShieldCheck /></span><div><h3>Stay in control</h3><p>Choose what is saved and how your context may be used across Bridge.</p></div></article>
            </div>
            <div className="about-principle"><Sparkles /><p>Bridge supports reflection and organization. It does not diagnose you or replace professional support.</p></div>
            <button type="button" className="primary-button info-modal-done" onClick={onClose}>Continue to my space</button>
          </>
        )}
      </section>
    </div>
  );
}
