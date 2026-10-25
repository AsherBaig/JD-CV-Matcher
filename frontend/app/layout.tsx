import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

// Next reads this and writes the <title> and <meta> tags for every page.
export const metadata: Metadata = {
  title: "JD-CV Matcher",
  description: "Dashboard for tailored CVs and job applications",
};

// Wraps every page. {children} is where the matching page.tsx is rendered —
// the same idea as Angular's <router-outlet>.
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <nav className="nav">
          <Link className="nav-brand" href="/">
            JD-CV Matcher
          </Link>
          <Link className="nav-link" href="/analyze">
            New Analysis
          </Link>
        </nav>
        <main>{children}</main>
      </body>
    </html>
  );
}
