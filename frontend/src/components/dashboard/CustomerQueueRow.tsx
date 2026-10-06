"use client";

import type { CallLang, Scenario, SupervisorScenario } from "@/lib/api";
import { isSupervisorPanelEnabled } from "@/lib/api";
import { formatAccountEnding } from "@/lib/format";

type Props = {
  scenario: Scenario | SupervisorScenario;
  busy?: boolean;
  selected?: boolean;
  onSelect?: () => void;
  onCall: (accountId: string, lang: CallLang) => void;
};

function getInitials(name = ""): string {
  const parts = name.trim().split(" ");
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : name.slice(0, 2).toUpperCase() || "??";
}

function issueMeta(issue = ""): { label: string; dotColor: string } {
  const u = issue.toUpperCase();
  if (u.includes("BOUNCE")) return { label: "Cheque Bounce", dotColor: "#7c3aed" };
  if (u.includes("LIEN"))   return { label: "Tax Lien", dotColor: "#d97706" };
  if (u.includes("HOLD"))   return { label: "Payment Hold", dotColor: "#e11d48" };
  if (u.includes("FREEZE")) return { label: "Debit Freeze", dotColor: "#2563eb" };
  if (u.includes("INOP"))   return { label: "Inoperative", dotColor: "#64748b" };
  return { label: issue.replace(/_/g, " ") || "Active Case", dotColor: "#059669" };
}

function PhoneCallIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.4 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.5a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 21.38 16c.04.308.06.617.06.92z" />
    </svg>
  );
}

export function CustomerQueueRow({ scenario: s, busy, selected, onSelect, onCall }: Props) {
  const sup = s as SupervisorScenario;
  const masked = formatAccountEnding({ maskedAcct: s.maskedAcct || sup.maskedAcct, accountId: s.accountId }) || "—";
  const supervisorOn = isSupervisorPanelEnabled();
  const issue = s.primaryIssue || "";
  const meta = issueMeta(issue);
  const preferred: CallLang = "gujarati";

  return (
    <div
      className={`queue-row ${selected ? "queue-row--selected" : ""}`}
      onClick={onSelect}
      aria-selected={selected}
    >
      <div className="queue-row__cells">
        {/* Customer Avatar & Name */}
        <div className="queue-row__customer-block">
          <div className="q-avatar" aria-hidden="true">
            {getInitials(s.customerName)}
          </div>
          <div className="q-info">
            <div className="q-name-row">
              <span className="q-name">{s.customerName || "Customer"}</span>
              <span className="q-badge">
                <span className="q-badge__dot" style={{ backgroundColor: meta.dotColor }} />
                <span>{meta.label}</span>
              </span>
            </div>
            <div className="q-meta">
              <span className="q-acct-chip">{masked}</span>
              <span className="q-dot-sep">/</span>
              <span className="q-lang-chip">Gujarati (ગુજરાતી)</span>
              {supervisorOn && sup.expectedLast4 && (
                <>
                  <span className="q-dot-sep">/</span>
                  <span className="q-supervisor-pill" title="Supervisor Auth Reference (Expected Last 4)">
                    <span className="q-supervisor-pill__icon">🛡️</span>
                    <span className="q-supervisor-pill__label">Auth</span>
                    <span className="q-supervisor-pill__code">{sup.expectedLast4}</span>
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Status column */}
        <div className="queue-row__case-block">
          <div className="q-ready">
            <span className="q-ready__pulse" />
            <span>Ready for Voice</span>
          </div>
        </div>

        {/* Action Button — Gujarati Voice */}
        <div className="queue-row__call-block" onClick={(e) => e.stopPropagation()}>
          <button
            type="button"
            className="q-call-btn"
            disabled={busy}
            onClick={() => onCall(s.accountId, "gujarati")}
            title="Start outbound call in Gujarati"
          >
            <PhoneCallIcon />
            <span>Call Gujarati</span>
          </button>
        </div>
      </div>
    </div>
  );
}
