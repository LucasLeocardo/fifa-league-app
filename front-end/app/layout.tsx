import type { Metadata } from "next";
import { Bebas_Neue, Outfit, Geist } from "next/font/google";

import { FlashAlert } from "@/components/FlashAlert";

import "./globals.css";
import { cn } from "@/lib/utils";

const geist = Geist({subsets:['latin'],variable:'--font-sans'});

const display = Bebas_Neue({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-display",
});

const body = Outfit({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "FIFA League",
  description: "Sua liga. Seus confrontos. Seu ranking.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={cn("h-full", display.variable, body.variable, "font-sans", geist.variable)}>
      <body className="min-h-full antialiased">
        <FlashAlert />
        {children}
      </body>
    </html>
  );
}
