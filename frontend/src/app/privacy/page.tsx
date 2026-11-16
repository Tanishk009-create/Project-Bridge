import { PolicyPage } from "@/components/screens/PolicyPage";

const sections = [
  { title: "Information you provide", body: "Bridge may process account details, conversations, Quick Captures, reflections, Emotional Passport items, corrections, preferences, and consent choices that you choose to provide." },
  { title: "How information is used", body: "Permitted information is used to provide conversations, preserve selected context, show chronological history, suggest tentative patterns, and support user-requested reflection. Bridge does not automatically convert private conversations into public content or therapist-facing records." },
  { title: "Memory and pattern controls", body: "You can decide whether information is saved, used in future conversations, included in pattern detection, or available for reflection. You can review, correct, exclude, and delete stored items." },
  { title: "AI and service providers", body: "When you enable AI replies, the backend sends your current message and earlier explicitly AI-shared turns in that conversation to Google Gemini. Selected confirmed memory, permitted Passport entries and interpretation corrections may accompany it when memory is enabled. Manual analysis shares up to 30 eligible messages and earlier pattern feedback. Gemini free-tier inputs and outputs may be used to improve Google products and reviewed by humans. Do not submit sensitive, confidential or personal information to the free tier; use fictional data for testing. Provider policies still apply. Turning off sharing stops new requests but cannot recall a request already sent." },
  { title: "Retention and deletion", body: "Information should be retained only for the documented product purpose and applicable legal requirements. Account controls should allow deletion of individual memories, entries, or the account, subject to clearly explained backup and security retention periods." },
  { title: "Security", body: "Project Bridge is designed to use access controls, secure authentication, encryption in transit and at rest, and appropriate session management. No system can guarantee absolute security." },
  { title: "Notifications", body: "Notifications outside the app should remain generic and should not expose inferred emotions, sensitive conversation text, or tentative patterns on a lock screen." },
  { title: "Your choices and contact", body: "Before launch, this section should identify the data controller, privacy contact, applicable user rights, regional disclosures, and a process for access, correction, deletion, and complaints." },
];

export default function PrivacyPage() {
  return <PolicyPage title="Privacy Policy" intro="This policy explains the privacy model described in the Project Bridge requirements: data minimization, clear permissions, correctability, and user control." sections={sections} />;
}
