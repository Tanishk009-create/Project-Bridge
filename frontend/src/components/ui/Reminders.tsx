"use client";
import Link from "next/link";
import {useEffect,useState,type FormEvent} from "react";
import {useSearchParams} from "next/navigation";
import {Bell,Check,Trash2} from "lucide-react";
import {useBridge} from "@/components/BridgeProvider";
import {useResource} from "@/lib/use-resource";
import {apiRequest,apiDate,errorMessage} from "@/lib/api";
import {Toggle} from "@/components/ui/Toggle";
import type {Reminder,PreviewSchedule} from "@/types/api";

export function ReminderSettings(){
 const {preferences,user,savePreferences}=useBridge();const params=useSearchParams();const reflectionId=params.get("reflection");
 const reminders=useResource<Reminder[]>("/reminders");const preview=useResource<PreviewSchedule>("/reflection-preview/schedule");
 const capabilities=useResource<{mail_delivery_mode:"file"|"smtp"|"disabled"}>("/capabilities");
 const [when,setWhen]=useState("");const [destination,setDestination]=useState("reflection");const [cadence,setCadence]=useState<7|14|30>(7);
 const [error,setError]=useState("");const [busy,setBusy]=useState(false);const [notice,setNotice]=useState("");
 useEffect(()=>{if(preview.data)setCadence(preview.data.cadence_days);},[preview.data]);
 async function enable(value:boolean,email=false){setBusy(true);setError("");try{await savePreferences(email?{notification_email_enabled:value,notification_enabled:value||!!preferences?.notification_enabled}:{notification_enabled:value,notification_email_enabled:value?!!preferences?.notification_email_enabled:false});setNotice("Notification preferences saved.");}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
 async function create(e:FormEvent){e.preventDefault();if(!when||busy)return;setBusy(true);setError("");try{await apiRequest("/reminders",{method:"POST",body:JSON.stringify({scheduled_at:new Date(when).toISOString(),destination,reflection_id:destination==="reflection"?reflectionId:null})});setNotice("Reminder saved. Bridge will check it in the background at the selected time.");setWhen("");reminders.reload();}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
 async function update(id:string,action:"done"|"delete"|"retry"){setBusy(true);setError("");try{await apiRequest("/reminders/"+id+(action==="retry"?"/retry-delivery":""),action==="delete"?{method:"DELETE"}:action==="retry"?{method:"POST"}:{method:"PATCH",body:JSON.stringify({status:"completed"})});reminders.reload();}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
 async function savePreview(enabled:boolean,days:7|14|30){setBusy(true);setError("");try{await apiRequest("/reflection-preview/schedule",{method:"PUT",body:JSON.stringify({enabled,cadence_days:days})});preview.reload();setNotice(enabled?"Reflection Preview scheduled. New eligible writing will be considered at the next check.":"Scheduled Reflection Preview paused.");}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
 const canPreview=!!(preferences?.save_history&&preferences.memory_allowed&&preferences.save_context_allowed&&preferences.reflection_allowed);
 const mailMode=capabilities.data?.mail_delivery_mode;
 return <>
  <div className="settings-section-title"><Bell/><div><h2>Reminders & previews</h2><p>Choose when Bridge checks in, and how you hear about it.</p></div></div>
  <div className="setting-row"><div><strong>In-app reminders</strong><span>Show due reminders on Home when you open Bridge.</span></div><Toggle checked={!!preferences?.notification_enabled} onChange={v=>void enable(v)} label="Enable in-app reminders"/></div>
  <div className="setting-row"><div><strong>Generic email notifications</strong><span>Send only a neutral reminder or “reflection ready” link, with no private writing.</span></div><Toggle checked={!!preferences?.notification_email_enabled} onChange={v=>void enable(v,true)} label="Enable generic email notifications" disabled={busy||mailMode==="disabled"||!user?.email_verified_at}/></div>
  <p className="field-help">{mailMode==="smtp"?"Email delivery is configured through the backend SMTP settings.":mailMode==="file"?"Local development: emails are saved in backend/.tmp/mail-outbox. Configure SMTP for outside-app delivery.":"Email delivery is disabled; configure MAIL_MODE and SMTP in backend/.env."} {!user?.email_verified_at&&"Verify your email before outside-app delivery."} Times use your device’s time zone ({Intl.DateTimeFormat().resolvedOptions().timeZone}).</p>
  <form className="reminder-form" onSubmit={create}><label>Date & time<input type="datetime-local" aria-label="Reminder date and time" value={when} onChange={e=>setWhen(e.target.value)} required/></label><label>Return to<select value={destination} onChange={e=>setDestination(e.target.value)}><option value="reflection">{reflectionId?"This reflection":"Reflections"}</option><option value="notebook">My notebook</option><option value="conversation">A conversation</option></select></label><button className="primary-button" disabled={busy||!when||!preferences?.notification_enabled}>Set reminder</button></form>
  <section className="preview-schedule-card"><h3>Scheduled Reflection Preview</h3><p>With your permission, Bridge periodically creates a cited draft from new eligible conversation writing. Review it before treating any interpretation as meaningful.</p><div className="setting-row"><div><strong>Generate previews automatically</strong><span>Requires History, Memory, Context extraction and Reflection permissions.</span></div><Toggle checked={!!preview.data?.enabled} onChange={v=>void savePreview(v,cadence)} label="Schedule Reflection Previews" disabled={busy||(!canPreview&&!preview.data?.enabled)}/></div><label>Check every <select value={cadence} onChange={e=>{const days=Number(e.target.value) as 7|14|30;setCadence(days);if(preview.data?.enabled)void savePreview(true,days);}}><option value={7}>7 days</option><option value={14}>14 days</option><option value={30}>30 days</option></select></label>{!canPreview&&<p className="field-help">Enable the required controls in <Link href="/profile?tab=data">Data & AI settings</Link> first.</p>}{preview.data?.enabled&&preview.data.next_run_at&&<p className="field-help">Next check: {apiDate(preview.data.next_run_at).toLocaleString()}. Last result: {preview.data.last_status.replaceAll("-"," ")}.</p>}{preview.data?.last_reflection_id&&<Link className="text-link" href={"/reflection?id="+preview.data.last_reflection_id}>Review latest preview →</Link>}</section>
  {notice&&<p role="status" className="integration-success">{notice}</p>}{(error||reminders.error||preview.error)&&<p role="alert" className="form-error">{error||reminders.error||preview.error}</p>}
  <div className="reminder-list">{reminders.loading?<p>Loading reminders…</p>:reminders.data?.length?reminders.data.map(r=><article key={r.id}><Bell size={16}/><div><strong>{r.title}</strong><p>{apiDate(r.scheduled_at).toLocaleString()} · {r.destination}</p><small>{r.status==="completed"?"Completed":preferences?.notification_enabled?"Scheduled in Bridge":"Paused in Settings"}{preferences?.notification_email_enabled?" · Email: "+r.delivery_status.replaceAll("-"," "):""}</small></div>{r.delivery_status==="failed"&&<button className="text-link" disabled={busy} onClick={()=>void update(r.id,"retry")}>Retry email</button>}{r.status!=="completed"&&<button className="icon-button" aria-label="Mark reminder done" disabled={busy} onClick={()=>void update(r.id,"done")}><Check/></button>}<button className="icon-button" aria-label="Delete reminder" disabled={busy} onClick={()=>void update(r.id,"delete")}><Trash2/></button></article>):<p className="compact-empty">No reminders set. Pick a time above.</p>}</div>
 </>;
}

export function DueReminders(){
 const {preferences}=useBridge();const reminders=useResource<Reminder[]>("/reminders");const [now,setNow]=useState(()=>Date.now());
 const reload=reminders.reload;
 useEffect(()=>{const tick=setInterval(()=>{setNow(Date.now());reload();},60000);return()=>clearInterval(tick);},[reload]);
 const due=reminders.data?.filter(r=>r.status==="scheduled"&&apiDate(r.scheduled_at).getTime()<=now)||[];
 if(!preferences?.notification_enabled||!due.length)return null;
 return <section className="due-reminder" role="status"><Bell size={18}/><div><strong>A moment for your Bridge space</strong><p>{due.length} reminder{due.length===1?" is":"s are"} ready when you are.</p></div><Link className="secondary-button" href={"/"+due[0].destination+(due[0].reflection_id?"?id="+due[0].reflection_id:"")}>Open</Link><Link className="text-link" href="/profile?tab=reminders">Manage</Link></section>;
}
