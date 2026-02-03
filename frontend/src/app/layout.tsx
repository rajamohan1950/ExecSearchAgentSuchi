import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Suchi - Your Autonomous Job Search Agent",
  description: "Upload your LinkedIn profile and let Suchi find your next role",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50">{children}</body>
    </html>
  );
}
