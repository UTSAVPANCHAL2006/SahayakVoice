import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sahayak Voice: Intelligent Outbound Banking Care in Native Gujarati Voice",
  description:
    "The next-generation outbound AI agent for Indian banking. Speaks natural colloquial Gujarati, grounded directly in core banking databases, ensuring every balance, fee, and timeline is accurate and compliant.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
