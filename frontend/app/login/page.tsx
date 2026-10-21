// S1-0.1 Log in / create account with Supabase Auth (email + password).
'use client';

import { Suspense, useRef, useState, type FormEvent } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { supabase } from '../../lib/supabase';

function LoginForm() {
  const router = useRouter();
  const next = useSearchParams().get('next');
  // only same-site paths, so a crafted link cannot send people elsewhere after login
  const target = next && next.startsWith('/') && !next.startsWith('//') ? next : '/';
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [loading, setLoading] = useState(false);
  const emailRef = useRef<HTMLInputElement>(null);
  const signup = mode === 'signup';

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
    setError('');
    setNotice('');
    if (!email.trim() || !password) {
      setError('Enter your email and password.');
      emailRef.current?.focus();
      return;
    }
    if (signup && password.length < 8) {
      setError('Use a password of at least 8 characters.');
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

      {error && <div role="alert" className="alert">{error}</div>}
      {notice && <p role="status">{notice}</p>}

      <div className="opt-group">
        <label htmlFor="email" className="glabel">Email</label>
        <input id="email" ref={emailRef} type="email" autoComplete="email" required
          value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <div className="opt-group">
        <label htmlFor="password" className="glabel">Password</label>
        <input id="password" type="password" required minLength={signup ? 8 : undefined}
          autoComplete={signup ? 'new-password' : 'current-password'}
          value={password} onChange={(e) => setPassword(e.target.value)}
          aria-describedby={signup ? 'password-hint' : undefined} />
        {signup && <p id="password-hint" className="hint">At least 8 characters.</p>}
      </div>

      <div className="actions">
        <button className="btn primary" type="submit" disabled={loading}>
          {loading ? 'Please wait…' : signup ? 'Create account' : 'Log in'}
        </button>
        <button className="btn" type="button" onClick={() => { setMode(signup ? 'login' : 'signup'); setError(''); }}>
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
