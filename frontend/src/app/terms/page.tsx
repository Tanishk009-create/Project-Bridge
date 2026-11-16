import { PolicyPage } from "@/components/screens/PolicyPage";

const sections = [
  { title: "Using Bridge", body: "Bridge is an AI-assisted space for expression, reflection, and organizing personal context. It is not a medical service, does not provide a diagnosis, and does not replace a qualified mental-health professional or emergency service." },
  { title: "Your account", body: "You are responsible for keeping your sign-in details secure and for the activity performed through your account. Information supplied during registration should be accurate and should belong to you." },
  { title: "Your content and choices", body: "You retain control of the thoughts, conversations, captures, corrections, and Passport information you provide. Memory, reflection, and pattern permissions determine how saved information may be used within the product." },
  { title: "Responsible use", body: "Do not use Bridge to harm another person, violate applicable law, attempt unauthorized access, disrupt the service, or submit content that you do not have permission to use." },
  { title: "AI-generated responses", body: "AI responses can be incomplete or incorrect. Pattern suggestions are tentative and should be reviewed by you. Bridge must not be treated as the sole basis for medical, legal, financial, or safety-critical decisions." },
  { title: "Availability and changes", body: "Features may change as the prototype is tested. We may update these terms when the service, law, or product scope changes, and the current version will remain available from the sign-in page." },
  { title: "Contact", body: "Before launch, this section should contain the official Project Bridge operator name, support email, governing law, and complaint process." },
];

export default function TermsPage() {
  return <PolicyPage title="Terms of Service" intro="These terms describe the intended rules for using Project Bridge and the boundaries of its AI-assisted experience." sections={sections} />;
}
