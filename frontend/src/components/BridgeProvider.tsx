"use client";
import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { ApiError, apiRequest, errorMessage } from "@/lib/api";
import type { User, Preferences } from "@/types/api";

interface BridgeState { user: User | null; preferences: Preferences | null; ready: boolean; error: string;
  refreshSession: () => Promise<void>; savePreferences: (values: Partial<Preferences>) => Promise<void>;
  saveProfile: (display_name: string) => Promise<void>; }
const BridgeContext = createContext<BridgeState | null>(null);
export function BridgeProvider({children}: {children: ReactNode}) {
  const [user, setUser] = useState<User | null>(null);
  const [preferences, setPreferences] = useState<Preferences | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const refreshSession = useCallback(async () => {
    try {
      const current = await apiRequest<User>("/users/me");
      const prefs = await apiRequest<Preferences>("/users/me/preferences");
      setUser(current); setPreferences(prefs); setError("");
    } catch (e) {
      setUser(null); setPreferences(null);
      setError(e instanceof ApiError && e.status === 401 ? "" : errorMessage(e));
    } finally { setReady(true); }
  }, []);
  useEffect(() => {
    void Promise.resolve().then(refreshSession);
    const expired = () => { setUser(null); setPreferences(null); };
    window.addEventListener("bridge-session-expired", expired);
    return () => window.removeEventListener("bridge-session-expired", expired);
  }, [refreshSession]);
  useEffect(()=>{
    document.documentElement.dataset.bridgeSize=preferences?.text_size||"comfortable";
  },[preferences?.text_size]);
  async function savePreferences(values: Partial<Preferences>) {
    const saved = await apiRequest<Preferences>("/users/me/preferences", {method: "PATCH", body: JSON.stringify(values)});
    setPreferences(saved);
  }
  async function saveProfile(display_name: string) {
    setUser(await apiRequest<User>("/users/me", {method: "PATCH", body: JSON.stringify({display_name})}));
  }
  return <BridgeContext.Provider value={{user, preferences, ready, error, refreshSession, savePreferences, saveProfile}}>{children}</BridgeContext.Provider>;
}
export function useBridge() { const context = useContext(BridgeContext); if (!context) throw new Error("BridgeProvider is required"); return context; }
