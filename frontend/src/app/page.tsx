"use client";

import Link from "next/link";
import { useState } from "react";
import "./home.css";

type CaseKey = "CHEQUE_BOUNCE" | "LIEN" | "HOLD" | "DEBIT_FREEZE" | "INOPERATIVE";

interface CaseDemo {
  key: CaseKey;
  label: string;
  customerName: string;
  accountId: string;
  maskedAcct: string;
  balance: string;
  blockedAmount: string;
  issueBadge: string;
  triggerEvent: string;
  actionRequired: string;
  dialogue: { speaker: "sahayak" | "customer"; text: string; time: string }[];
}

const DEMO_CASES: Record<CaseKey, CaseDemo> = {
  CHEQUE_BOUNCE: {
    key: "CHEQUE_BOUNCE",
    label: "Cheque Bounce",
    customerName: "Hardik Patel",
    accountId: "ACC-CHQ-HARDIK",
    maskedAcct: "•••• 7294",
    balance: "₹68,674",
    blockedAmount: "₹523 charge",
    issueBadge: "CTS Return #123456",
    triggerEvent: "Cheque returned unpaid due to insufficient funds (CTS Code 01).",
    actionRequired: "Deposit funds within 24h or issue fresh UPI/cheque payment to payee.",
    dialogue: [
      {
        speaker: "sahayak",
        time: "0:02",
        text: "નમસ્કાર Hardikભાઈ, હું સહાયક બેંકમાંથી બોલું છું. ખાતાની સુરક્ષા ખાતર કૃપા કરીને તમારા ખાતાના છેલ્લા 4 આંકડા કન્ફર્મ કરશો?",
      },
      {
        speaker: "customer",
        time: "0:06",
        text: "હા, 7294 છે.",
      },
      {
        speaker: "sahayak",
        time: "0:09",
        text: "આભાર Hardikભાઈ. તમારા ખાતામાંથી ₹12,500 નો ચેક બેલેન્સ ઓછું હોવાથી રિટર્ન થયો છે અને નિયમ મુજબ ₹523 નો ચાર્જ લાગ્યો છે.",
      },
      {
        speaker: "customer",
        time: "0:14",
        text: "aatlo badho charge kem lagyo? mane pelathi call na karvo joiye?",
      },
      {
        speaker: "sahayak",
        time: "0:19",
        text: "Hardikભાઈ, ₹523 નો ચાર્જ બેંકની સ્ટાન્ડર્ડ ક્લિયરિંગ રિટર્ન પોલિસી મુજબ ઓટો-ડેબિટ થયો છે. જો તમે આજે જરૂરી રકમ જમા કરી દો, તો પેઈને UPI અથવા નવો ચેક આપી શકો છો.",
      },
    ],
  },
  LIEN: {
    key: "LIEN",
    label: "Tax Lien",
    customerName: "Pratik Sharma",
    accountId: "ACC-LIEN-PRIYA",
    maskedAcct: "•••• 4521",
    balance: "₹52,783",
    blockedAmount: "₹38,419 Lien",
    issueBadge: "IT-ATTACH-2026-8891",
    triggerEvent: "Income Tax Department Section 226(3) attachment order received.",
    actionRequired: "Clear funds are ₹14,364. Lien removal requires IT Department revocation order.",
    dialogue: [
      {
        speaker: "sahayak",
        time: "0:02",
        text: "નમસ્કાર Pratikભાઈ, સહાયક બેંકમાંથી ઇન્કમ ટેક્સ લિયન નોટિસ સંદર્ભે વાત કરવી છે. સુરક્ષા ખાતર છેલ્લા 4 આંકડા કન્ફર્મ કરશો?",
      },
      {
        speaker: "customer",
        time: "0:05",
        text: "4521 છે.",
      },
      {
        speaker: "sahayak",
        time: "0:08",
        text: "આભાર. ઇન્કમ ટેક્સ ઓર્ડર હેઠળ ₹38,419 લિયન તરીકે હોલ્ડ થયા છે. આજે તમારું ક્લિયર ઉપલબ્ધ બેલેન્સ ₹14,364 છે.",
      },
      {
        speaker: "customer",
        time: "0:13",
        text: "mare ketla paisa use karva male? badhu account bandh che?",
      },
      {
        speaker: "sahayak",
        time: "0:18",
        text: "ના Pratikભાઈ, ખાતું ચાલુ છે. તમે પૂરા ₹14,364 ઉપાડી અથવા ટ્રાન્સફર કરી શકો છો. ₹38,419 નો હોલ્ડ હટાવવા ટેક્સ વિભાગમાંથી રિવોકેશન ઓર્ડર જરૂરી છે.",
      },
    ],
  },
  HOLD: {
    key: "HOLD",
    label: "Payment Hold",
    customerName: "Amit Singh",
    accountId: "ACC-HOLD-AMIT",
    maskedAcct: "•••• 5619",
    balance: "₹34,920",
    blockedAmount: "₹18,500 Hold",
    issueBadge: "UPI-REF-8829104",
    triggerEvent: "Interbank UPI settlement pending verification at NPCI clearing house.",
    actionRequired: "Do not initiate duplicate transaction; funds will settle within 24-48 hours.",
    dialogue: [
      {
        speaker: "sahayak",
        time: "0:02",
        text: "નમસ્કાર Amitભાઈ, તમારા એકાઉન્ટમાં ₹18,500 ના પેન્ડિંગ ટ્રાન્ઝેક્શન હોલ્ડ બાબતે સંપર્ક કર્યો છે.",
      },
      {
        speaker: "customer",
        time: "0:06",
        text: "mara paisa kya che? fari payment karu? dukandar pase nathi pahochya.",
      },
      {
        speaker: "sahayak",
        time: "0:11",
        text: "Amitભાઈ, તમારા પૈસા બેંકમાં સંપૂર્ણ સુરક્ષિત છે. ટ્રાન્ઝેક્શન બેંક ક્લિયરિંગમાં હોવાથી ફરીથી પેમેન્ટ ન કરશો. 24 થી 48 કલાકમાં વેન્ડર ખાતામાં અપડેટ થઈ જશે.",
      },
    ],
  },
  DEBIT_FREEZE: {
    key: "DEBIT_FREEZE",
    label: "Debit Freeze",
    customerName: "Vikram Shah",
    accountId: "ACC-FRZ-VIKRAM",
    maskedAcct: "•••• 8471",
    balance: "₹1,15,400",
    blockedAmount: "Full Debit Lock",
    issueBadge: "FRZ-SEC-2026-1180",
    triggerEvent: "Cyber Crime Cell / AML compliance notice requiring in-person Re-KYC.",
    actionRequired: "Inward credits allowed; debits locked until original KYC verification at home branch.",
    dialogue: [
      {
        speaker: "sahayak",
        time: "0:02",
        text: "નમસ્કાર Vikramભાઈ, સહાયક બેંકમાંથી બોલું છું. તમારા ખાતા પર ડેબિટ ફ્રીઝ સંદર્ભે જરૂરી માહિતી આપવા સંપર્ક કર્યો છે.",
      },
      {
        speaker: "customer",
        time: "0:07",
        text: "km freeze thyu? mara ATM mathi paisa nikadse? mare urgent payment karvu che.",
      },
      {
        speaker: "sahayak",
        time: "0:12",
        text: "Vikramભાઈ, સાયબર સેલ નિર્દેશ હેઠળ ડેબિટ વ્યવહારો સ્થગિત કરાયા છે. એટીએમ અને યુપીઆઈ હાલ બંધ રહેશે. શાખામાં કેવાયસી ડોક્યુમેન્ટ્સ સબમિટ કરીને અનફ્રીઝ કરાવી શકો છો.",
      },
    ],
  },
  INOPERATIVE: {
    key: "INOPERATIVE",
    label: "Inoperative Account",
    customerName: "Rahul Patel",
    accountId: "ACC-INOP-RAHUL",
    maskedAcct: "•••• 9043",
    balance: "₹8,450",
    blockedAmount: "Dormant Status",
    issueBadge: "RBI-DORMANT-2Y",
    triggerEvent: "Account inactive for 24+ months without customer-induced transaction.",
    actionRequired: "Submit fresh PAN, Aadhaar, and biometric Re-KYC form at any branch.",
    dialogue: [
      {
        speaker: "sahayak",
        time: "0:02",
        text: "નમસ્કાર Rahulભાઈ, તમારા ખાતામાં ૨ વર્ષથી કોઈ વ્યવહાર ન હોવાથી RBI માર્ગદર્શિકા મુજબ ખાતું ઇનઓપરેટિવ થયું છે.",
      },
      {
        speaker: "customer",
        time: "0:08",
        text: "chalu karava su karvu? branch javu padse ke online thase?",
      },
      {
        speaker: "sahayak",
        time: "0:13",
        text: "Rahulભાઈ, કોઈપણ શાખામાં પાન કાર્ડ અને આધાર કાર્ડ સાથે રુબરુ Re-KYC ફોર્મ સબમિટ કરશો એટલે ખાતું 24 કલાકમાં વગર કોઈ પેનલ્ટીએ ફરી સક્રિય થઈ જશે.",
      },
    ],
  },
};

