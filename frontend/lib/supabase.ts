// S1-0.1 Login: the Supabase client. Null when the NEXT_PUBLIC_SUPABASE_* vars are not set
// (local dev, CI), and the app then runs in guest mode with a browser id (lib/user.ts).
import { createClient, type SupabaseClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabase: SupabaseClient | null = url && anonKey ? createClient(url, anonKey) : null;

export const loginRequired = supabase !== null;
