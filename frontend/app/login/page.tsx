// S1-0.1 Log in / create account with Supabase Auth (email + password).
'use client';

import { Suspense, useEffect, useRef, useState, type FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '../../lib/supabase';

// Only same-site paths, so a crafted link cannot send people elsewhere after login. The URL parser
// treats "\" like "/" and strips tabs and newlines, so resolve the link instead of checking its text.
function safeTarget(next: string | null) {
  if (!next?.startsWith('/')) return '/';
  try {
    const url = new URL(next, 'http://same-site.invalid');
    const path = url.pathname + url.search + url.hash;
    return url.origin === 'http://same-site.invalid' && !path.startsWith('//') ? path : '/';
  } catch {
    return '/';
  }
}

type Bad = 'email' | 'password' | 'both' | null;

function LoginForm() {
  const router = useRouter();
  const target = safeTarget(useSearchParams().get('next'));
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);
  const [bad, setBad] = useState<Bad>(null); // which field(s) the error is about
  const emailRef = useRef<HTMLInputElement>(null);
  const passwordRef = useRef<HTMLInputElement>(null);
  const signup = mode === 'signup';

  // already logged in: go on to where the user was headed instead of showing the form
  useEffect(() => {
    void supabase?.auth.getSession().then(({ data }) => { if (data.session) router.replace(target); });
  }, [router, target]);

  if (!supabase) {
    return (
      <div className="panel pad">
        <h1 className="card-title">Login is off</h1>
        <p className="muted">This build runs in guest mode, so no account is needed.</p>
      </div>
    );
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (loading) return;
    setError('');
    setBad(null);
    setNotice('');
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      setBad(!email.trim() ? 'email' : 'password');
      (!email.trim() ? emailRef : passwordRef).current?.focus();
      return;
    }
    if (signup && password.length < 8) {
      setError('Use a password of at least 8 characters.');
      setBad('password');
      passwordRef.current?.focus();
      return;
    }
    setLoading(true);
    const creds = { email: email.trim(), password };
    const { data, error: authError } = signup
      ? await supabase!.auth.signUp(creds)
      : await supabase!.auth.signInWithPassword(creds);
    setLoading(false);
    if (authError) {
      setError(authError.message);
      setBad('both');
      passwordRef.current?.focus();
      return;
    }
    if (!data.session) {
      // email confirmation is on in Supabase: no session until the link is clicked
      setNotice('Check your email for a link to confirm your account, then log in.');
      setMode('login');
      return;
    }
    router.replace(target);
  }

  return (
    <form className="panel pad" onSubmit={handleSubmit} noValidate>
      <h1 id="login-title" className="card-title">{signup ? 'Create an account' : 'Log in'}</h1>
      <p className="muted" style={{ margin: '-6px 0 20px' }}>
        Your interviews and results are saved to your account.
      </p>

      {error && <div role="alert" id="login-error" className="alert">{error}</div>}
      {notice && <p role="status">{notice}</p>}
      <p role="status" className="sr-only">{loading ? 'Please wait…' : ''}</p>

      <div className="opt-group">
        <label htmlFor="email" className="glabel">Email</label>
        <input id="email" ref={emailRef} type="email" autoComplete="email" required
          value={email} onChange={(e) => setEmail(e.target.value)}
          aria-invalid={bad === 'email' || bad === 'both'} aria-describedby={error ? 'login-error' : undefined} />
      </div>
      <div className="opt-group">
        <label htmlFor="password" className="glabel">Password</label>
        <input id="password" ref={passwordRef} type="password" required minLength={signup ? 8 : undefined}
          autoComplete={signup ? 'new-password' : 'current-password'}
          value={password} onChange={(e) => setPassword(e.target.value)}
          aria-invalid={bad === 'password' || bad === 'both'}
          aria-describedby={[signup && 'password-hint', error && 'login-error'].filter(Boolean).join(' ') || undefined} />
        {signup && <p id="password-hint" className="hint">At least 8 characters.</p>}
      </div>

      <div className="actions">
        <button className="btn primary" type="submit" aria-disabled={loading}>
          {loading ? 'Please wait…' : signup ? 'Create account' : 'Log in'}
        </button>
        <button className="btn" type="button" onClick={() => { setMode(signup ? 'login' : 'signup'); setError(''); setBad(null); }}>
          {signup ? 'I already have an account' : 'Create an account'}
        </button>
      </div>
    </form>
  );
}

export default function LoginPage() {
  return (
    <section className="wrap hero" aria-labelledby="login-title">
      <Suspense>
        <LoginForm />
      </Suspense>
    </section>
  );
}
