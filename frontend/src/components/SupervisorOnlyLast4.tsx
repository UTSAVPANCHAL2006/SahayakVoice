"use client";

type Props = { digits: string };

export function SupervisorOnlyLast4({ digits }: Props) {
  const clean = digits.replace(/\D/g, "").slice(0, 4);

  return (
    <div className="supervisor-only-last4" role="note" aria-label="Supervisor only expected last four digits">
      <div className="supervisor-only-last4__header">
        <div className="supervisor-only-last4__tag">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          <span>Supervisor Audit</span>
        </div>
        <span className="supervisor-only-last4__status">Hard Gate</span>
      </div>
      <div className="supervisor-only-last4__digits-box">
        <span className="supervisor-only-last4__label">Expected Last 4</span>
        <div className="supervisor-only-last4__pins">
          {clean.split("").map((d, i) => (
            <span key={i} className="supervisor-pin-cell">{d}</span>
          ))}
        </div>
      </div>
      <p className="supervisor-only-last4__note">
        Voice AI prompts customer for this key before disclosing sensitive balance or hold data.
      </p>
    </div>
  );
}
