"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { CustomerQueueRow } from "@/components/dashboard/CustomerQueueRow";
import { SupervisorOnlyLast4 } from "@/components/SupervisorOnlyLast4";
import { savePendingCallContext } from "@/lib/callContext";
import {
  fetchHealth,
  fetchScenarios,
  fetchSupervisorScenarios,
  isSupervisorPanelEnabled,
  startDemo,
  type CallLang,
  type Scenario,
  type SupervisorScenario,
} from "@/lib/api";
import { formatAccountEnding } from "@/lib/format";
import {
  countByIssue,
  filterScenarios,
  ISSUE_FILTERS,
  type IssueFilter,
} from "@/lib/scenarios";
import {
  dossierImpacted,
  dossierOutreachObjective,
  dossierTotalBalance,
  type DossierScenario,
} from "@/lib/dossierSummary";
import "./dashboard.css";

/* ── Helper functions ──────────────────────────────────────── */

function issueCount(scenarios: Scenario[], id: IssueFilter) {
  if (id === "FREEZE")
    return scenarios.filter(
      (s) => s.primaryIssue === "DEBIT_FREEZE" || s.primaryIssue === "FREEZE"
    ).length;
  return countByIssue(scenarios, id);
}

function issueLabel(issue: string) {
  const m: Record<string, string> = {
    CHEQUE_BOUNCE: "Cheque Bounce",
    LIEN: "Tax Lien",
    HOLD: "Payment Hold",
    DEBIT_FREEZE: "Debit Freeze",
    FREEZE: "Debit Freeze",
    INOPERATIVE: "Inoperative Account",
  };
  return m[issue] || issue.replace(/_/g, " ");
}

function getIssueDotColor(issue: string = ""): string {
  const u = issue.toUpperCase();
  if (u.includes("BOUNCE")) return "#7c3aed";
  if (u.includes("LIEN"))   return "#d97706";
  if (u.includes("HOLD"))   return "#e11d48";
  if (u.includes("FREEZE")) return "#2563eb";
  if (u.includes("INOP"))   return "#64748b";
  return "#059669";
}

function getInitials(name = ""): string {
  const parts = name.trim().split(" ");
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : name.slice(0, 2).toUpperCase() || "??";
}

/* ── Mini icons ────────────────────────────────────────────── */

function SearchIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
    </svg>
  );
}

function ShieldCheckIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2" strokeLinecap="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}

function PhoneIcon() {
  return (
    <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.4 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.5a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 21.38 16c.04.308.06.617.06.92z" />
    </svg>
  );
}

/* ── Skeleton row ──────────────────────────────────────────── */

function RowSkeleton() {
  return (
    <div className="queue-row queue-row--skeleton">
      <div className="queue-row__cells">
        <div className="queue-row__customer-block">
          <div className="skeleton-box" style={{ width: 36, height: 36, borderRadius: 8 }} />
          <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 6 }}>
            <div className="skeleton-box" style={{ height: 13, width: "55%" }} />
            <div className="skeleton-box" style={{ height: 10, width: "38%" }} />
          </div>
        </div>
        <div>
          <div className="skeleton-box" style={{ height: 12, width: "60%", marginBottom: 4 }} />
          <div className="skeleton-box" style={{ height: 10, width: "80%" }} />
        </div>
        <div>
          <div className="skeleton-box" style={{ height: 32, width: 120, borderRadius: 6 }} />
        </div>
      </div>
    </div>
  );
}

/* ── Main Page Component ───────────────────────────────────── */

