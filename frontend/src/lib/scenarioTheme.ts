export function themeForIssue(issue: string) {
  const norm = (issue || "").toUpperCase();
  switch (norm) {
    case "CHEQUE_BOUNCE":
      return {
        accent: "#7c3aed",
        bg: "#f5f3ff",
        border: "#ddd6fe",
        icon: "📄",
        title: "Cheque return",
        blurb: "NSF / return reason, charges, and how to avoid repeat bounce.",
      };
    case "LIEN":
      return {
        accent: "#d97706",
        bg: "#fffbeb",
        border: "#fde68a",
        icon: "⚖️",
        title: "Lien on balance",
        blurb: "Loan set-off lien / credit hold and available funds to use.",
      };
    case "HOLD":
      return {
        accent: "#ea580c",
        bg: "#fff7ed",
        border: "#fed7aa",
        icon: "⏳",
        title: "UPI / IMPS hold",
        blurb: "Pending transaction hold and bank clearance steps.",
      };
    case "FREEZE":
    case "DEBIT_FREEZE":
      return {
        accent: "#2563eb",
        bg: "#eff6ff",
        border: "#bfdbfe",
        icon: "🔒",
        title: "Debit freeze",
        blurb: "Clarify freeze restriction, statutory order, and documentation.",
      };
    case "INOPERATIVE":
      return {
        accent: "#475569",
        bg: "#f8fafc",
        border: "#e2e8f0",
        icon: "🔄",
        title: "Inoperative account",
        blurb: "Dormant account reminder and simple branch Re-KYC steps.",
      };
    default:
      return {
        accent: "#2563eb",
        bg: "#eff6ff",
        border: "#bfdbfe",
        icon: "🏦",
        title: "Account care",
        blurb: "Proactive update on account health and banking support options.",
      };
  }
}

