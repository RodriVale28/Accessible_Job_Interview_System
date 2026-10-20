// S1-0.1 Login: sends signed-out users to /login (except on the landing and login pages),
// and shows the account + Log out button in the top bar. Does nothing in guest mode.
'use client';

import { useEffect, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { supabase } from '../lib/supabase';

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
    if (guarded && email === null) router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [guarded, email, pathname, router]);

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
        onClick={async () => { await supabase!.auth.signOut(); router.replace('/'); }}>
        Log out
      </button>
    </>
  );
}
