"use client";
import {useState} from "react";
import Link from "next/link";
import {useBridge} from "@/components/BridgeProvider";
import {useResource} from "@/lib/use-resource";
import {apiRequest,errorMessage} from "@/lib/api";

type Memory={id:string;kind:string;label:string;review_status:string;sources:{id:string;content:string;conversation_id:string}[]};
export function AIMemoryReview({reloadPatterns}:{reloadPatterns:()=>void}){
  const {preferences:p}=useBridge();
  const status=useResource<{configured:boolean;provider:string}>("/ai/status");
  const memories=useResource<Memory[]>("/ai/memories");
  const [consent,setConsent]=useState(false);const [busy,setBusy]=useState(false);const [error,setError]=useState("");const [notice,setNotice]=useState("");
  const allowed=p?.save_history&&p.memory_allowed&&p.save_context_allowed&&p.reflection_allowed;
  async function analyze(){
    if(!consent||busy)return;setBusy(true);setError("");setNotice("");
    try{
      const result=await apiRequest<{nodes_created:number;patterns_created:number;messages_considered:number}>("/ai/analyze",{method:"POST",signal:AbortSignal.timeout(190000),body:JSON.stringify({consent:true})});
      setNotice(`Reviewed ${result.messages_considered} eligible messages. Created ${result.nodes_created} context suggestions and ${result.patterns_created} possible patterns. Insufficient or repeated evidence may produce no new patterns.`);
      memories.reload();reloadPatterns();setConsent(false);
    }catch(e){setError(errorMessage(e));}finally{setBusy(false);}
  }
  return <section className="settings-card integration-section ai-memory"><h2>AI context & pattern review</h2><p>Send up to 30 recent conversation messages that you saved with memory and context permission to {status.data?.provider||"Google Gemini"}. Earlier pattern reviews and corrections are included. Captures and personal reflection notes are excluded.</p><p>Possible patterns need at least 3 messages across 2 conversations. They remain suggestions for you to review.</p>{!allowed&&<p>Enable History, Memory, Context extraction and Reflection in <Link href="/profile" className="text-link">Settings</Link>, then save eligible messages in Conversation.</p>}{!status.data?.configured&&<p>Configure GEMINI_API_KEY in backend/.env and restart to enable analysis.</p>}<p className="field-help">Gemini free tier may use submitted content to improve Google products. Use fictional, non-sensitive text for testing.</p><label className="ai-consent"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)} disabled={busy||!allowed||!status.data?.configured}/>I agree to share this eligible writing with the AI provider for this analysis.</label><button className="primary-button" disabled={!consent||busy||!allowed||!status.data?.configured} onClick={()=>void analyze()}>{busy?"Reviewing eligible writing…":"Analyse eligible writing"}</button>{error&&<p role="alert" className="form-error">{error}</p>}{notice&&<p role="status">{notice}</p>}<h3>Context you can review</h3><p>Only suggestions you confirm can be retrieved for later conversations. Rejecting keeps your decision; deleting removes the suggestion. To prevent extraction again, delete its source conversation in History.</p>{memories.loading?<p>Loading context…</p>:memories.error?<p role="alert">{memories.error}</p>:!memories.data?.length?<p>No context suggestions yet.</p>:memories.data.map(memory=><MemoryCard key={`${memory.id}-${memory.label}-${memory.review_status}`} memory={memory} reload={memories.reload}/>)}</section>;
}
function MemoryCard({memory,reload}:{memory:Memory;reload:()=>void}){
  const [label,setLabel]=useState(memory.label);const [busy,setBusy]=useState(false);const [error,setError]=useState("");
  async function save(review_status:string){setBusy(true);setError("");try{await apiRequest(`/ai/memories/${memory.id}`,{method:"PATCH",body:JSON.stringify({label,review_status})});reload();}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
  async function remove(){setBusy(true);setError("");try{await apiRequest(`/ai/memories/${memory.id}`,{method:"DELETE"});reload();}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
  return <article className="integration-pattern"><p className="eyebrow">{memory.kind.replaceAll("_"," ")} · {memory.review_status}</p><label>Edit context<textarea value={label} onChange={e=>setLabel(e.target.value)} maxLength={255}/></label><details><summary>View supporting writing ({memory.sources.length})</summary>{memory.sources.map(s=><p key={s.id}><Link href={`/conversation?id=${s.conversation_id}`}>{s.content}</Link></p>)}</details><div className="integration-row"><button className="secondary-button" disabled={busy||!label.trim()} onClick={()=>void save("confirmed")}>Confirm / save edit</button><button className="secondary-button" disabled={busy||!label.trim()} onClick={()=>void save("rejected")}>Reject</button><button className="danger-button" disabled={busy} onClick={()=>void remove()}>Delete</button></div>{error&&<p role="alert">{error}</p>}</article>;
}
