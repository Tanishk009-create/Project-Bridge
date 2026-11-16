"use client";
import {useEffect,useRef,useState,type FormEvent,type KeyboardEvent} from "react";
import {useRouter,useSearchParams} from "next/navigation";
import Link from "next/link";
import {ArrowUp,Clock3,MessageSquareText,Sparkles} from "lucide-react";
import {AppShell} from "@/components/layout/AppShell";
import {useBridge} from "@/components/BridgeProvider";
import {Toggle} from "@/components/ui/Toggle";
import {PhotoPicker} from "@/components/ui/PhotoPicker";
import {apiRequest,apiDate,errorMessage} from "@/lib/api";
import {useResource} from "@/lib/use-resource";
import type {Conversation,Message,Preferences} from "@/types/api";
export function ConversationScreen(){
  const params=useSearchParams();const id=params.get("id");const {preferences}=useBridge();
  const [created,setCreated]=useState<Conversation>();const local=!!id&&id===created?.id;
  const thread=useResource<Conversation>(id&&!local?`/conversations/${id}`:null);
  function rememberCreated(conversation:Conversation){setCreated(conversation);window.history.replaceState(null,"",`/conversation?id=${conversation.id}`);}
  return <AppShell>{thread.error?<div className="page-content"><p role="alert" className="form-error">{thread.error}</p><Link href="/history">Return to history</Link></div>:id&&!local&&!thread.data?<p className="page-content" role="status">Loading conversation…</p>:preferences&&<ConversationWorkspace key={local?"new":id||"new"} initial={local?undefined:thread.data} preferences={preferences} requestedMode={params.get("mode")} onCreated={rememberCreated} focusMessage={params.get("message")}/>}</AppShell>;
}
function ConversationWorkspace({initial,preferences,requestedMode,onCreated,focusMessage}:{initial?:Conversation;preferences:Preferences;requestedMode:string|null;onCreated:(conversation:Conversation)=>void;focusMessage:string|null}){
  const router=useRouter();const {savePreferences}=useBridge();const [conversation,setConversation]=useState(initial);
  const ai=useResource<{configured:boolean;provider:string;model:string}>("/ai/status");
  const [replying,setReplying]=useState(false);
  const [mode,setMode]=useState(initial ? (initial.initial_mode==="reflection"?"reflection":"mind-dump") : requestedMode ? (requestedMode==="reflection"?"reflection":"mind-dump") : preferences.default_mode==="reflection"?"reflection":"mind-dump");
  const [memory,setMemory]=useState(preferences.memory_allowed);const [context,setContext]=useState(preferences.save_context_allowed);
  const [messages,setMessages]=useState<Message[]>([]);const [draft,setDraft]=useState("");const [photo,setPhoto]=useState<string|null>(null);const [busy,setBusy]=useState(false);const [replyFailed,setReplyFailed]=useState(false);
  const [loading,setLoading]=useState(!!initial);const [error,setError]=useState("");const [ended,setEnded]=useState(!!initial?.ended_at);
  const [loadVersion,setLoadVersion]=useState(0);const chatRef=useRef<HTMLDivElement>(null);const preferenceWrite=useRef<Promise<unknown>>(Promise.resolve());
  const temporary=!conversation&&!preferences.save_history;
  const readOnly=ended||(!temporary&&!preferences.save_history);
  useEffect(()=>{
    if(!initial)return;
    const controller=new AbortController();
    async function load(){
      try{
        const all:Message[]=[];
        for(let offset=0;;offset+=100){
          const page=await apiRequest<Message[]>(`/conversations/${initial!.id}/messages?offset=${offset}&limit=100`,{signal:controller.signal});
          all.push(...page);if(page.length<100)break;
        }
        if(!controller.signal.aborted){setMessages(all.filter(m=>m.sender!=="assistant"||m.active_mode==="reflection"));if(all.length)setMode(all[all.length-1].active_mode==="reflection"?"reflection":"mind-dump");setError("");}
      }catch(e){if(!controller.signal.aborted)setError(errorMessage(e));}finally{if(!controller.signal.aborted)setLoading(false);}
    }
    void load();return()=>controller.abort();
  },[initial,loadVersion]);
  useEffect(()=>{if(focusMessage){document.getElementById(`message-${focusMessage}`)?.scrollIntoView({block:"center"});}else chatRef.current?.scrollTo({top:chatRef.current.scrollHeight});},[messages,focusMessage]);
  async function getReply(cid:string,message:Message){
    setReplying(true);
    try{
      const result=await apiRequest<{message:Message;safety_routed:boolean}>(`/conversations/${cid}/reply`,{method:"POST",signal:AbortSignal.timeout(190000),body:JSON.stringify({message_id:message.id,consent:true,use_memory:memory&&context})});
      setReplyFailed(false);if(result.message.active_mode==="reflection" || result.safety_routed) setMessages(old=>old.some(m=>m.id===result.message.id)?old:[...old,result.message]);
    }finally{setReplying(false);}
  }
  async function retryReply(message:Message){
    if(!conversation||busy)return;setBusy(true);setError("");
    try{await getReply(conversation.id,message);}
    catch(e){setReplyFailed(true);setError(`Your writing is saved. ${errorMessage(e)}`);}finally{setBusy(false);}
  }
  async function send(event:FormEvent){
    event.preventDefault();const content=draft.trim();if(!content||busy||readOnly||loading)return;
    setBusy(true);setError("");setReplyFailed(false);
    try{
      await preferenceWrite.current;
      if(temporary){setMessages(old=>[...old,{id:crypto.randomUUID(),conversation_id:"temporary",sender:"user",content,photo_data:photo,created_at:new Date().toISOString(),active_mode:mode,memory_allowed:false}]);setDraft("");setPhoto(null);return;}
      let current=conversation;
      if(!current){current=await apiRequest<Conversation>("/conversations",{method:"POST",body:JSON.stringify({initial_mode:mode})});setConversation(current);onCreated(current);}
      const saved=await apiRequest<Message>(`/conversations/${current.id}/messages`,{method:"POST",body:JSON.stringify({content,active_mode:mode,memory_allowed:memory&&context,photo_data:photo})});
      setMessages(old=>[...old,saved]);setDraft("");setPhoto(null);
      try{await getReply(current.id,saved);}catch(e){setReplyFailed(true);setError(`Your writing is saved. ${errorMessage(e)} Use “Request / retry AI reply” below your latest message.`);return;}
    }catch(e){setError(errorMessage(e));}finally{setBusy(false);}
  }
  async function end(){
    if(busy)return;setBusy(true);setError("");
    try{if(conversation)await apiRequest(`/conversations/${conversation.id}/end`,{method:"POST"});setEnded(true);}
    catch(e){setError(errorMessage(e));}finally{setBusy(false);}
  }
  function keyDown(event:KeyboardEvent<HTMLTextAreaElement>){if(event.key==="Enter"&&!event.shiftKey&&!event.nativeEvent.isComposing){event.preventDefault();event.currentTarget.form?.requestSubmit();}}
  return <div className="conversation-page"><section className="conversation-main"><header className="conversation-header"><div><p className="eyebrow">{temporary?"Temporary conversation":"Conversation"}</p><h1>Just say it as it is.</h1><p>{temporary?"These messages stay in this tab and disappear when you leave or refresh.":"Your messages are saved to your account. You can review or delete them in History."}</p></div></header>
    <p className="integration-notice">{mode==="mind-dump"?"Mind Dump saves your words for later analysis when you allow memory and context. Bridge only interrupts for urgent safety concerns.":"Deep Reflection is a back-and-forth conversation with Bridge."} {ai.data?.configured?"Messages in saved conversations are sent to Gemini when you press Send.":"Gemini is not configured. Add GEMINI_API_KEY to backend/.env and restart."} Gemini free-tier data may be used to improve Google products; use fictional, non-sensitive text while testing.</p>
    {error&&<p className="form-error" role="alert">{error}{initial&&<button className="text-link" onClick={()=>setLoadVersion(v=>v+1)}>Reload messages</button>}</p>}
    <div className="chat-panel"><div className="messages chat-surface" ref={chatRef} aria-live="polite">{loading?<p role="status">Loading messages…</p>:!messages.length?<div className="chat-empty-state"><Sparkles/><p>Start whenever you want.</p><span>This space is yours.</span></div>:messages.map(message=><div key={message.id} id={`message-${message.id}`} data-cited={message.id===focusMessage||undefined} className={`message message--${message.sender==="user"?"user":"bridge"}`}><div className="message-stack"><div className="message-bubble">{message.sender!=="user"&&<small>Bridge · AI response</small>}<p>{message.content}</p>{message.photo_data&&<img className="message-photo" src={message.photo_data} alt="Photo attached to message"/>}</div>{message.sender==="user"&&message.id===messages.filter(m=>m.sender==="user").at(-1)?.id&&!readOnly&&!temporary&&replyFailed&&<button className="text-link ai-retry" disabled={busy} onClick={()=>void retryReply(message)}>Request / retry AI reply</button>}<time className="message-timestamp">{apiDate(message.created_at).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"})}</time></div></div>)}</div>
    {readOnly?<div className="integration-notice"><strong>{ended?"Conversation ended.":"History is off; new messages cannot be stored in this conversation."}</strong><p><button type="button" className="text-link" onClick={()=>{setEnded(false);setMessages([]);setDraft("");setConversation(undefined);router.push("/conversation");}}>Start a new conversation</button> · <Link href="/history" className="text-link">View history</Link></p></div>:<form className="composer" onSubmit={send}><PhotoPicker photo={photo} onChange={setPhoto} disabled={busy}/><textarea value={draft} onChange={e=>setDraft(e.target.value)} onKeyDown={keyDown} placeholder="Type whatever is on your mind…" aria-label="Message" rows={2} maxLength={20000}/><button className="send-button" aria-label="Send message to Bridge" disabled={busy||loading||!draft.trim()}><ArrowUp/></button><div className="composer-meta"><span>{replying?"Bridge is thinking…":busy?"Saving…":temporary?"Only in this tab":"Saved to your private history"}</span><span>Enter to send · Shift + Enter for new line</span></div></form>}</div></section>
    <aside className="conversation-controls"><h2>Conversation controls</h2><label className="control-row"><span>Current mode</span><select aria-label="Conversation mode" value={mode} onChange={e=>setMode(e.target.value)} disabled={busy||ended}><option value="mind-dump">Mind Dump</option><option value="reflection">Deep Reflection</option></select></label><fieldset className="integration-fieldset" disabled={temporary||readOnly}><div className="control-row"><div><span>Use reviewed memory</span><strong>{memory&&!temporary?"Allowed":"Not allowed"}</strong></div><Toggle checked={memory&&!temporary} onChange={v=>{setMemory(v);if(v&&!preferences.memory_allowed)preferenceWrite.current=preferenceWrite.current.catch(()=>{}).then(()=>savePreferences({memory_allowed:true})).catch(e=>{setError(errorMessage(e));setMemory(false);});}} label="Allow memory for new messages"/></div></fieldset><fieldset className="integration-fieldset" disabled={temporary||readOnly}><div className="control-row"><div><span>Allow context extraction</span><strong>{context&&!temporary?"Allowed":"Not allowed"}</strong></div><Toggle checked={context&&!temporary} onChange={v=>{setContext(v);if(v&&!preferences.save_context_allowed)preferenceWrite.current=preferenceWrite.current.catch(()=>{}).then(()=>savePreferences({save_context_allowed:true})).catch(e=>{setError(errorMessage(e));setContext(false);});}} label="Allow context extraction for new messages"/></div></fieldset><Link href="/profile" className="secondary-button conversation-settings-link">Manage settings</Link><div className="conversation-info"><h3>Conversation info</h3>{conversation&&<Link className="text-link" href={`/reflection?conversation=${conversation.id}`}>Create a cited reflection →</Link>}<p><Clock3/>Started <strong>{conversation?apiDate(conversation.started_at).toLocaleDateString():"This session"}</strong></p><p><MessageSquareText/>Messages <strong>{messages.length}</strong></p></div><button className="danger-button" disabled={busy||ended||loading} onClick={end}>{ended?"Conversation ended":"End conversation"}</button></aside></div>;
}

