import type { Metadata } from "next";
import "./globals.css";
import { AppSidebar } from "@/components/AppSidebar";
import { AppHeader } from "@/components/AppHeader";

export const metadata: Metadata = {
  title: "EventFlow AI | Smart Traffic Intelligence",
  description: "AI-powered event-driven traffic orchestration for smart cities.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased overflow-hidden">
        <div className="fixed inset-0 overflow-hidden pointer-events-none z-0">
          <div
            className="ambient-orb w-[600px] h-[600px] opacity-[0.07]"
            style={{ background: "#3B82F6", top: "-200px", left: "-100px" }}
          />
          <div
            className="ambient-orb w-[500px] h-[500px] opacity-[0.05]"
            style={{ background: "#06B6D4", bottom: "-150px", right: "-100px", animationDelay: "2s" }}
          />
          <div
            className="ambient-orb w-[300px] h-[300px] opacity-[0.04]"
            style={{ background: "#A78BFA", top: "40%", left: "40%", animationDelay: "4s" }}
          />
        </div>

        <div className="flex h-screen relative z-10">
          <AppSidebar />
          <div className="flex-1 flex flex-col overflow-hidden">
            <AppHeader />
            <main className="flex-1 overflow-hidden">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
