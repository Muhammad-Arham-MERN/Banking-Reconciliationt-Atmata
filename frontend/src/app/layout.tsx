import type { Metadata } from "next";
import { Space_Grotesk, Geist_Mono } from "next/font/google";
import "./globals.css";
import AuthSessionProvider from "@/components/providers/session-provider";
import { ThemeProvider } from "@/components/providers/theme-provider";
import SessionStatus from "@/components/auth/session-status";
import { ThemeToggle } from "@/components/theme/theme-toggle";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-mono",
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
      suppressHydrationWarning
      className={`${spaceGrotesk.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <AuthSessionProvider>
            <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3 dark:border-gray-800 dark:bg-gray-950">
              <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Bank Reconciliation
              </span>
              <nav className="flex items-center gap-4 text-sm font-medium">
                <a
                  href="/upload"
                  className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
                >
                  Upload
                </a>
                <a
                  href="/tests"
                  className="text-gray-600 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100"
                >
                  Test Data
                </a>
                <div className="flex items-center gap-3">
                  <ThemeToggle />
                  <SessionStatus />
                </div>
              </nav>
            </header>
            <main className="flex-1">{children}</main>
          </AuthSessionProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
