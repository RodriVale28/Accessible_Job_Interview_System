// Root layout: prototype look (background, top bar, footer), skip link, landmarks.
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import Link from 'next/link';
import { MarkIcon, ShieldIcon } from '@/components/Icons';
import './globals.css';

export const metadata: Metadata = {
  title: 'Interview Studio',
  description: 'Accessible mock technical interviews with feedback you can act on.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <a href="#main" className="skip">Skip to content</a>
        <div className="page">
          <header className="top">
            <div className="wrap">
              <Link href="/" className="brand"><span className="mark"><MarkIcon /></span>Interview Studio</Link>
              <div className="spacer" />
              <Link href="/setup" className="chip-btn">New interview</Link>
            </div>
          </header>
          <main id="main">{children}</main>
          <footer>
            <div className="wrap">
              <span>Accessible Interview System — CSCE 4901 Capstone, Savage 17.</span>
              <span className="a11y-note"><ShieldIcon />Keyboard and screen-reader ready</span>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
