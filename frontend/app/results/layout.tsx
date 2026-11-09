// Gives the results page its own browser tab title (read out by Next.js's route announcer).
import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = { title: 'Interview results · Interview Studio' };

export default function ResultsLayout({ children }: { children: ReactNode }) {
  return children;
}
