import type { Metadata } from "next";

import { Providers } from "./providers";
import "./globals.css";
import { ChatPanel } from "@/components/chat/ChatPanel";
import { Navbar } from "@/components/ui/Navbar";

export const metadata: Metadata = {
  title: "Football Intelligence Platform",
  description:
    "Standings, team statistics, and recent results across Europe's top five football leagues.",
};

// Set the theme class before paint to avoid a flash of the wrong theme.
const themeScript = `(function(){try{var t=localStorage.getItem('theme');var d=t?t==='dark':window.matchMedia('(prefers-color-scheme: dark)').matches;if(d)document.documentElement.classList.add('dark');}catch(e){}})();`;

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      {/* suppressHydrationWarning: browser extensions (e.g. Grammarly) inject
          attributes onto <body> before React hydrates. */}
      <body className="min-h-screen" suppressHydrationWarning>
        <Providers>
          <Navbar />
          <main className="container py-8 sm:py-10">{children}</main>
          <footer className="border-t border-border">
            <div className="container py-6 text-sm text-muted">
              Football Intelligence Platform · Data via Football-Data.org
            </div>
          </footer>
          <ChatPanel />
        </Providers>
      </body>
    </html>
  );
}
