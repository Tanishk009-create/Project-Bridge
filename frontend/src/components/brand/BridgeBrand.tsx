import Image from "next/image";

export function BridgeBrand({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand ${compact ? "brand--compact" : ""}`}>
      <Image src="/bridge-logo.png" width={compact ? 34 : 46} height={compact ? 34 : 46} alt="Bridge logo" priority />
      <div>
        <strong>BRIDGE</strong>
        {!compact && <span>Conversations → Context → Clarity</span>}
      </div>
    </div>
  );
}
