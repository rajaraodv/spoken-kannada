import type { Metadata } from "next";
import { Baloo_2, Noto_Sans_Kannada } from "next/font/google";
import "./globals.css";

const baloo = Baloo_2({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["400", "500", "600", "700", "800"],
});

const kannada = Noto_Sans_Kannada({
  subsets: ["kannada"],
  variable: "--font-kannada",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Spoken Kannada Chapters",
  description: "Generated spoken Kannada chapter practice pages.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${baloo.variable} ${kannada.variable} font-display`}>
        {children}
      </body>
    </html>
  );
}
