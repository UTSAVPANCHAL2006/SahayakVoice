"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/AppShell";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function CasePage() {
  const params = useParams();
  const caseRef = params.id as string;
  const [data, setData] = useState<Record<string, string> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API}/api/cases/${caseRef}`)
      .then((r) => r.json())
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [caseRef]);

  return (
    <AppShell>
      <Link href="/dashboard" className="back-link">
        ← Back to console
      </Link>

      <header className="case-page-header">
        <h1>Case</h1>
        <p className="case-page-header__ref">{caseRef}</p>
        <p className="case-page-header__sub">Resolution record from voice session</p>
      </header>

      {loading ? (
        <p className="case-page-muted">Loading case details…</p>
      ) : data?.error ? (
        <div className="alert-error">Case {caseRef} not found.</div>
      ) : (
        <dl className="case-detail-grid">
          <div>
            <dt>State</dt>
            <dd className="case-detail-grid__emphasis">{data?.state || "OPEN"}</dd>
          </div>
          <div>
            <dt>Account</dt>
            <dd className="case-detail-grid__mono">{data?.accountId || "—"}</dd>
          </div>
          <div>
            <dt>Voice session</dt>
            <dd className="case-detail-grid__mono case-detail-grid__break">{data?.sessionId || "—"}</dd>
          </div>
          <div>
            <dt>Last updated</dt>
            <dd>{data?.updatedAt || "—"}</dd>
          </div>
        </dl>
      )}
    </AppShell>
  );
}
