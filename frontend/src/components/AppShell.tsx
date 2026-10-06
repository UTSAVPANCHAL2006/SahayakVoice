"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Props = { children: React.ReactNode };

function BrandIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5" />
      <path d="M2 12l10 5 10-5" />
    </svg>
  );
}

function HomeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
      <polyline points="9 22 9 12 15 12 15 22" />
    </svg>
  );
}

function QueueIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <rect x="3" y="4" width="18" height="3" rx="1" />
      <rect x="3" y="10.5" width="18" height="3" rx="1" />
      <rect x="3" y="17" width="18" height="3" rx="1" />
    </svg>
  );
}

function PhoneIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.4 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.5a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 21.38 16c.04.308.06.617.06.92z" />
    </svg>
  );
}

export function AppShell({ children }: Props) {
  const path = usePathname();
  const isLiveCall = path?.startsWith("/call");
  const callId = isLiveCall ? path?.split("/")[2] : null;

  return (
    <div className="shell">
      <aside className="sidebar" aria-label="Navigation">
        {/* Brand Header */}
        <Link href="/" className="brand">
          <div className="brand-icon-box">
            <BrandIcon />
          </div>
          <div>
            <div className="brand-title">Sahayak Voice</div>
            <div className="brand-sub">RM Console</div>
          </div>
        </Link>

        {/* Clean, sleek navigation list */}
        <div className="sidebar-nav-group">
          <nav className="sidebar-nav" aria-label="Main navigation">
            <Link
              href="/"
              className={`nav-link ${path === "/" ? "active" : ""}`}
            >
              <HomeIcon />
              <span>Overview</span>
            </Link>

            <Link
              href="/dashboard"
              className={`nav-link ${path === "/dashboard" ? "active" : ""}`}
              aria-current={path === "/dashboard" ? "page" : undefined}
            >
              <QueueIcon />
              <span>Outreach Queue</span>
            </Link>

            {isLiveCall && callId && (
              <Link href={`/call/${callId}`} className="nav-link active" aria-current="page">
                <PhoneIcon />
                <span>Live Call Session</span>
                <span className="live-indicator-dot" aria-label="Call active" />
              </Link>
            )}
          </nav>
        </div>

      </aside>

      <main className={`main ${isLiveCall ? "main--workbench" : "main--ops"}`}>
        {children}
      </main>
    </div>
  );
}
