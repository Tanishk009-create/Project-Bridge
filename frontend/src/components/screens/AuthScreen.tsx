"use client";

import { useRouter } from "next/navigation";
import { getProviders, signIn } from "next-auth/react";
import { ArrowRight, Eye, EyeOff, FileText, LockKeyhole, Mail, MessageSquareText, Network, ShieldCheck, X } from "lucide-react";
import { FormEvent, useEffect, useRef, useState } from "react";
import { ApiError, apiRequest, errorMessage } from "@/lib/api";
import { useBridge } from "@/components/BridgeProvider";
import { BridgeBrand } from "@/components/brand/BridgeBrand";

type AuthTab = "login" | "signup";

export function AuthScreen() {
  const router = useRouter();
  const { refreshSession } = useBridge();
  const [busy, setBusy] = useState(false);
  const emailInputRef = useRef<HTMLInputElement>(null);
  const passwordInputRef = useRef<HTMLInputElement>(null);
  const [tab, setTab] = useState<AuthTab>("login");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [rememberedUsername, setRememberedUsername] = useState("");
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [legalOpen, setLegalOpen] = useState<"terms" | "privacy" | null>(null);
  const [googleAvailable, setGoogleAvailable] = useState(false);
  const [googleSetupOpen, setGoogleSetupOpen] = useState(false);
  const [recoveryOpen, setRecoveryOpen] = useState(false);
  const [notice, setNotice] = useState("");
  const [recoveryEmail, setRecoveryEmail] = useState("");
  const [recoveryNotice, setRecoveryNotice] = useState("");


  useEffect(() => {
    getProviders()
      .then((providers) => setGoogleAvailable(Boolean(providers?.google)))
      .catch(() => setGoogleAvailable(false));

    Promise.resolve().then(() => {
      setRememberedUsername(window.localStorage.getItem("bridge.rememberedUsername") || "");
      const reason = new URLSearchParams(window.location.search).get("error");
      if (reason) setError(reason === "AccountExists" ? "This email already has an account. Use your password to sign in." : "Google sign-in could not be completed. Please try again or use email.");
    });
  }, []);

  function changeTab(nextTab: AuthTab) {
    setTab(nextTab);
    setError("");
    setNotice("");
    setShowPassword(false);
    setShowConfirmation(false);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const data = new FormData(event.currentTarget);
    const name = String(data.get("name") || "").trim();
    const submittedEmail = String(data.get("username") || "").trim();
    const password = String(data.get("password") || "");
    const confirmation = String(data.get("confirmPassword") || "");

    if (tab === "signup" && name.length < 2) {
      setError("Enter your full name to create an account.");
      return;
    }
    if (!submittedEmail) {
      setError("Enter your email address or username.");
      emailInputRef.current?.focus();
      return;
    }
    if (password.length < 8) {
      setError("Your password must contain at least 8 characters.");
      return;
    }
    if (tab === "signup" && password !== confirmation) {
      setError("The passwords do not match. Please enter the same password in both fields.");
      return;
    }

    if (tab === "login") {
      if (rememberMe) {
        window.localStorage.setItem("bridge.rememberedUsername", submittedEmail);
        setRememberedUsername(submittedEmail);
      }
    }

    if (busy) return;
    setBusy(true);
    try {
      if (tab === "signup") {
        const username = String(data.get("newUsername") || "").trim();
        const created = await apiRequest<{verification_required:boolean;delivery:string}>("/auth/signup", {method: "POST", body: JSON.stringify({email: submittedEmail, username, password, display_name: name})});
        if(created.verification_required){setTab("login");setNotice(created.delivery==="local-file"?"Account created. Open the verification link in backend/.tmp/mail-outbox, then log in.":created.delivery==="sent"?"Account created. Check your email for the verification link before logging in.":"Account created, but email delivery failed. Configure mail delivery and request a new verification link.");return;}
      }
      const identifier = submittedEmail.includes("@") ? {email: submittedEmail} : {username: submittedEmail};
      await apiRequest("/auth/login", {method: "POST", body: JSON.stringify({...identifier, password})});
      if (!rememberMe) window.localStorage.removeItem("bridge.rememberedUsername");
      await refreshSession();
      router.replace(tab === "signup" ? "/welcome" : "/home");
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }

  async function continueWithGoogle() {
    setError("");
    if (!googleAvailable) {
      setGoogleSetupOpen(true);
      return;
    }
    if (busy) return;
    setBusy(true);
    try { await signIn("google", { callbackUrl: "/api/auth/bridge" }); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }

  function continueWithEmail() {
    setError("");
    changeTab("login");
    window.requestAnimationFrame(() => emailInputRef.current?.focus());
  }

  async function resendVerification(){if(!email.trim()) {setError("Enter your email address first.");return;}setBusy(true);setError("");try{const result=await apiRequest<{message:string}>("/auth/resend-verification",{method:"POST",body:JSON.stringify({email:email.trim()})});setNotice(result.message);}catch(e){setError(errorMessage(e));}finally{setBusy(false);}}
  async function requestRecovery(event:FormEvent){event.preventDefault();setBusy(true);setRecoveryNotice("");try{const result=await apiRequest<{message:string}>("/auth/request-password-reset",{method:"POST",body:JSON.stringify({email:recoveryEmail.trim()})});setRecoveryNotice(result.message);}catch(e){setRecoveryNotice(e instanceof ApiError && e.status===404 ? "Password reset is unavailable in the running backend. Restart the backend to load the updated account routes, then try again." : errorMessage(e));}finally{setBusy(false);}}

  return (
    <main className="auth-page">
      <section className="auth-story">
        <BridgeBrand />
        <div className="auth-copy">
          <h1>A private place to<br />think out loud.</h1>
          <p>Bridge gives you a private space to write and reflect. It does not diagnose you or replace professional support.</p>
          <div className="benefit-list">
            <div><span><MessageSquareText /></span><p><strong>Your thoughts, your space</strong>Converse freely, without judgment.</p></div>
            <div><span><Network /></span><p><strong>Revisit your own words</strong>Keep captures, reflections, and personal context.</p></div>
            <div><span><ShieldCheck /></span><p><strong>Private and in your control</strong>You decide what to save and explore.</p></div>
          </div>
        </div>
        <p className="story-quote">A clearer mind builds a brighter future.</p>
      </section>

      <section className={`auth-panel ${tab === "signup" ? "auth-panel--signup" : ""}`}>
        <div className="auth-panel-top">
          <span>{tab === "login" ? "New to Bridge?" : "Already have an account?"}</span>
          <button type="button" className="ghost-button" onClick={() => changeTab(tab === "login" ? "signup" : "login")}>
            {tab === "login" ? "Create an account" : "Log in"}
          </button>
        </div>

        <div className="auth-form-wrap">
          <h2>{tab === "login" ? "Welcome back" : "Create your account"}</h2>
          <p>{tab === "login" ? "Log in to continue your journey." : "Start a private space that stays in your control."}</p>

          <div className="auth-tabs" role="tablist" aria-label="Account access">
            <button type="button" role="tab" aria-selected={tab === "login"} className={tab === "login" ? "active" : ""} onClick={() => changeTab("login")}>Log In</button>
            <button type="button" role="tab" aria-selected={tab === "signup"} className={tab === "signup" ? "active" : ""} onClick={() => changeTab("signup")}>Sign Up</button>
          </div>

          <form onSubmit={submit} autoComplete="on" noValidate>
            {tab === "signup" && <label>Full name<div className="input-wrap"><input name="name" placeholder="Enter your full name" autoComplete="name" /></div></label>}
            <label>{tab === "signup" ? "Email address" : "Email or username"}<div className="input-wrap"><Mail size={20} /><input ref={emailInputRef} id="auth-username" name="username" type="text" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="Enter your email or username" autoComplete="username" list={tab === "login" && rememberedUsername ? "remembered-usernames" : undefined} /></div></label>
            {tab === "login" && rememberedUsername && <datalist id="remembered-usernames"><option value={rememberedUsername}>Saved username</option></datalist>}
            {tab === "signup" && <label>Username<div className="input-wrap"><input name="newUsername" placeholder="Choose a username" autoComplete="username" minLength={3} maxLength={40}/></div><span className="password-hint">3–40 letters, numbers, dots, underscores, or hyphens.</span></label>}
            <label>{tab === "signup" ? "Create a new password" : "Password"}<div className="input-wrap"><LockKeyhole size={20} /><input ref={passwordInputRef} id="auth-password" name="password" type={showPassword ? "text" : "password"} placeholder={tab === "signup" ? "Create a new password" : "Enter your password"} autoComplete={tab === "login" ? "current-password" : "new-password"} /><button type="button" className="icon-button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={20} /> : <Eye size={20} />}</button></div></label>
            {tab === "signup" && <label>Confirm password<div className="input-wrap"><LockKeyhole size={20} /><input name="confirmPassword" type={showConfirmation ? "text" : "password"} placeholder="Enter the new password again" autoComplete="new-password" /><button type="button" className="icon-button" aria-label={showConfirmation ? "Hide confirmed password" : "Show confirmed password"} onClick={() => setShowConfirmation(!showConfirmation)}>{showConfirmation ? <EyeOff size={20} /> : <Eye size={20} />}</button></div><span className="password-hint">Use 8+ characters with uppercase, lowercase, a number, and a special character.</span></label>}
            {tab === "login" && <div className="form-options"><label className="check"><input type="checkbox" checked={rememberMe} onChange={(event) => setRememberMe(event.target.checked)} /> Remember username</label><button type="button" className="link-button" onClick={() => {setRecoveryEmail(email);setRecoveryOpen(true);}}>Forgot password?</button><button type="button" className="link-button" onClick={()=>void resendVerification()}>Resend verification</button></div>}
            {notice&&<p className="integration-success" role="status">{notice}</p>}
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="primary-button" type="submit" disabled={busy}>{busy ? "Please wait…" : tab === "login" ? "Log In" : "Create account"}<ArrowRight size={20} /></button>
          </form>

          <div className="divider"><span>OR</span></div>
          <div className="social-row">
            <button type="button" onClick={continueWithGoogle} disabled={busy}><b className="google-mark" aria-hidden="true">G</b>Continue with Google</button>
            <button type="button" onClick={continueWithEmail} disabled={busy}><Mail size={21} />Continue with Email</button>
          </div>
          <p className="terms">By continuing, you agree to our <button type="button" onClick={() => setLegalOpen("terms")}>Terms of Service</button><button type="button" onClick={() => setLegalOpen("privacy")}>Privacy Policy</button></p>
        </div>
      </section>

      {googleSetupOpen && (
        <div className="auth-modal-backdrop" role="presentation" onMouseDown={() => setGoogleSetupOpen(false)}>
          <section className="auth-modal google-setup-modal" role="dialog" aria-modal="true" aria-labelledby="google-setup-title" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="modal-close" aria-label="Close Google sign-in setup" onClick={() => setGoogleSetupOpen(false)}><X /></button>
            <span className="modal-symbol google-mark" aria-hidden="true">G</span>
            <p className="eyebrow">One-time setup</p>
            <h2 id="google-setup-title">Connect Google sign-in</h2>
            <p>Google sign-in is not available in this environment yet. You can create an account or log in using email and a password.</p>
            <button className="primary-button" type="button" onClick={() => setGoogleSetupOpen(false)}>Got it</button>
          </section>
        </div>
      )}

      {legalOpen && (
        <div className="auth-modal-backdrop" role="presentation" onMouseDown={() => setLegalOpen(null)}>
          <section className="auth-modal legal-modal" role="dialog" aria-modal="true" aria-labelledby="legal-title" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="modal-close" aria-label={`Close ${legalOpen === "terms" ? "terms" : "privacy policy"}`} onClick={() => setLegalOpen(null)}><X /></button>
            <div className="legal-modal-heading"><span><FileText /></span><div><p className="eyebrow">Project Bridge</p><h2 id="legal-title">{legalOpen === "terms" ? "Terms of Service" : "Privacy Policy"}</h2><p>Last updated: 30 September 2026</p></div></div>
            <div className="legal-summary-note">Prototype policy summary - this content needs legal review before a public launch.</div>
            {legalOpen === "terms" ? (
              <div className="legal-grid">
                <article><h3>Using Bridge</h3><p>Bridge supports expression and reflection. It is not a medical service or emergency resource.</p></article>
                <article><h3>Your account</h3><p>Keep your sign-in details secure and provide information that belongs to you.</p></article>
                <article><h3>Your content</h3><p>You control your conversations, captures, corrections, and Emotional Passport information.</p></article>
                <article><h3>Responsible use</h3><p>Do not harm others, break the law, disrupt the service, or attempt unauthorized access.</p></article>
                <article><h3>AI responses</h3><p>AI output can be incomplete. Patterns remain tentative and require your review.</p></article>
                <article><h3>Service changes</h3><p>Features and these terms may change as the prototype is tested and improved.</p></article>
              </div>
            ) : (
              <div className="legal-grid">
                <article><h3>Information you provide</h3><p>Account details, conversations, captures, reflections, preferences, and consent choices.</p></article>
                <article><h3>How it is used</h3><p>Only permitted information supports conversations, history, tentative patterns, and reflection.</p></article>
                <article><h3>Your controls</h3><p>You can review, correct, exclude, and delete saved items and change memory permissions.</p></article>
                <article><h3>Service providers</h3><p>Only relevant, permitted context should reach approved authentication, storage, and AI services.</p></article>
                <article><h3>Security</h3><p>Bridge is designed for secure authentication, access controls, and encryption in transit and at rest.</p></article>
                <article><h3>Notifications</h3><p>Outside-app notifications should remain generic and avoid sensitive inferred content.</p></article>
              </div>
            )}
            <button className="primary-button legal-accept" type="button" onClick={() => setLegalOpen(null)}>I understand</button>
          </section>
        </div>
      )}

      {recoveryOpen && (
        <div className="auth-modal-backdrop" role="presentation" onMouseDown={() => setRecoveryOpen(false)}>
          <section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="recovery-title" onMouseDown={(event) => event.stopPropagation()}>
            <button type="button" className="modal-close" aria-label="Close password recovery" onClick={() => setRecoveryOpen(false)}><X /></button>
            <p className="eyebrow">Account recovery</p><h2 id="recovery-title">Reset your password</h2><p>Enter the email you use to log in to Bridge. The reset link goes to that account email. The project’s sending address is configured separately.</p><form onSubmit={requestRecovery}><label>Bridge account email<input type="email" required value={recoveryEmail} onChange={e=>setRecoveryEmail(e.target.value)}/></label><button className="primary-button" disabled={busy}>Send reset link</button></form>{recoveryNotice&&<p role="status">{recoveryNotice}</p>}
          </section>
        </div>
      )}
    </main>
  );
}
