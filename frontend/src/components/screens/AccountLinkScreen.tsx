"use client";
import Link from "next/link";
import {useEffect,useState,type FormEvent} from "react";
import {BridgeBrand} from "@/components/brand/BridgeBrand";
import {apiRequest,errorMessage} from "@/lib/api";

export function AccountLinkScreen({kind}:{kind:"verify"|"reset"}){
  const [token,setToken]=useState("");
  const [status,setStatus]=useState("");
  const [error,setError]=useState("");
  const [password,setPassword]=useState("");
  const [confirmation,setConfirmation]=useState("");
  const [busy,setBusy]=useState(false);
  useEffect(()=>{
    const value=new URLSearchParams(window.location.search).get("token")||"";
    setToken(value);
    if(!value){setError("This link has no token. Request a new link from the login page.");return;}
    if(kind==="verify"){
      setBusy(true);
      void apiRequest<{message:string}>("/auth/verify-email",{method:"POST",body:JSON.stringify({token:value})})
        .then(result=>setStatus(result.message)).catch(cause=>setError(errorMessage(cause))).finally(()=>setBusy(false));
    }
  },[kind]);
  async function reset(event:FormEvent){event.preventDefault();if(password!==confirmation){setError("The passwords do not match.");return;}setBusy(true);setError("");try{const result=await apiRequest<{message:string}>("/auth/reset-password",{method:"POST",body:JSON.stringify({token,new_password:password})});setStatus(result.message);}catch(cause){setError(errorMessage(cause));}finally{setBusy(false);}}
  return <main className="account-link-page"><section className="account-link-card"><BridgeBrand/><h1>{kind==="verify"?"Verify your email":"Reset your password"}</h1>{busy&&<p role="status">{kind==="verify"?"Verifying your link…":"Updating password…"}</p>}{error&&<p className="form-error" role="alert">{error}</p>}{status&&<p className="integration-success" role="status">{status}</p>}{kind==="reset"&&token&&!status&&<form className="integration-form" onSubmit={reset}><label>New password<input type="password" autoComplete="new-password" minLength={8} value={password} onChange={e=>setPassword(e.target.value)} required/></label><label>Confirm new password<input type="password" autoComplete="new-password" value={confirmation} onChange={e=>setConfirmation(e.target.value)} required/></label><button className="primary-button" disabled={busy}>Update password</button></form>}<Link className="secondary-button" href="/login">Return to login</Link></section></main>;
}
