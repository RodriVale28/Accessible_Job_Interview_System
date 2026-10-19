// Landing page. Links into the Sprint 1 flow.
import Link from 'next/link';

export default function Home() {
  return (
    <section className="wrap hero">
      <p className="eyebrow">Accessible Interview System · Sprint 1</p>
      <h1>Practice a technical interview</h1>
      <p className="lede">
        Set up a session, answer questions one at a time, and get a score with feedback on each answer.
      </p>
      <Link className="btn amber" href="/setup">Set up a technical interview</Link>
    </section>
  );
}
