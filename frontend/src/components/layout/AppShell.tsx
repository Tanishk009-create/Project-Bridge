"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { CircleHelp, Clock3, Fingerprint, Home, Network, BookOpen } from "lucide-react";
import { type ReactNode, useEffect, useState } from "react";
import { BridgeBrand } from "@/components/brand/BridgeBrand";
import { AppInfoDialog, type AppInfoDialogType } from "@/components/ui/AppInfoDialog";
import { AccountMenu } from "@/components/ui/AccountMenu";
import { useBridge } from "@/components/BridgeProvider";
const navigation = [
  { href: "/home", label: "Home", icon: Home }, { href: "/history", label: "History", icon: Clock3 },
  { href: "/reflection", label: "Reflections", icon: Network }, { href: "/passport", label: "Passport", icon: Fingerprint },
  { href: "/notebook", label: "Notebook", icon: BookOpen },
];
export function AppShell({children}: {children: ReactNode}) {
  const pathname = usePathname(); const router = useRouter();
  const {user, preferences, ready, error, refreshSession} = useBridge();
  const [infoDialog, setInfoDialog] = useState<AppInfoDialogType | null>(null);
  useEffect(() => {
    if (ready && !error && !user) router.replace("/login");
    else if (user && preferences && !preferences.onboarding_complete && pathname !== "/welcome") router.replace("/welcome");
  }, [ready, error, user, preferences, pathname, router]);
  if (error) return <main className="session-state"><h1>Unable to load your space</h1><p role="alert">{error}</p><button className="primary-button" onClick={() => void refreshSession()}>Try again</button></main>;
  if (!ready || !user || !preferences) return <main className="screen-loader" role="status">Loading your space…</main>;
  if (!preferences.onboarding_complete && pathname !== "/welcome") return <main className="screen-loader">Opening welcome…</main>;
  return <div className={`app-frame app-frame--text-${preferences.text_size}${preferences.dark_mode ? " app-frame--dark" : ""}${preferences.reduced_motion ? " app-frame--reduced-motion" : ""}`}>
    <aside className="sidebar">
      <button className="brand-trigger" aria-label="About Project Bridge" onClick={() => setInfoDialog("about")}><BridgeBrand compact /></button>
      <nav aria-label="Primary navigation">{navigation.map(({href,label,icon:Icon}) => <Link key={href} href={href} className={pathname === href ? "active" : ""}><Icon size={18}/><span>{label}</span></Link>)}</nav>
      <AccountMenu/>
    </aside>
    <main className="app-main"><div className="topbar"><button className="brand-trigger" aria-label="About Project Bridge" onClick={() => setInfoDialog("about")}><BridgeBrand compact /></button><button className="help-button" onClick={() => setInfoDialog("help")}><CircleHelp size={17}/>Help</button><div className="mobile-account"><AccountMenu compact/></div></div>{children}</main>
    <nav className="mobile-nav" aria-label="Mobile navigation">{navigation.map(({href,label,icon:Icon}) => <Link key={href} href={href} className={pathname === href ? "active" : ""}><Icon size={19}/><span>{label}</span></Link>)}</nav>
    {infoDialog && <AppInfoDialog type={infoDialog} onClose={() => setInfoDialog(null)}/>}
  </div>;
}
