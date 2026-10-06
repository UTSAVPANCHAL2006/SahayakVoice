import type { Scenario } from "@/lib/api";

export type IssueFilter =
  | "ALL"
  | "CHEQUE_BOUNCE"
  | "LIEN"
  | "HOLD"
  | "FREEZE"
  | "INOPERATIVE";

export const ISSUE_FILTERS: { id: IssueFilter; label: string }[] = [
  { id: "ALL", label: "All" },
  { id: "CHEQUE_BOUNCE", label: "Cheque Bounce" },
  { id: "LIEN", label: "Lien" },
  { id: "HOLD", label: "Payment Hold" },
  { id: "FREEZE", label: "Debit Freeze" },
  { id: "INOPERATIVE", label: "Inoperative" },
];

export function countByIssue(scenarios: Scenario[], issue: string): number {
  return scenarios.filter((s) => s.primaryIssue === issue).length;
}

function matchesIssueFilter(primaryIssue: string | undefined, filter: IssueFilter): boolean {
  if (filter === "ALL") return true;
  const issue = (primaryIssue || "").toUpperCase();
  if (filter === "FREEZE") return issue === "FREEZE" || issue === "DEBIT_FREEZE";
  return issue === filter;
}

export function filterScenarios<T extends Scenario>(
  scenarios: T[],
  filter: IssueFilter,
  searchQuery: string
): T[] {
  const q = searchQuery.trim().toLowerCase();
  return scenarios.filter((s) => {
    const matchesFilter = matchesIssueFilter(s.primaryIssue, filter);
    if (!matchesFilter) return false;
    if (!q) return true;
    const maskedAcct = (s as unknown as { maskedAcct?: string }).maskedAcct || "";
    return (
      (s.customerName || "").toLowerCase().includes(q) ||
      (s.label || "").toLowerCase().includes(q) ||
      (s.accountId || "").toLowerCase().includes(q) ||
      maskedAcct.toLowerCase().includes(q) ||
      (s.primaryIssue || "").toLowerCase().includes(q)
    );
  });
}
