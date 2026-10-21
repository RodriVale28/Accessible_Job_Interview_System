// Who is calling the API. With login configured (lib/supabase.ts) that is the Supabase
// access token; otherwise (local dev, CI) a random guest id kept in this browser.
import { supabase } from './supabase';

export async function authHeaders(): Promise<Record<string, string>> {
  if (!supabase) return { 'X-User-Id': getUserId() };
  const { data } = await supabase.auth.getSession();
  return data.session ? { Authorization: `Bearer ${data.session.access_token}` } : {};
}

const KEY = 'interview-studio-user-id';
let memoryId: string | null = null;

function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export function getUserId(): string {
  try {
    const saved = window.localStorage.getItem(KEY);
    if (saved) return saved;
    const id = newId();
    window.localStorage.setItem(KEY, id);
    return id;
  } catch {
    memoryId ??= newId(); // private mode / storage blocked
    return memoryId;
  }
}
