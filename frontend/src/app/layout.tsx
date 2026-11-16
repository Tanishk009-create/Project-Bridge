import type { Metadata } from "next";
import "./globals.css";
import { BridgeProvider } from "@/components/BridgeProvider";

export const metadata: Metadata = {
  title: "Bridge — A private place to think out loud",
  description: "Project Bridge frontend prototype",
  icons: { icon: "/bridge-logo.png" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><BridgeProvider>{children}</BridgeProvider></body>
    </html>
  );
}
