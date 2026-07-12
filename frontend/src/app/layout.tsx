import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import AuthSessionProvider from "@/components/providers/session-provider";
import SessionStatus from "@/components/auth/session-status";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Bank Reconciliation System",
  description: "Bank Reconciliation System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <AuthSessionProvider>
          <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
            <span className="text-lg font-semibold text-gray-900">
              Bank Reconciliation
            </span>
            <SessionStatus />
          </header>
          <main className="flex-1">{children}</main>
        </AuthSessionProvider>
      </body>
    </html>
  );
}