const DIALECT_EXAMPLES = [
  {
    query: "mare manager sathe vat krvi che",
    tag: "Manager Escalation",
    resp: "Warm handoff to human branch RM console with full call transcript",
    badge: "Instant Transfer",
  },
  {
    query: "aatlo badho charge kem lagyo?",
    tag: "Fee Objection",
    resp: "Breaks down ₹523 bounce charge and explains balance replenishment",
    badge: "Policy Grounded",
  },
  {
    query: "mara paisa kya che? fari payment karu?",
    tag: "Fund Safety Assurance",
    resp: "Reassures funds are held in clearing; prevents duplicate UPI debit",
    badge: "Zero Double-Debit",
  },
  {
    query: "km freeze thyu? ATM mathi nikadse?",
    tag: "KYC Restrictions",
    resp: "Explains cyber cell / Re-KYC restriction and branch unfreeze protocol",
    badge: "RBI Compliant",
  },
];

export default function HomePage() {
  const [activeCase, setActiveCase] = useState<CaseKey>("CHEQUE_BOUNCE");
  const currentDemo = DEMO_CASES[activeCase];

  return (
    <div className="home-page">
      <div className="home-backdrop" />
      <div className="home-grid-pattern" />

      <div className="home-wrap">
        {/* Navigation Bar */}
        <header className="home-nav">
          <div className="home-nav-inner">
            <Link href="/" className="home-brand">
              <div className="home-brand-icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z" />
                  <path d="M2 17l10 5 10-5" />
                  <path d="M2 12l10 5 10-5" />
                </svg>
              </div>
              <div className="home-brand-text">Sahayak Voice</div>
            </Link>

            <nav className="home-nav-links">
              <a href="#scenarios" className="home-nav-link">Scenarios</a>
              <a href="#comparison" className="home-nav-link">Why Sahayak</a>
              <a href="#pipeline" className="home-nav-link">State Machine</a>
              <a href="#dialect" className="home-nav-link">Dialects</a>
            </nav>

            <div className="home-nav-actions">
              <Link href="/dashboard" className="home-cta-btn">
                <span>Launch RM Console</span>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </Link>
            </div>
          </div>
        </header>

        {/* Hero Section */}
        <section className="home-hero">
          <div className="home-hero-grid">
            <div className="home-hero-content">
              <div className="home-badge-pill">
                <span className="home-badge-dot" />
                <span>AUTONOMOUS OUTBOUND BANKING VOICE AGENT</span>
              </div>

              <h1 className="home-hero-title">
                Intelligent Outbound Banking Care <span className="home-hero-title-highlight">in Native Voice.</span>
              </h1>

              <p className="home-hero-desc">
                The next-generation outbound AI agent for Indian banking. Speaks natural colloquial <strong>Gujarati</strong>, grounded directly in core banking databases, ensuring every balance, fee, and timeline is accurate and compliant.
              </p>

              <div className="home-hero-actions">
                <Link href="/dashboard" className="home-cta-btn home-cta-btn--lg">
                  <span>Open RM Console</span>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </Link>
                <a href="#scenarios" className="home-secondary-btn">
                  <span>Explore Banking Scenarios</span>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M19 9l-7 7-7-7" />
                  </svg>
                </a>
              </div>

              {/* Key Metrics Strip */}
              <div className="home-hero-stats">
                <div className="home-stat-item">
                  <div className="home-stat-val">100%</div>
                  <div className="home-stat-label">Hard-Gated Last-4</div>
                </div>
                <div className="home-stat-item">
                  <div className="home-stat-val">5 Scenarios</div>
                  <div className="home-stat-label">Core Bank Seeded</div>
                </div>
                <div className="home-stat-item">
                  <div className="home-stat-val">0.0%</div>
                  <div className="home-stat-label">Pre-Auth Leakage</div>
                </div>
              </div>
            </div>

            {/* Hero Live Simulator Terminal */}
            <div className="home-terminal-card" id="simulator">
              <div className="home-terminal-header">
                <div className="home-terminal-title">
                  <span className="window-dot" />
                  <span className="window-dot" />
                  <span className="window-dot" />
                  <span className="window-title-text">LIVE OUTBOUND SIMULATOR</span>
                </div>
                <div className="home-live-tag">
                  <span className="home-badge-dot" />
                  <span>GUJARATI ONLY</span>
                </div>
              </div>

              {/* Case Selector Tabs */}
              <div className="home-case-selector">
                {(Object.keys(DEMO_CASES) as CaseKey[]).map((key) => (
                  <button
                    key={key}
                    className={`home-case-tab ${activeCase === key ? "active" : ""}`}
                    onClick={() => setActiveCase(key)}
                  >
                    {DEMO_CASES[key].label}
                  </button>
                ))}
              </div>

              {/* Customer Strip */}
              <div className="home-client-strip">
                <div className="home-client-left">
                  <div className="home-client-avatar">
                    {currentDemo.customerName
                      .split(" ")
                      .map((n) => n[0])
                      .join("")}
                  </div>
                  <div>
                    <div className="home-client-name">{currentDemo.customerName}</div>
                    <div className="home-client-meta">
                      {currentDemo.issueBadge} · {currentDemo.maskedAcct}
                    </div>
                  </div>
                </div>
                <div className="home-verified-pill">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>Last-4 Verified</span>
                </div>
              </div>

              {/* Dynamic Audio Waves Indicator */}
              <div className="audio-wave-strip">
                <span className="wave-label">SARVAM VOICE SYNTHESIS · 16KHZ STREAM</span>
                <div className="wave-bars">
                  <span className="bar" />
                  <span className="bar" />
                  <span className="bar" />
                  <span className="bar" />
                  <span className="bar" />
                  <span className="bar" />
                </div>
              </div>

              {/* Transcript Stream */}
              <div className="home-transcript-stream">
                {currentDemo.dialogue.map((item, idx) => (
                  <div key={idx} className={`home-chat-bubble ${item.speaker}`}>
                    <div className="home-chat-speaker">
                      <span>{item.speaker === "sahayak" ? "Sahayak Voice AI" : currentDemo.customerName}</span>
                      <span className="home-chat-time">{item.time}</span>
                    </div>
                    <div className="home-chat-text">{item.text}</div>
                  </div>
                ))}
              </div>

              {/* Terminal Footer Metrics */}
              <div className="home-terminal-footer">
                <div className="home-footer-metric">
                  <div className="home-footer-label">Ledger Balance</div>
                  <div className="home-footer-val">{currentDemo.balance}</div>
                </div>
                <div className="home-footer-metric">
                  <div className="home-footer-label">Status Impact</div>
                  <div className="home-footer-val">{currentDemo.blockedAmount}</div>
                </div>
                <div className="home-footer-metric">
                  <div className="home-footer-label">Fact Guard</div>
                  <div className="home-footer-val">✓ Hardware Grounded</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── SECTION: 5 Seeded Core Banking Scenarios In-Depth ────────────── */}
        <section className="home-section" id="scenarios">
          <div className="home-section-header">
            <span className="home-section-tag">CORE BANKING DOMAIN COVERAGE</span>
            <h2 className="home-section-title">Five Seeded Account-Status Scenarios</h2>
            <p className="home-section-desc">
              Sahayak Voice is pre-configured with complete core banking schemas, statutory notice templates, and realistic Indian retail scenarios.
            </p>
          </div>

          <div className="home-scenario-grid">
            <div className="home-scenario-card">
              <div className="home-scenario-card__head">
                <span className="home-scenario-card__code">ACC-CHQ-HARDIK</span>
                <span className="badge-tag-warn">Cheque Bounce</span>
              </div>
              <div className="home-scenario-card__title">Inward CTS Cheque Return</div>
              <p className="home-scenario-card__desc">
                Informs customer of returned cheque #123456 due to insufficient funds (CTS Code 01), explains the ₹523 return charge, and details options to replenish balance or issue UPI/fresh cheque.
              </p>
              <div className="home-scenario-card__meta">
                <span>Hold: ₹523 Fee</span>
                <span>Dialect: Gujarati</span>
              </div>
            </div>

            <div className="home-scenario-card">
              <div className="home-scenario-card__head">
                <span className="home-scenario-card__code">ACC-LIEN-PRIYA</span>
                <span className="badge-tag-warn">Tax Lien</span>
              </div>
              <div className="home-scenario-card__title">Statutory IT Attachment Notice</div>
              <p className="home-scenario-card__desc">
                Explains ₹38,419 statutory tax lien attachment under Section 226(3), reassures the customer of their ₹14,364 usable clear balance, and provides Income Tax release order submission procedures.
              </p>
              <div className="home-scenario-card__meta">
                <span>Hold: ₹38,419 Lien</span>
                <span>Dialect: Gujarati</span>
              </div>
            </div>

            <div className="home-scenario-card">
              <div className="home-scenario-card__head">
                <span className="home-scenario-card__code">ACC-HOLD-AMIT</span>
                <span className="badge-tag-warn">Payment Hold</span>
              </div>
              <div className="home-scenario-card__title">UPI / Interbank Clearing Hold</div>
              <p className="home-scenario-card__desc">
                Clarifies that ₹18,500 pending transfer is held in clearing house verification and strictly prevents the customer from initiating duplicate payments during the 24-48h settlement window.
              </p>
              <div className="home-scenario-card__meta">
                <span>Hold: ₹18,500 Pending</span>
                <span>Dialect: Gujarati</span>
              </div>
            </div>

            <div className="home-scenario-card">
              <div className="home-scenario-card__head">
                <span className="home-scenario-card__code">ACC-FRZ-VIKRAM</span>
                <span className="badge-tag-bad">Debit Freeze</span>
              </div>
              <div className="home-scenario-card__title">Cyber Cell / Re-KYC Freeze</div>
              <p className="home-scenario-card__desc">
                Informs customer of compliance/cyber cell directive restricting ATM and UPI debits without accusatory language, providing a clear branch document checklist to unfreeze the account.
              </p>
              <div className="home-scenario-card__meta">
                <span>Hold: Full Debit Lock</span>
                <span>Dialect: Gujarati</span>
              </div>
            </div>

            <div className="home-scenario-card">
              <div className="home-scenario-card__head">
                <span className="home-scenario-card__code">ACC-INOP-RAHUL</span>
                <span className="badge-tag-bad">Inoperative</span>
              </div>
              <div className="home-scenario-card__title">2-Year Dormant Account (RBI)</div>
              <p className="home-scenario-card__desc">
                Explains 24-month account inactivity under RBI circulars, reassures the customer that accumulated interest remains safe, and details instant in-person branch Re-KYC reactivation.
              </p>
              <div className="home-scenario-card__meta">
                <span>Hold: Dormant</span>
                <span>Dialect: Gujarati</span>
              </div>
            </div>

            <div className="home-scenario-card" style={{ background: "#fafafa" }}>
              <div className="home-scenario-card__head">
                <span className="home-scenario-card__code">SUPERVISOR HANDOFF</span>
                <span className="badge-tag-good">Warm Transfer</span>
              </div>
              <div className="home-scenario-card__title">Human Escalation Protocol</div>
              <p className="home-scenario-card__desc">
                Any customer request for senior management or complex dispute triggers a live warm transfer to the branch manager console with pre-verified session proof and audio transcript.
              </p>
              <div className="home-scenario-card__meta">
                <span>Trigger: Dispute / Request</span>
                <span>Audit: Full Transcript Proof</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── SECTION: Why Retail Banks Choose Sahayak (Comparison Table) ─── */}
        <section className="home-section" id="comparison">
          <div className="home-section-header">
            <span className="home-section-tag">THE ENTERPRISE ADVANTAGE</span>
            <h2 className="home-section-title">Why Banks Need Sahayak Over Legacy Systems</h2>
            <p className="home-section-desc">
              Traditional IVR dialers irritate customers and leak confidential data, while human relationship managers cannot scale to thousands of daily account status alerts.
            </p>
          </div>

          <div className="home-compare-wrap">
            <table className="home-compare-table">
              <thead>
                <tr>
                  <th>Operational Dimension</th>
                  <th>Legacy Robo-Callers / IVR</th>
                  <th>Human Branch Staff (RMs)</th>
                  <th className="highlight">Sahayak Voice (Autonomous RM)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="feature">Identity Authentication</td>
                  <td><span className="badge-tag-bad">✕ None / Unverified</span></td>
                  <td><span className="badge-tag-warn">⚠ Inconsistent Manual Check</span></td>
                  <td className="highlight"><span className="badge-tag-good">✓ 100% Hard-Gated Last-4</span></td>
                </tr>
                <tr>
                  <td className="feature">Pre-Auth Data Leakage</td>
                  <td><span className="badge-tag-bad">✕ Discloses Balance to Anyone</span></td>
                  <td><span className="badge-tag-warn">⚠ Risk of Social Engineering</span></td>
                  <td className="highlight"><span className="badge-tag-good">✓ 0.0% Pre-Auth Leakage</span></td>
                </tr>
                <tr>
                  <td className="feature">Dialect Comprehension</td>
                  <td><span className="badge-tag-bad">✕ Monotone Scripted English</span></td>
                  <td><span className="badge-tag-good">✓ Fluent Regional Dialect</span></td>
                  <td className="highlight"><span className="badge-tag-good">✓ Colloquial Gujarati Script &amp; Voice</span></td>
                </tr>
                <tr>
                  <td className="feature">Fact Accuracy &amp; Promises</td>
                  <td><span className="badge-tag-bad">✕ Static Recorded Audio</span></td>
                  <td><span className="badge-tag-warn">⚠ Unauthorized Fee Promises</span></td>
                  <td className="highlight"><span className="badge-tag-good">✓ Hardware Fact Guard Enforced</span></td>
                </tr>
                <tr>
                  <td className="feature">Turn-Taking Architecture</td>
                  <td><span className="badge-tag-bad">✕ Rigid Fixed IVR Menus</span></td>
                  <td><span className="badge-tag-warn">⚠ Ad-hoc Manual Routing</span></td>
                  <td className="highlight"><span className="badge-tag-good">✓ Hybrid: Template Fast-Path + LLM</span></td>
                </tr>
                <tr>
                  <td className="feature">Queue Automation</td>
                  <td>High Drop-off / Abandonment</td>
                  <td>Limited Daily Manual Bandwidth</td>
                  <td className="highlight"><strong>Automated Outbound Queue</strong></td>
                </tr>
                <tr>
                  <td className="feature">Dispute &amp; Handoff Path</td>
                  <td><span className="badge-tag-bad">✕ Dead End / Disconnects</span></td>
                  <td><span className="badge-tag-warn">⚠ Manual Ticket Creation</span></td>
                  <td className="highlight"><span className="badge-tag-good">✓ Instant Warm Transfer + Audit Proof</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* ── SECTION: 5-Stage Outbound State Machine Pipeline ─────────────── */}
        <section className="home-section" id="pipeline">
          <div className="home-section-header">
            <span className="home-section-tag">DETERMINISTIC STATE MACHINE</span>
            <h2 className="home-section-title">How Sahayak Executes Every Outbound Call</h2>
            <p className="home-section-desc">
              Every turn follows a strict 5-stage architectural lifecycle executed by backend node runners to ensure zero leakage and complete auditability.
            </p>
          </div>

          <div className="home-pipeline-grid">
            <div className="home-pipeline-card">
              <div className="home-pipeline-num-box">01</div>
              <div className="home-pipeline-title">Connect &amp; Greet</div>
              <p className="home-pipeline-text">
                Softphone line opens with respectful bank greetings in customer&apos;s native Gujarati dialect and obtains affirmative consent before proceeding.
              </p>
            </div>

            <div className="home-pipeline-card">
              <div className="home-pipeline-num-box">02</div>
              <div className="home-pipeline-title">Last-4 Identity Gate</div>
              <p className="home-pipeline-text">
                Hard gate verifying account last 4 digits against PostgreSQL core banking. Zero ledger data or balance hints are transmitted over the wire prior to a match.
              </p>
            </div>

            <div className="home-pipeline-card">
              <div className="home-pipeline-num-box">03</div>
              <div className="home-pipeline-title">Core Ledger Fetch</div>
              <p className="home-pipeline-text">
                Queries read-only PostgreSQL snapshot for real-time ledger balances, hold reasons, return codes, and tax lien notices. No invented numbers or hallucinations.
              </p>
            </div>

            <div className="home-pipeline-card">
              <div className="home-pipeline-num-box">04</div>
              <div className="home-pipeline-title">Hybrid Dialog &amp; Guards</div>
              <p className="home-pipeline-text">
                Combines fast YAML policy templates with DialogCoach LLM for human life context, guarded by Fact Guard to block unauthorized promises or fake refund dates.
              </p>
            </div>

            <div className="home-pipeline-card">
              <div className="home-pipeline-num-box">05</div>
              <div className="home-pipeline-title">Resolution &amp; Handoff</div>
              <p className="home-pipeline-text">
                Guides customer through branch Re-KYC, logs formal dispute tickets via banking tools, or triggers warm seamless transfer to a human branch relationship manager.
              </p>
            </div>
          </div>
        </section>

        {/* ── SECTION: Dialects & Objection Handling ───────────────────────── */}
        <section className="home-section" id="dialect">
          <div className="home-section-header">
            <span className="home-section-tag">NATURAL REGIONAL COMPREHENSION</span>
            <h2 className="home-section-title">Colloquial Gujarati Dialog Engine</h2>
            <p className="home-section-desc">
              Sahayak natively comprehends colloquial spoken Gujarati, Roman Gujarati transcripts, and flexible customer phrasing while always replying in natural spoken Gujarati script.
            </p>
          </div>

          <div className="dialect-grid">
            {DIALECT_EXAMPLES.map((item) => (
              <div key={item.query} className="dialect-card">
                <div className="dialect-card__head">
                  <span className="dialect-card__badge">{item.badge}</span>
                  <span className="dialect-card__tag">{item.tag}</span>
                </div>
                <div className="dialect-card__query">&ldquo;{item.query}&rdquo;</div>
                <div className="dialect-card__resp">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>{item.resp}</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Footer */}
        <footer className="home-footer">
          <div>© 2026 Sahayak Voice · Enterprise Retail Banking Voice Architecture</div>
          <div style={{ display: "flex", gap: "16px" }}>
            <Link href="/dashboard" className="home-nav-link">
              Operations Console
            </Link>
          </div>
        </footer>
      </div>
    </div>
  );
}
