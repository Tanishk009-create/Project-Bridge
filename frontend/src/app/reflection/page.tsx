import { Suspense } from "react";
import { ReflectionScreen } from "@/components/screens/ReflectionScreen";
export default function ReflectionPage() { return <Suspense fallback={<div className="screen-loader">Loading…</div>}><ReflectionScreen /></Suspense>; }
