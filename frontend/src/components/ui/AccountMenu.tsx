"use client";
import Link from "next/link";
import {useEffect,useRef,useState} from "react";
import {Ellipsis,UserRound,Settings2,ShieldCheck,Bell,LogOut} from "lucide-react";
import {useRouter} from "next/navigation";
import {signOut} from "next-auth/react";
import {useBridge} from "@/components/BridgeProvider";
import {apiRequest,errorMessage} from "@/lib/api";

export function AccountMenu({compact=false}:{compact?:boolean}){
 const {user,refreshSession}=useBridge();const router=useRouter();const [open,setOpen]=useState(false);const [error,setError]=useState("");const [busy,setBusy]=useState(false);
 const wrap=useRef<HTMLDivElement>(null);const trigger=useRef<HTMLButtonElement>(null);
 useEffect(()=>{if(!open)return;function outside(e:PointerEvent){if(!wrap.current?.contains(e.target as Node))setOpen(false);}function key(e:KeyboardEvent){if(e.key==="Escape"){setOpen(false);trigger.current?.focus();}}document.addEventListener("pointerdown",outside);document.addEventListener("keydown",key);return()=>{document.removeEventListener("pointerdown",outside);document.removeEventListener("keydown",key);};},[open]);
 async function logout(){setBusy(true);try{await apiRequest("/auth/logout",{method:"POST"});await signOut({redirect:false});await refreshSession();router.replace("/login");}catch(e){setError(errorMessage(e));setBusy(false);}}
 return <div className={`account-menu ${compact?"account-menu--compact":""}`} ref={wrap}><button ref={trigger} type="button" className="account-trigger" aria-label="My Space options" aria-expanded={open} onClick={()=>setOpen(!open)}><span className="account-avatar">{(user?.display_name||user?.username||"B").slice(0,1).toUpperCase()}</span>{!compact&&<span className="account-label"><strong>{user?.display_name||user?.username}</strong><small>My space</small></span>}<Ellipsis size={18}/></button>{open&&<nav className="account-popover" aria-label="Account options"><div><strong>{user?.display_name||user?.username}</strong><small>{user?.email}</small></div>{[["profile","Profile",UserRound],["appearance","Settings",Settings2],["reminders","Reminders",Bell],["security","Security",ShieldCheck]].map(([id,label,Icon])=>{const Glyph=Icon as typeof UserRound;return <Link key={String(id)} href={`/profile?tab=${id}`} onClick={()=>setOpen(false)}><Glyph size={16}/>{String(label)}</Link>;})}<button disabled={busy} onClick={()=>void logout()}><LogOut size={16}/>{busy?"Signing out…":"Sign out"}</button>{error&&<p role="alert">{error}</p>}</nav>}</div>;
}
