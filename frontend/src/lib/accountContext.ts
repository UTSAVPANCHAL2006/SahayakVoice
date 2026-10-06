import { formatInr } from "@/lib/format";

export type AccountContext = {
  accountId?: string;
  customerName?: string;
  maskedAcct?: string;
  maskedLast4?: string;
  primaryIssue?: string;
  bankName?: string;
  ledgerBalanceInr?: number;
  availableBalanceInr?: number;
  holdAmountInr?: number;
  expectedLast4?: string;
  preferredLang?: string;
  chequeNumber?: string;
  chequeAmountInr?: number;
  returnReason?: string;
  chequeStatus?: string;
  lienAmountInr?: number;
  lienReason?: string;
  lienAuthority?: string;
  holdReason?: string;
  txnAmountInr?: number;
  accountStatus?: string;
  freezeReason?: string;
  inactiveReason?: string;
  lastTransactionDate?: string;
  referenceNumber?: string;
};

export type ContextRow = { label: string; value: string; emphasis?: boolean };

export function maskAccountDisplay(masked?: string, last4?: string): string {
  const l4 = last4 || (masked ? masked.replace(/\D/g, "").slice(-4) : "");
  if (!l4) return "•••• —";
  return `•••• ${l4}`;
}

export function langLabel(code?: string): string {
  return "Gujarati (ગુજરાતી)";
}

export function caseRows(ctx: AccountContext | undefined): ContextRow[] {
  if (!ctx?.primaryIssue) return [];
  const issue = ctx.primaryIssue.toUpperCase();
  const rows: ContextRow[] = [];

  if (ctx.ledgerBalanceInr !== undefined) {
    rows.push({ label: "Balance", value: formatInr(ctx.ledgerBalanceInr), emphasis: true });
  }

  if (issue === "CHEQUE_BOUNCE") {
    if (ctx.holdAmountInr !== undefined) {
      rows.push({ label: "Hold", value: formatInr(ctx.holdAmountInr) });
    }
    if (ctx.chequeNumber) rows.push({ label: "Cheque", value: `#${ctx.chequeNumber}` });
    if (ctx.chequeAmountInr !== undefined) {
      rows.push({ label: "Cheque amount", value: formatInr(ctx.chequeAmountInr) });
    }
    if (ctx.chequeStatus) rows.push({ label: "Status", value: ctx.chequeStatus });
    if (ctx.returnReason) rows.push({ label: "Return reason", value: String(ctx.returnReason) });
  } else if (issue === "LIEN") {
    if (ctx.lienAmountInr !== undefined || ctx.holdAmountInr !== undefined) {
      rows.push({
        label: "Lien",
        value: formatInr(ctx.lienAmountInr ?? ctx.holdAmountInr),
      });
    }
    if (ctx.availableBalanceInr !== undefined) {
      rows.push({ label: "Available", value: formatInr(ctx.availableBalanceInr) });
    }
    if (ctx.lienReason) rows.push({ label: "Lien reason", value: ctx.lienReason });
    if (ctx.referenceNumber) rows.push({ label: "Reference", value: ctx.referenceNumber });
  } else if (issue === "HOLD") {
    if (ctx.holdAmountInr !== undefined) {
      rows.push({ label: "Hold", value: formatInr(ctx.holdAmountInr) });
    }
    if (ctx.availableBalanceInr !== undefined) {
      rows.push({ label: "Available", value: formatInr(ctx.availableBalanceInr) });
    }
    if (ctx.holdReason) rows.push({ label: "Hold reason", value: ctx.holdReason });
    if (ctx.referenceNumber) rows.push({ label: "Reference", value: ctx.referenceNumber });
  } else if (issue === "FREEZE") {
    if (ctx.accountStatus) rows.push({ label: "Account status", value: ctx.accountStatus });
    if (ctx.freezeReason) rows.push({ label: "Freeze reason", value: ctx.freezeReason });
    if (ctx.availableBalanceInr !== undefined) {
      rows.push({ label: "Available", value: formatInr(ctx.availableBalanceInr) });
    }
  } else if (issue === "INOPERATIVE") {
    if (ctx.accountStatus) rows.push({ label: "Account status", value: ctx.accountStatus });
    if (ctx.inactiveReason) rows.push({ label: "Reason", value: ctx.inactiveReason });
    if (ctx.lastTransactionDate) {
      rows.push({ label: "Last activity", value: ctx.lastTransactionDate });
    }
  }

  return rows;
}
