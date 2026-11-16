"use client";
import {useState,type FormEvent} from "react";
import {useRouter} from "next/navigation";
import {AppShell} from "@/components/layout/AppShell";
import {useBridge} from "@/components/BridgeProvider";
import {apiRequest,errorMessage} from "@/lib/api";
export default function WelcomePage(){
  const router=useRouter();const {refreshSession}=useBridge();const [primer,setPrimer]=useState("");const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{await apiRequest("/onboarding",{method:"POST",body:JSON.stringify({primer})});await refreshSession();router.replace("/home");}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
  return <AppShell><div className="page-content integration-welcome"><p className="eyebrow">Welcome to Bridge</p><h1>A space in your own words.</h1><p>Bridge supports expression and personal reflection. It does not diagnose, provide treatment, or replace professional care.</p><div className="settings-card"><h2>Your choices come first</h2><p>Saved writing is private to your account. AI memory and analysis permissions start off. You can change them in Settings and remove saved entries in History or Passport.</p><p>In this development version you can save conversations, captures, reflections, and passport items. Optional Gemini replies require explicit sharing in Conversation. Manual analysis in Reflect uses only messages saved with memory and context permission.</p><form className="integration-form" onSubmit={submit}><label>Anything you would like to remember about how you prefer support? (optional)<textarea value={primer} onChange={e=>setPrimer(e.target.value)} maxLength={500} rows={4} placeholder="For example: Give me time to explain before offering suggestions."/></label><p>If entered, this will be saved as an item you wrote in your Passport, with AI-use permissions off.</p>{error&&<p className="form-error" role="alert">{error}</p>}<button className="primary-button" disabled={busy}>{busy?"Saving…":"Continue to my space"}</button></form></div></div></AppShell>;
}
