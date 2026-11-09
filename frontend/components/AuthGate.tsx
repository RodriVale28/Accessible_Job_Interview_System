// S1-0.1 Login: sends signed-out users to /login (except on the landing and login pages),
// and shows the account + Log out button in the top bar. Does nothing in guest mode.
'use client';

import { useEffect, useRef, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { supabase } from '../lib/supabase';
import { clearSettings } from '../lib/settings';

const PUBLIC_PATHS = ['/', '/login'];

function useSignedInEmail() {
  // undefined = still checking, null = signed out
  const [email, setEmail] = useState<string | null | undefined>(supabase ? undefined : null);
  useEffect(() => {
    if (!supabase) return;
    supabase.auth.getSession().then(({ data }) => setEmail(data.session?.user.email ?? null));
    const { data } = supabase.auth.onAuthStateChange((_event, session) => setEmail(session?.user.email ?? null));
    return () => data.subscription.unsubscribe();
  }, []);
  return email;
}

export function AuthGate({ children }: { children: ReactNode }) {
  const email = useSignedInEmail();
  const pathname = usePathname();
  const router = useRouter();
  const guarded = supabase !== null && !PUBLIC_PATHS.includes(pathname);

  useEffect(() => {
    if (guarded && email === null) router.replace(`/login?next=${encodeURIComponent(pathname + window.location.search)}`);
  }, [guarded, email, pathname, router]);

  // After a page change the clicked link is gone and focus falls to <body>. If nothing took focus, put it on the new page's heading.
  const first = useRef(true);
  useEffect(() => {
    if (first.current) { first.current = false; return; }
    const active = document.activeElement;
    if (active && active !== document.body) return;
    const target = document.querySelector<HTMLElement>('#main h1') ?? document.getElementById('main');
    if (!target) return;
    target.tabIndex = -1;
    target.focus();
  }, [pathname]);

  if (guarded && !email) return <p className="wrap hero muted" aria-live="polite">Checking your login…</p>;
  return <>{children}</>;
}

export function AccountMenu() {
  const email = useSignedInEmail();
  const router = useRouter();
  if (!supabase || email === undefined) return null;
  if (!email) return <Link href="/login" className="chip-btn">Log in</Link>;
  return (
    <>
      <span className="muted" style={{ marginRight: 8 }}>{email}</span>
      <button className="chip-btn" type="button"
        onClick={async () => { await supabase!.auth.signOut(); clearSettings(); router.replace('/'); }}>
        Log out
      </button>
    </>
  );
}
