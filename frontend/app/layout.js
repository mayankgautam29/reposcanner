import { Fraunces, IBM_Plex_Mono, Instrument_Sans } from "next/font/google";

import "./globals.css";

const fraunces = Fraunces({ subsets: ["latin"], style: ["normal", "italic"], axes: ["opsz"], variable: "--font-fraunces" });
const instrument = Instrument_Sans({ subsets: ["latin"], variable: "--font-instrument" });
const plexMono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500"], variable: "--font-plex-mono" });

export const metadata = {
  title: "RepoScan - know what is inside a repository",
  description: "Paste a public GitHub link and get a quality score out of 100.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${fraunces.variable} ${instrument.variable} ${plexMono.variable} bg-paper font-sans text-ink antialiased`}>
        {children}
      </body>
    </html>
  );
}
