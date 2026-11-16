"use client";

import Link from "next/link";
import { ArrowRight, Feather, Inbox, MessageSquareText, Network, Bell, Zap } from "lucide-react";
import { useState } from "react";
import { useBridge } from "@/components/BridgeProvider";
import { useResource } from "@/lib/use-resource";
import { apiDate } from "@/lib/api";
import type { HistoryData, Pattern } from "@/types/api";
import { AppShell } from "@/components/layout/AppShell";
import { DueReminders } from "@/components/ui/Reminders";
import { QuickCaptureModal } from "@/components/ui/QuickCaptureModal";

const chipDescriptions: Record<string, string> = {
  Thoughts: "Everyday thoughts you want to get out of your head and into a private space.",
  Ideas: "Rough possibilities or creative sparks you want to explore without judging them yet.",
  Worries: "Concerns taking up mental space, written down without pressure to solve them immediately.",
  Anything: "Use this when your entry does not need a label. Start wherever you are.",
  "Deeper insights": "Look beneath the immediate thought to understand what may be influencing it.",
  Connections: "Compare moments or conversations to notice themes that may be related.",
  Growth: "Reflect on changes, lessons, and progress you want to recognize over time.",
  Notes: "Save a short piece of information for later without starting a conversation.",
  Links: "Keep a useful URL together with the context you want to remember.",
  Snippets: "Capture a quote, fragment, or small detail before it gets lost.",
  Reminders: "Record something you want to return to later in your Bridge space.",
};

function InfoChip({ label }: { label: keyof typeof chipDescriptions }) {
  const description = chipDescriptions[label];
  return <span className="info-chip" tabIndex={0} data-tooltip={description} aria-label={`${label}: ${description}`}>{label}</span>;
}

export function DashboardScreen() {
  const [captureOpen, setCaptureOpen] = useState(false);
  const {user} = useBridge();
  const displayName = user?.display_name || user?.username || "";
  const activity = useResource<HistoryData>("/history?limit=5");
  const patterns = useResource<Pattern[]>("/patterns");

  return (
    <AppShell>
      <div className="page-content dashboard-page">
        <div className="dashboard-heading">
          <div><p className="eyebrow">Your space</p><h1>What’s taking up space today? <span>{displayName}</span></h1><p className="page-lead">Choose a space to write, reflect, or capture a thought.</p></div>
          <Link href="/profile?tab=reminders" className="secondary-button dashboard-settings-button"><Bell />Reminders</Link>
        </div>

        <DueReminders/>
        <div className="action-grid">
          <article className="action-card mind-dump">
            <div className="card-icon"><MessageSquareText /></div><div className="action-card-copy"><h2>Mind Dump</h2><p>Just get it out. Low interruption, no pressure to analyse.</p></div>
            <Link href="/conversation?mode=mind-dump" className="card-button">Start writing <ArrowRight size={16} /></Link>
            <div className="chips"><InfoChip label="Thoughts" /><InfoChip label="Ideas" /><InfoChip label="Worries" /><InfoChip label="Anything" /></div>
          </article>
          <article className="action-card reflect-card">
            <div className="card-icon"><Feather /></div><div className="action-card-copy"><h2>Reflect</h2><p>Explore your thoughts in a Deep Reflection conversation.</p></div>
            <Link href="/conversation?mode=reflection" className="card-button">Explore a thought <ArrowRight size={16} /></Link>
            <div className="chips"><InfoChip label="Deeper insights" /><InfoChip label="Connections" /><InfoChip label="Growth" /></div>
          </article>
          <article className="action-card capture-card">
            <div className="card-icon"><Zap /></div><div className="action-card-copy"><h2>Quick Capture</h2><p>A thought, idea, moment or note. Keep it in your notebook.</p></div>
            <button type="button" className="card-button" onClick={() => setCaptureOpen(true)}>Capture thought <ArrowRight size={16} /></button>
            <div className="chips"><span>Thought</span><span>Idea</span><span>Moment</span><span>Note</span></div>
          </article>
        </div>

        <div className="dashboard-lower">
          <section className="revisit-card">
            <div className="section-heading"><div><p className="eyebrow">Possible connection</p><h2>Something worth revisiting</h2></div></div>
            {patterns.data?.filter(p=>p.status!=="rejected").length?<div className="connection-preview"><span className="entry-tag">Tentative · yours to review</span><h3>{patterns.data.filter(p=>p.status!=="rejected")[0].statement_text}</h3><p>Based on {patterns.data.filter(p=>p.status!=="rejected")[0].evidence.length} permitted excerpts. See the sources and say what fits.</p><Link className="primary-button" href="/reflection?tab=patterns">Read & reflect <ArrowRight size={15}/></Link></div>:<div className="connection-empty"><span><Network /></span><strong>No possible connections yet</strong><p>Connections appear only after you request analysis of eligible writing.</p><Link className="text-link" href="/reflection">Open reflections →</Link></div>}
          </section>

          <section className="recent-card">
            <div className="section-heading"><h2>Recent activity</h2><Link className="text-link" href="/history">View all →</Link></div>
            {activity.loading ? <p role="status">Loading activity…</p> : activity.error ? <p role="alert">{activity.error}<button className="text-link" onClick={activity.reload}>Try again</button></p> : activity.data?.items.length ? <div className="connected-activity">{activity.data.items.map(item => <Link href={item.href} key={item.id}><span className="activity-icon">{item.type==="quick-capture"?<Zap size={16}/>:item.type==="reflection"?<Feather size={16}/>:<MessageSquareText size={16}/>}</span><div><strong>{item.type==="quick-capture"?item.text.split("\n")[0].slice(0,60):item.title === "mind-dump" ? "Mind Dump" : item.title=== "reflection"?"Deep Reflection":item.title}</strong><p>{item.type==="quick-capture"?`${item.title} · Notebook`:item.text}</p></div><time>{apiDate(item.created_at).toLocaleDateString()}</time></Link>)}<Link className="text-link" href="/history">View all activity →</Link></div> : <div className="recent-empty"><span><Inbox /></span><strong>No recent activity yet</strong><p>Your saved conversations and captures will appear here.</p></div>}
          </section>
        </div>
      </div>
      {captureOpen && <QuickCaptureModal onClose={() => setCaptureOpen(false)} onSaved={activity.reload} />}
    </AppShell>
  );
}
