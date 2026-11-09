// Gives this page its own browser tab title (the Next.js route announcer reads it to screen-reader users after navigation).
import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = { title: 'Interview in progress · Interview Studio' };

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
