// Landing page. Links into setup, practice and past interviews.
import type { Metadata } from 'next';
import Link from 'next/link';
import { PastInterviews } from '@/components/PastInterviews';

export const metadata: Metadata = { title: 'Home · Interview Studio' };

export default function Home() {
  return (
    <section className="wrap hero">
      <p className="eyebrow">Accessible Interview System</p>
      <h1>Practice a job interview</h1>
      <p className="lede">
        Set up a technical, behavioral or mixed interview, answer one question at a time, and get a score with feedback on each answer.
      </p>
      <div className="actions">
        <Link className="btn amber" href="/setup">Set up an interview</Link>
        <Link className="btn primary" href="/practice">Practice one question</Link>
      </div>
      <PastInterviews />
    </section>
  );
}
