import { Suspense } from "react";
import { ConversationScreen } from "@/components/screens/ConversationScreen";

export default function ConversationPage() {
  return <Suspense fallback={<div className="screen-loader">Opening your private space…</div>}><ConversationScreen /></Suspense>;
}
