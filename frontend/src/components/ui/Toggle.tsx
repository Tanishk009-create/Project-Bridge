"use client";

export function Toggle({ checked, onChange, label, disabled=false }: { checked: boolean; onChange: (checked: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <label className="toggle-control">
      <input type="checkbox" checked={checked} disabled={disabled} onChange={(event) => onChange(event.target.checked)} aria-label={label} />
      <span className="toggle-track" aria-hidden="true"><span className="toggle-knob" /></span>
    </label>
  );
}
