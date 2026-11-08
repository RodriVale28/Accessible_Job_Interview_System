
import { authHeaders } from './user';

export type Settings = {
  text_size: 'sm' | 'md' | 'lg' | 'xl';
  theme: 'light' | 'dark' | 'contrast';
  font: 'default' | 'dyslexic';
  read_aloud: boolean;
};

export const TEXT_SIZES = ['sm', 'md', 'lg', 'xl'] as const;
export const THEMES = ['light', 'dark', 'contrast'] as const;
export const FONTS = ['default', 'dyslexic'] as const;

export const DEFAULT_SETTINGS: Settings = { text_size: 'md', theme: 'light', font: 'default', read_aloud: false };

const KEY = 'interview-studio-settings';

function pick<T extends string>(allowed: readonly T[], value: unknown, fallback: T): T {
  return typeof value === 'string' && (allowed as readonly string[]).includes(value) ? (value as T) : fallback;
}


export function normalizeSettings(raw: unknown): Settings {
  const r = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
  return {
    text_size: pick(TEXT_SIZES, r.text_size, DEFAULT_SETTINGS.text_size),
    theme: pick(THEMES, r.theme, DEFAULT_SETTINGS.theme),
    font: pick(FONTS, r.font, DEFAULT_SETTINGS.font),
    read_aloud: r.read_aloud === true,
  };
}

// Runs in <head> before the first paint so there is no flash of the wrong theme or size.
export const SETTINGS_INIT_SCRIPT = `(function(){var d=document.documentElement,s={};try{s=JSON.parse(localStorage.getItem(${JSON.stringify(KEY)})||'{}')||{}}catch(e){}function p(a,v,f){return a.indexOf(v)>-1?v:f}d.dataset.textSize=p(${JSON.stringify(TEXT_SIZES)},s.text_size,'md');d.dataset.theme=p(${JSON.stringify(THEMES)},s.theme,'light');d.dataset.font=p(${JSON.stringify(FONTS)},s.font,'default')})();`;

//browser storage
function readLocal(): Settings | null {
  try {
    const saved = window.localStorage.getItem(KEY);
    return saved ? normalizeSettings(JSON.parse(saved)) : null;
  } catch {
    return null;
  }
}
function writeLocal(s: Settings) {
  try { window.localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* keep going in memory */ }
}
function removeLocal() {
  try { window.localStorage.removeItem(KEY); } catch { /* storage blocked: nothing to remove */ }
}

let current: Settings = DEFAULT_SETTINGS;
const listeners = new Set<() => void>();

export const getSettingsSnapshot = () => current;
export const getServerSettings = () => DEFAULT_SETTINGS;
export function subscribeSettings(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

function same(a: Settings, b: Settings) {
  return a.text_size === b.text_size && a.theme === b.theme && a.font === b.font && a.read_aloud === b.read_aloud;
}

// The three data-* attributes on <html> are what globals.css reads.
function applyToDocument(s: Settings) {
  const root = document.documentElement;
  root.dataset.textSize = s.text_size;
  root.dataset.theme = s.theme;
  root.dataset.font = s.font;
}

function setCurrent(next: Settings) {
  if (same(next, current)) return;
  current = next;
  applyToDocument(next);
  listeners.forEach((fn) => fn());
}


// Account copy (GET / PUT /api/settings). Signed out = no auth headers = browser only.
// Plain fetch, not api(): a 401 here must never send the user to the login page.
async function account(init?: RequestInit): Promise<Settings | null> {
  try {
    const headers = await authHeaders();
    if (!Object.keys(headers).length) return null;
    const res = await fetch('/api/settings', {
      ...init, headers: { 'Content-Type': 'application/json', ...headers }, cache: 'no-store',
    });
    return res.ok ? normalizeSettings(await res.json()) : null;
  } catch {
    return null; // offline or server down: localStorage keeps working
  }
}

let edits = 0; // a change made while the account copy loads wins over the loaded copy

// Load the account's saved settings (page load and sign-in), so they survive logout and login.
export async function loadAccountSettings() {
  const before = edits;
  const saved = await account();
  if (saved && edits === before) {
    writeLocal(saved);
    setCurrent(saved);
  }
}

// Call once from a mounted component. Returns the cleanup function.
export function initSettings(): () => void {
  const local = readLocal();
  if (local) setCurrent(local);
  void loadAccountSettings();
  return () => {};
}

export function updateSettings(patch: Partial<Settings>) {
  const next = normalizeSettings({ ...current, ...patch });
  if (same(next, current)) return;
  edits += 1;
  writeLocal(next);
  setCurrent(next);
  void account({ method: 'PUT', body: JSON.stringify(next) });
}

export const resetSettings = () => updateSettings(DEFAULT_SETTINGS);

// deletes local settings and resets back to the default settings
export function clearSettings() {
  removeLocal();
  setCurrent(DEFAULT_SETTINGS);
}