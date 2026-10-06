"use client";

import { formatAccountEnding, formatInrOptional } from "@/lib/format";

type Snap = Record<string, unknown> | null;

type Props = {
  primaryIssue?: string;
  verified: boolean;
  snap: Snap;
  phase?: string;
  proof?: Record<string, unknown> | null;
  /** Masked account from queue / session API (visible before verify). */
  outreachAccount?: string | null;
  outreachCustomer?: string | null;
};

function RailBlock({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="case-rail__block">
      <div className="case-rail__label">{label}</div>
      <div className="case-rail__value">{children}</div>
    </div>
  );
}

function FactRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="case-rail__fact">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function issueTitle(issue: string) {
  const map: Record<string, string> = {
    CHEQUE_BOUNCE: "Cheque bounce",
    LIEN: "Lien",
    HOLD: "Payment hold",
    DEBIT_FREEZE: "Debit freeze",
    FREEZE: "Debit freeze",
    INOPERATIVE: "Inoperative",
  };
  return map[issue] || issue.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function CaseContextPanel({
  primaryIssue,
  verified,
  snap,
  phase,
  proof,
  outreachAccount,
}: Props) {
  const issue = (primaryIssue || (snap?.primaryIssue as string) || "").toUpperCase();
  const handoffActive =
    phase === "handoff" ||
    proof?.handoffStage === "connected" ||
    (proof?.handoff as { status?: string } | undefined)?.status === "CONNECTED";
  const resolved = phase === "end";

  const ch = (snap?.cheque || snap?.extra || {}) as Record<string, unknown>;
  const ld = (snap?.lienDetails || snap?.extra || {}) as Record<string, unknown>;
  const hd = (snap?.holdDetails || snap?.extra || {}) as Record<string, unknown>;
  const fd = (snap?.freezeDetails || snap?.extra || {}) as Record<string, unknown>;
  const iod = (snap?.inoperativeDetails || snap?.extra || {}) as Record<string, unknown>;

  const chequeNo = ch.chequeNumber ? `•••• ${String(ch.chequeNumber).slice(-4)}` : null;
  const chequeAmt = formatInrOptional(Number(ch.amount_inr || ch.amountInr || 0) || null);
  const chequeReason = String(ch.reason_code || ch.reasonCode || ch.reason || "").trim() || null;

  const masked =
    formatAccountEnding({ maskedAcct: snap?.maskedAcct as string | undefined }) ??
    outreachAccount ??
    null;

  return (
    <div className="case-rail" aria-label="Case and banking context">
      <RailBlock label="Case">{issue ? issueTitle(issue) : "—"}</RailBlock>
      <RailBlock label="Status">
        {resolved ? (
          <span className="case-rail__status case-rail__status--resolved">Resolved</span>
        ) : handoffActive ? (
          <span className="case-rail__status case-rail__status--handoff">Human handoff</span>
        ) : (
          "Open"
        )}
      </RailBlock>
      {masked && <RailBlock label="Account">{masked}</RailBlock>}
      <RailBlock label="Verification">
        {verified ? "Verified" : "Pending"}
      </RailBlock>

      {!verified ? (
        <div className="case-rail__locked">
          <div className="case-rail__locked-title">Banking context unavailable</div>
          <p>Locked until identity verification.</p>
        </div>
      ) : !snap ? (
        <p className="case-rail__muted">Synchronizing authorized context…</p>
      ) : (
        <>
          <div className="case-rail__auth-label">Authorized context</div>
          <div className="case-rail__facts">
            {issue === "CHEQUE_BOUNCE" && (
              <>
                <FactRow label="Cheque status" value="Returned" />
                <FactRow label="Reason" value={chequeReason || "Insufficient balance"} />
                <FactRow label="Reference" value={chequeNo} />
                <FactRow label="Amount" value={chequeAmt} />
                <FactRow label="Available" value={formatInrOptional(snap.availableBalanceInr as number)} />
              </>
            )}
            {issue === "LIEN" && (
              <>
                <FactRow label="Lien amount" value={formatInrOptional(snap.holdAmountInr as number)} />
                <FactRow
                  label="Reason"
                  value={String(ld.lienReason || ld.lien_reason || "Tax attachment").trim()}
                />
                <FactRow label="Available" value={formatInrOptional(snap.availableBalanceInr as number)} />
              </>
            )}
            {issue === "HOLD" && (
              <>
                <FactRow label="Hold" value={formatInrOptional(snap.holdAmountInr as number)} />
                <FactRow label="Status" value={String(hd.reason || hd.holdReason || "UPI pending").trim()} />
                <FactRow label="Available" value={formatInrOptional(snap.availableBalanceInr as number)} />
              </>
            )}
            {(issue === "FREEZE" || issue === "DEBIT_FREEZE") && (
              <>
                <FactRow label="Restriction" value={String(fd.restrictionType || "Debit freeze")} />
                <FactRow label="Reason" value={String(fd.reason || "Cyber cell / KYC").trim()} />
              </>
            )}
            {issue === "INOPERATIVE" && (
              <>
                <FactRow label="Account status" value="Dormant / inactive" />
                <FactRow label="Next step" value={String(iod.action || "Branch Re-KYC").trim()} />
                <FactRow label="Balance" value={formatInrOptional(snap.ledgerBalanceInr as number)} />
              </>
            )}
            {!issue && (
              <>
                <FactRow label="Ledger" value={formatInrOptional(snap.ledgerBalanceInr as number)} />
                <FactRow label="Available" value={formatInrOptional(snap.availableBalanceInr as number)} />
              </>
            )}
          </div>
        </>
      )}
    </div>
  );
}
