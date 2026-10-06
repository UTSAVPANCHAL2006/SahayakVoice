/** Queue → live call handoff (masked outreach context only; no verification secrets). */

export type PendingCallContext = {
  accountId: string;
  customerName?: string;
  maskedAcct?: string;
  primaryIssue?: string;
  callLang?: string;
};

const KEY = "sahayak.pendingCall";

export function savePendingCallContext(ctx: PendingCallContext) {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(ctx));
  } catch {
    /* ignore */
  }
}

export function loadPendingCallContext(): PendingCallContext | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    return JSON.parse(raw) as PendingCallContext;
  } catch {
    return null;
  }
}

export function clearPendingCallContext() {
  try {
    sessionStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}

/** Backend scenario id → primary issue code */
export function issueFromScenarioId(scenario: string | undefined): string | undefined {
  if (!scenario) return undefined;
  const map: Record<string, string> = {
    P1_INOPERATIVE: "INOPERATIVE",
    P2_LIEN: "LIEN",
    P2_HOLD: "HOLD",
    P2_CHEQUE: "CHEQUE_BOUNCE",
    P3_FREEZE: "DEBIT_FREEZE",
  };
  return map[scenario] || undefined;
}
