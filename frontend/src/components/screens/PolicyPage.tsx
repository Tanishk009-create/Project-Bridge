import Link from "next/link";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { BridgeBrand } from "@/components/brand/BridgeBrand";

interface PolicySection {
  title: string;
  body: string;
}

export function PolicyPage({ title, intro, sections }: { title: string; intro: string; sections: PolicySection[] }) {
  return (
    <main className="policy-page">
      <header className="policy-header">
        <Link href="/" aria-label="Return to Bridge login"><BridgeBrand compact /></Link>
        <Link href="/" className="secondary-button"><ArrowLeft size={16} />Back to login</Link>
      </header>
      <article className="policy-document">
        <div className="policy-title"><span><ShieldCheck /></span><div><p className="eyebrow">Project Bridge</p><h1>{title}</h1><p>Last updated: 27 October 2026</p></div></div>
        <p className="policy-intro">{intro}</p>
        <div className="policy-prototype-note"><strong>Prototype notice</strong><span>This text explains the intended product behaviour. It must be reviewed and approved by a qualified legal professional before a public launch.</span></div>
        {sections.map((section, index) => <section key={section.title}><h2>{index + 1}. {section.title}</h2><p>{section.body}</p></section>)}
        <Link href="/" className="primary-button"><ArrowLeft size={16} />Return to Bridge</Link>
      </article>
    </main>
  );
}
