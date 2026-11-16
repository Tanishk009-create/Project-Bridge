"use client";
import { useCallback, useEffect, useState } from "react";
import { useBridge } from "@/components/BridgeProvider";
import { apiRequest, errorMessage } from "@/lib/api";
export function useResource<T>(path: string | null) {
  const {user} = useBridge();
  const [result, setResult] = useState<{key: string; data?: T; error?: string}>({key: ""});
  const [version, setVersion] = useState(0);
  const key = `${user?.id}:${path}:${version}`;
  const reload = useCallback(() => setVersion(v => v + 1), []);
  useEffect(() => {
    if (!user || !path) return;
    const controller = new AbortController();
    apiRequest<T>(path, {signal: controller.signal}).then(data => setResult({key, data})).catch(e => {
      if (!controller.signal.aborted) setResult({key, error: errorMessage(e)});
    });
    return () => controller.abort();
  }, [key, path, user]);
  return {data: result.key === key ? result.data : undefined, error: result.key === key ? result.error : undefined,
    loading: !!path && result.key !== key, reload};
}
