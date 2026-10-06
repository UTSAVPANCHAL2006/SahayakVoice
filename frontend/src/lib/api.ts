const PROD_API = "https://sahayakvoice.onrender.com";
const PROD_WS = "wss://sahayakvoice.onrender.com";

function isProduction(): boolean {
  return (
    typeof window !== "undefined" &&
    window.location.hostname !== "localhost" &&
    window.location.hostname !== "127.0.0.1"
  );
}

export function getApiUrl(): string {
  // In production browser, use relative paths so requests go through Next.js rewrites proxy.
  if (isProduction()) {
    return "";
  }
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (envUrl) {
    return envUrl.replace(/\/+$/, "");
  }
  return "http://localhost:8001";
}

export function getWsUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_WS_URL;
  if (envUrl) {
    return envUrl.replace(/\/+$/, "");
  }
  return isProduction() ? PROD_WS : "ws://localhost:8001";
}


export type CallLang = "gujarati";

export type Scenario = {
  accountId: string;
  maskedAcct?: string;
  primaryIssue: string;
  label: string;
  customerName?: string;
  preferredLang?: string;
  ledgerBalanceInr?: number;
  availableBalanceInr?: number;
  holdAmountInr?: number;
  dossierExtra?: Record<string, unknown>;
};

export type SupervisorScenario = Scenario & {
  maskedAcct?: string;
  caseLabel?: string;
  ledgerBalanceInr?: number;
  availableBalanceInr?: number;
  holdAmountInr?: number;
  expectedLast4?: string;
  accountContext?: Record<string, any>;
  /** @deprecated use expectedLast4 */
  verifyLast4?: string;
};

export type CallSupervisorHint = {
  sessionId?: string;
  accountId?: string;
  customerName?: string;
  primaryIssue?: string;
  caseLabel?: string;
  callLang?: string;
  expectedLast4?: string;
  maskedAcct?: string;
  phase?: string;
  verified?: boolean;
};

export type CallSessionDetail = {
  sessionId: string;
  accountId: string;
  maskedAcct?: string | null;
  scenario: string;
  phase: string;
  verified: boolean;
  snapshotId?: string;
  transcript: Array<{ role: string; content: string }>;
  proof?: Record<string, unknown>;
};

export async function fetchHealth(): Promise<{
  ok: boolean;
  database?: string;
  accounts?: number;
  detail?: string;
  integrations?: Record<string, unknown>;
}> {
  try {
    const url = `${getApiUrl()}/health`;
    console.log("[fetchHealth] calling", url);
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) {
      return { ok: false, detail: `HTTP ${res.status} from ${url}` };
    }
    const data = await res.json();
    console.log("[fetchHealth] response", data);
    return data;
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[fetchHealth] error:", msg);
    return { ok: false, detail: msg };
  }
}

const SUPERVISOR =
  process.env.NEXT_PUBLIC_DEMO_SUPERVISOR_PANEL === "true" ||
  process.env.NEXT_PUBLIC_DEMO_SUPERVISOR_PANEL === "1";

export async function fetchScenarios(): Promise<Scenario[]> {
  const res = await fetch(`${getApiUrl()}/api/scenarios`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  const data = await res.json();
  if (!Array.isArray(data)) {
    throw new Error((data as { error?: string }).error || "Invalid scenarios response");
  }
  return data;
}

export async function fetchSupervisorScenarios(): Promise<SupervisorScenario[]> {
  if (!SUPERVISOR) return [];
  const res = await fetch(`${getApiUrl()}/api/scenarios/supervisor`, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export async function fetchCallSupervisorHint(
  sessionId: string
): Promise<CallSupervisorHint | null> {
  if (!SUPERVISOR) return null;
  const res = await fetch(`${getApiUrl()}/api/calls/${encodeURIComponent(sessionId)}/supervisor`, {
    cache: "no-store",
  });
  if (!res.ok) return null;
  return res.json();
}

export function isSupervisorPanelEnabled(): boolean {
  return SUPERVISOR;
}

export async function fetchCallSession(sessionId: string): Promise<CallSessionDetail> {
  const res = await fetch(`${getApiUrl()}/api/calls/${encodeURIComponent(sessionId)}`, {
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to load call session (${res.status})`);
  }
  return res.json();
}

export async function endCallSession(sessionId: string): Promise<CallSessionDetail> {
  const res = await fetch(`${getApiUrl()}/api/calls/${encodeURIComponent(sessionId)}/end`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to end call session (${res.status})`);
  }
  return res.json();
}

export async function transcribeAudio(
  blob: Blob,
  lang: CallLang = "gujarati",
  sessionId?: string,
  filename = "reply.webm"
): Promise<string> {
  const form = new FormData();
  form.append("file", blob, filename);
  const q = new URLSearchParams({ lang });
  if (sessionId) q.set("sessionId", sessionId);
  const res = await fetch(`${getApiUrl()}/api/stt?${q}`, { method: "POST", body: form });
  if (!res.ok) {
    throw new Error(`STT error ${res.status}`);
  }
  const data = await res.json();
  return (data.transcript as string) || "";
}

export async function startDemo(
  accountId: string,
  lang: CallLang = "gujarati"
): Promise<{
  sessionId: string;
  callLang?: string;
  maskedAcct?: string;
}> {
  const res = await fetch(
    `${getApiUrl()}/api/demo/start?accountId=${encodeURIComponent(accountId)}&lang=${encodeURIComponent(lang)}`,
    { method: "POST" }
  );
  const data = await res.json();
  if (!res.ok || data.error) {
    throw new Error(data.error || `Start failed (${res.status})`);
  }
  return data;
}

export { last4FromMasked } from "@/lib/format";
