import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BullBearArena — AI Stock Analysis by Legendary Investors",
  description: "Watch Warren Buffett, Cathie Wood, Ray Dalio, Michael Burry, and Peter Lynch debate any stock. AI-powered multi-perspective financial analysis.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
