/** Display helpers for dashboard & call UI */

export function formatInr(amount: number | undefined | null): string {
  if (amount === undefined || amount === null || Number.isNaN(amount)) return "—";
  return `₹${amount.toLocaleString("en-IN")}`;
}

/** Returns null when amount is missing (for hiding empty UI rows). */
export function formatInrOptional(amount: number | undefined | null): string | null {
  if (amount === undefined || amount === null || Number.isNaN(amount)) return null;
  return formatInr(amount);
}

export function customerInitials(name: string | undefined): string {
  return (name || "CU")
    .split(/\s+/)
    .filter(Boolean)
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

export function last4FromMasked(masked: string): string {
  return masked.replace(/\D/g, "").slice(-4);
}

/** Normalize masked account strings (XXXX7294 → last4 only for parsing). */
export function accountLast4FromSources(opts: {
  maskedAcct?: string | null;
  maskedLast4?: string | null;
  accountId?: string | null;
}): string | null {
  const fromMasked = opts.maskedAcct ? last4FromMasked(opts.maskedAcct) : "";
  if (fromMasked.length === 4) return fromMasked;
  const ml = (opts.maskedLast4 || "").replace(/\D/g, "");
  if (ml.length === 4) return ml;
  const fromId = (opts.accountId || "").replace(/\D/g, "").slice(-4);
  if (fromId.length === 4) return fromId;
  return null;
}

/** Operator-facing account ending — never uses verification secrets. */
export function formatAccountEnding(opts: {
  maskedAcct?: string | null;
  maskedLast4?: string | null;
  accountId?: string | null;
}): string | null {
  const last4 = accountLast4FromSources(opts);
  if (!last4) return null;
  const raw = (opts.maskedAcct || "").trim();
  if (raw && /[•·*]/.test(raw)) {
    return raw.replace(/X{4}/gi, "••••").replace(/\s+/g, " ");
  }
  return `•••• ${last4}`;
}
