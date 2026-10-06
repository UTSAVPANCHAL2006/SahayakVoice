import type { Scenario } from "@/lib/api";

export type DossierScenario = Scenario & {
  ledgerBalanceInr?: number;
  availableBalanceInr?: number;
  holdAmountInr?: number;
  dossierExtra?: Record<string, unknown>;
};

export function formatInr(amount: number | undefined | null): string {
  if (amount == null || Number.isNaN(amount)) return "—";
  return `₹${amount.toLocaleString("en-IN")}`;
}

export function dossierTotalBalance(s: DossierScenario): string {
  return formatInr(s.ledgerBalanceInr);
}

export type ImpactedLine = { title: string; value: string };

export function dossierImpacted(s: DossierScenario): ImpactedLine {
  const issue = (s.primaryIssue || "").toUpperCase();
  const extra = s.dossierExtra || {};

  if (issue === "CHEQUE_BOUNCE") {
    const charge = Number(extra.chargesInr ?? 523);
    return { title: "Return charge", value: formatInr(charge) };
  }
  if (issue === "LIEN") {
    return { title: "Lien held", value: formatInr(s.holdAmountInr) };
  }
  if (issue === "HOLD") {
    const hold = s.holdAmountInr ?? Number(extra.txnAmountInr ?? 19847);
    return { title: "Amount on hold", value: formatInr(hold) };
  }
  if (issue === "FREEZE" || issue === "DEBIT_FREEZE") {
    const ledger = s.ledgerBalanceInr ?? 0;
    const avail = s.availableBalanceInr ?? 0;
    const blocked = Math.max(0, ledger - avail);
    return {
      title: "Debit restriction",
      value: blocked > 0 ? formatInr(blocked) : "Debits blocked",
    };
  }
  if (issue === "INOPERATIVE") {
    return {
      title: "In bank (inactive)",
      value: formatInr(s.ledgerBalanceInr),
    };
  }
  return { title: "Impacted amount", value: formatInr(s.holdAmountInr) };
}

export function dossierOutreachObjective(s: DossierScenario): string {
  const issue = (s.primaryIssue || "").toUpperCase();
  const extra = s.dossierExtra || {};
  const name = s.customerName?.split(" ")[0] || "Customer";

  if (issue === "CHEQUE_BOUNCE") {
    const no = String(extra.chequeNumber ?? "847293");
    const amt = Number(extra.amountInr ?? extra.chequeAmountInr ?? 49847);
    const charge = Number(extra.chargesInr ?? extra.chequeChargesInr ?? 523);
    const payee = String(extra.payeeName ?? "payee");
    return `Inform ${name} about returned cheque #${no} (₹${amt.toLocaleString("en-IN")} to ${payee}), explain ₹${charge.toLocaleString("en-IN")} return charge, and options to re-deposit or pay via UPI/NEFT.`;
  }
  if (issue === "LIEN") {
    const lien = s.holdAmountInr ?? 38419;
    const avail = s.availableBalanceInr ?? 14364;
    const ref = String(extra.referenceNumber ?? "IT-ATTACH-2026-8891");
    return `Explain ₹${lien.toLocaleString("en-IN")} statutory tax lien (${ref}), confirm ₹${avail.toLocaleString("en-IN")} still usable today, and guide on IT release order via branch.`;
  }
  if (issue === "HOLD") {
    const hold = s.holdAmountInr ?? Number(extra.txnAmountInr ?? 19847);
    const avail = s.availableBalanceInr ?? 77494;
    return `Reassure that ₹${hold.toLocaleString("en-IN")} transfer is pending in clearing (not lost); ₹${avail.toLocaleString("en-IN")} remains usable — advise against duplicate payment until status clears.`;
  }
  if (issue === "FREEZE" || issue === "DEBIT_FREEZE") {
    const ref = String(extra.referenceNumber ?? "FRZ-SEC-2026-1180");
    return `Explain debit freeze (${ref}) blocking ATM/UPI debits; ledger ₹${(s.ledgerBalanceInr ?? 78329).toLocaleString("en-IN")} — branch Re-KYC / compliance steps to lift restriction.`;
  }
  if (issue === "INOPERATIVE") {
    const bal = s.ledgerBalanceInr ?? 43827;
    return `Notify ${name} of dormancy under RBI rules; ₹${bal.toLocaleString("en-IN")} remains in bank — in-person branch Re-KYC to reactivate (PAN, Aadhaar, address proof).`;
  }
  return "Banking operational outreach for this account — verify identity before sharing ledger details.";
}