export default function DashboardPage() {
  const [scenarios, setScenarios] = useState<(Scenario | SupervisorScenario)[]>([]);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<IssueFilter>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [online, setOnline] = useState(true);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const supervisorDetails = isSupervisorPanelEnabled();

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const health = await fetchHealth();
        if (!health.ok) {
          setOnline(false);
          setError(`API error: ${health.detail ?? "database unreachable"}`);
          return;
        }
        setOnline(true);
        setError(null);
        if (supervisorDetails) {
          const sup = await fetchSupervisorScenarios();
          setScenarios(sup.length > 0 ? sup : await fetchScenarios());
        } else {
          setScenarios(await fetchScenarios());
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        console.error("[Dashboard] fetch failed:", msg);
        setOnline(false);
        setError(`Connection error: ${msg}`);
      } finally {
        setLoading(false);
      }
    })();
  }, [supervisorDetails]);


  const onStart = useCallback(
    async (accountId: string, lang: CallLang) => {
      setLoadingId(accountId);
      setError(null);
      const row = scenarios.find((s) => s.accountId === accountId);
      try {
        const { sessionId } = await startDemo(accountId, lang);
        savePendingCallContext({
          accountId,
          customerName: row?.customerName,
          maskedAcct: row?.maskedAcct,
          primaryIssue: row?.primaryIssue,
          callLang: lang,
        });
        window.location.assign(`/call/${sessionId}?lang=${encodeURIComponent(lang)}`);
      } catch {
        setError("Unable to start the call. Check backend connection.");
        setLoadingId(null);
      }
    },
    [scenarios]
  );

  const filtered = useMemo(
    () => filterScenarios(scenarios, filter, searchQuery),
    [scenarios, filter, searchQuery]
  );

  useEffect(() => {
    if (filtered.length === 0) { setSelectedId(null); return; }
    if (!selectedId || !filtered.some((s) => s.accountId === selectedId)) {
      setSelectedId(filtered[0].accountId);
    }
  }, [filtered, selectedId]);

  const selected = filtered.find((s) => s.accountId === selectedId) || null;
  const selectedDossier = selected as DossierScenario | null;
  const selectedImpacted = useMemo(
    () => (selectedDossier ? dossierImpacted(selectedDossier) : null),
    [selectedDossier]
  );
  const selectedMasked = selected
    ? formatAccountEnding({
        maskedAcct: selected.maskedAcct || (selected as SupervisorScenario).maskedAcct,
        accountId: selected.accountId,
      }) || "—"
    : "—";
  const filterCount = (id: IssueFilter) =>
    id === "ALL" ? scenarios.length : issueCount(scenarios, id);

  const total   = scenarios.length;
  const ready   = scenarios.length;
  const active  = loadingId ? 1 : 0;

  return (
    <AppShell>
      <div className="ops-page">

        {/* ── TOP HEADER STRIP ──────────────────────────────────── */}
        <div className="ops-header-strip">
          <div className="ops-header-strip__inner">
            <div className="ops-header-strip__left">
              <div className="ops-breadcrumb">
                <span>Sahayak Operations</span>
                <span className="ops-breadcrumb__sep">/</span>
                <span className="ops-breadcrumb__current">Outreach Queue</span>
              </div>
              <h1 className="ops-page__title">Outbound RM Console</h1>
            </div>

            <div className="ops-kpi-row">
              <div className="ops-kpi-cell">
                <span className="ops-kpi-cell__val">{loading ? "—" : total}</span>
                <span className="ops-kpi-cell__label">Queue</span>
              </div>
              <div className="ops-kpi-cell">
                <span className="ops-kpi-cell__val ops-kpi-cell__val--green">{loading ? "—" : ready}</span>
                <span className="ops-kpi-cell__label">Ready</span>
              </div>
              <div className="ops-kpi-cell">
                <span className="ops-kpi-cell__val ops-kpi-cell__val--amber">{active}</span>
                <span className="ops-kpi-cell__label">In Call</span>
              </div>
              <div className="ops-kpi-cell">
                <span className="ops-kpi-cell__val ops-kpi-cell__val--blue">
                  {supervisorDetails ? "SUPERVISOR" : "STANDARD"}
                </span>
                <span className="ops-kpi-cell__label">Protocol</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── BANNERS ───────────────────────────────────────────── */}
        {!online && (
          <p className="ops-page__offline" role="status">
            ⚠ Backend unreachable — check Postgres and API status.
          </p>
        )}
        {error && <div className="alert-error">{error}</div>}

        {/* ── MAIN WORKSPACE (FULL HEIGHT DATA TABLE + DOSSIER) ─────── */}
        <div className="ops-body">

          {/* Left / Main Table Column */}
          <div className="ops-main-col">

            {/* Filter Toolbar */}
            <div className="ops-toolbar-bar">
              <div className="ops-search">
                <span className="ops-search__icon"><SearchIcon /></span>
                <input
                  type="search"
                  placeholder="Filter name, account, issue…"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {searchQuery && (
                  <button
                    type="button"
                    className="ops-search__clear"
                    onClick={() => setSearchQuery("")}
                  >×</button>
                )}
              </div>

              <div className="ops-filters" role="tablist">
                {ISSUE_FILTERS.map(({ id, label }) => (
                  <button
                    key={id}
                    type="button"
                    role="tab"
                    aria-selected={filter === id}
                    className={`ops-filter ${filter === id ? "ops-filter--on" : ""}`}
                    onClick={() => setFilter(id)}
                  >
                    {label}
                    <span className="ops-filter__n">{filterCount(id)}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* High Density Customer Data Table */}
            <div className="queue-table">
              <div className="queue-table__head">
                <span>Customer &amp; Account</span>
                <span>Status</span>
                <span>Launch Voice Session</span>
              </div>

              {loading ? (
                Array.from({ length: 6 }).map((_, i) => <RowSkeleton key={i} />)
              ) : filtered.length === 0 ? (
                <div className="dash-empty">
                  <h3>No customers match this filter.</h3>
                  <p>Try resetting your search query or filter selection.</p>
                  <button
                    type="button"
                    className="btn-secondary-sm"
                    onClick={() => { setFilter("ALL"); setSearchQuery(""); }}
                  >
                    Reset Filters
                  </button>
                </div>
              ) : (
                filtered.map((s) => (
                  <CustomerQueueRow
                    key={s.accountId}
                    scenario={s}
                    busy={loadingId === s.accountId}
                    selected={selectedId === s.accountId}
                    onSelect={() => setSelectedId(s.accountId)}
                    onCall={onStart}
                  />
                ))
              )}
            </div>

          </div>

          {/* Dossier Side Column (Right) */}
          <div className="ops-side-col">
            {!selected || loading ? (
              <div className="ops-dossier__none">
                Select a customer from the queue to view their active dossier.
              </div>
            ) : (
              <div className="ops-dossier">
                {/* Header */}
                <div className="dossier-header">
                  <div className="dossier-eyebrow">Active Account Dossier</div>
                  <div className="dossier-identity">
                    <div className="dossier-avatar">
                      {getInitials(selected.customerName)}
                    </div>
                    <div className="dossier-name-block">
                      <div className="dossier-name">{selected.customerName || "Customer"}</div>
                      <div className="dossier-acct">
                        <span className="dossier-acct-num">{selectedMasked}</span>
                        <span className="q-badge">
                          <span
                            className="q-badge__dot"
                            style={{ backgroundColor: getIssueDotColor(selected.primaryIssue) }}
                          />
                          <span>{issueLabel(selected.primaryIssue || "")}</span>
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Ledger Financial Summary */}
                <div className="dossier-section">
                  <div className="dossier-section__label">Account Ledger Summary</div>
                  <div className="ledger-grid">
                    <div className="ledger-card">
                      <span className="ledger-card__title">Total Balance</span>
                      <span className="ledger-card__val">
                        {selectedDossier ? dossierTotalBalance(selectedDossier) : "—"}
                      </span>
                    </div>
                    <div className="ledger-card">
                      <span className="ledger-card__title">
                        {selectedImpacted?.title ?? "Impacted amount"}
                      </span>
                      <span className="ledger-card__val ledger-card__val--amber">
                        {selectedImpacted?.value ?? "—"}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Why this outreach call */}
                <div className="dossier-section">
                  <div className="dossier-section__label">Outreach Guidance &amp; Objective</div>
                  <div className="dossier-why-card">
                    {selectedDossier
                      ? dossierOutreachObjective(selectedDossier)
                      : "—"}
                  </div>
                </div>

                {/* Mandatory Identity Auth Gate */}
                <div className="dossier-section">
                  <div className="dossier-rule-card">
                    <div className="dossier-rule-card__icon">
                      <ShieldCheckIcon />
                    </div>
                    <div className="dossier-rule-card__body">
                      <div className="dossier-rule-card__title">Mandatory Auth Gate</div>
                      <p className="dossier-rule-card__desc">
                        Voice AI verifies last-4 digits before disclosing any ledger data. Hard-gated.
                      </p>
                    </div>
                  </div>

                  {supervisorDetails && (selected as SupervisorScenario).expectedLast4 && (
                    <div style={{ marginTop: "10px" }}>
                      <SupervisorOnlyLast4 digits={(selected as SupervisorScenario).expectedLast4!} />
                    </div>
                  )}
                </div>

                {/* Preferred Dialect */}
                <div className="dossier-section">
                  <div className="dossier-section__label">Customer Preferred Language</div>
                  <div className="dossier-lang">
                    <span style={{ fontSize: 14 }}>🇮🇳</span>
                    <span style={{ fontWeight: 600 }}>
                      Gujarati (ગુજરાતી)
                    </span>
                  </div>
                </div>

                {/* Launch Call Widget */}
                <div className="dossier-launch">
                  <div className="dossier-launch__label">Initiate Outbound Voice Call</div>
                  <div className="dossier-launch__btns">
                    <button
                      type="button"
                      className="dossier-launch__btn dossier-launch__btn--primary"
                      disabled={!!loadingId}
                      onClick={() => onStart(selected.accountId, "gujarati")}
                    >
                      <PhoneIcon />
                      <span>Launch Outbound Call (Gujarati)</span>
                    </button>
                  </div>
                  {loadingId === selected.accountId && (
                    <p className="dossier-launch__busy">Connecting outbound channel…</p>
                  )}
                </div>

              </div>
            )}
          </div>

        </div>

      </div>
    </AppShell>
  );
}
