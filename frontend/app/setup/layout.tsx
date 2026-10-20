// Gives the setup page its own browser tab title. A distinct title is also what
// Next.js's route announcer reads to screen-reader users after navigation.
import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = { title: 'Interview setup · Interview Studio' };

export default function SetupLayout({ children }: { children: ReactNode }) {
  return children;
}
