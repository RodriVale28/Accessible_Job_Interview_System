
// used for api
export type Settings = {
  text_size: 'sm' | 'md' | 'lg' | 'xl';
  theme: 'light' | 'dark' | 'contrast';
  font: 'default' | 'dyslexic';
  read_aloud: boolean;
};


export type LocalSettings = Settings & { text_scale: number };

export const TEXT_SCALE = { min: 80, max: 200, step: 10, default: 100 } as const;
export const THEMES = ['light', 'dark', 'contrast'] as const;
export const FONTS = ['default', 'dyslexic'] as const;
const SIZES = ['sm', 'md', 'lg', 'xl'] as const;

const SIZE_TO_SCALE = { sm: 90, md: 100, lg: 120, xl: 140 } as const;

export const DEFAULT_SETTINGS: LocalSettings = {
  text_size: 'md', text_scale: TEXT_SCALE.default, theme: 'light', font: 'default', read_aloud: false,
};

const KEY = 'interview-studio-settings';

// sets the slider to match the api
export function scaleToSize(scale: number): Settings['text_size'] {
  return scale <= 90 ? 'sm' : scale <= 110 ? 'md' : scale <= 150 ? 'lg' : 'xl';
}

function pick<T extends string>(allowed: readonly T[], value: unknown, fallback: T): T {
  return typeof value === 'string' && (allowed as readonly string[]).includes(value) ? (value as T) : fallback;
}

function cleanScale(value: unknown, size: unknown): number {
  let n = Number(value);
  if (!(n >= TEXT_SCALE.min && n <= TEXT_SCALE.max)) n = SIZE_TO_SCALE[pick(SIZES, size, 'md')];
  return Math.min(TEXT_SCALE.max, Math.max(TEXT_SCALE.min, Math.round(n / TEXT_SCALE.step) * TEXT_SCALE.step));
}

// Anything (old storage, a typo) becomes a valid LocalSettings object.
export function normalizeSettings(raw: unknown): LocalSettings {
  const r = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
  const text_scale = cleanScale(r.text_scale, r.text_size);
  return {
    text_size: scaleToSize(text_scale),
    text_scale,
    theme: pick(THEMES, r.theme, DEFAULT_SETTINGS.theme),
    font: pick(FONTS, r.font, DEFAULT_SETTINGS.font),
    read_aloud: r.read_aloud === true,
  };
}

// Runs in <head> before the first paint so there is no flash of the wrong theme or size.
export const SETTINGS_INIT_SCRIPT = `(function(){var d=document.documentElement,s={};try{s=JSON.parse(localStorage.getItem(${JSON.stringify(KEY)})||'{}')||{}}catch(e){}function p(a,v,f){return a.indexOf(v)>-1?v:f}var sc=Number(s.text_scale);if(!(sc>=${TEXT_SCALE.min}&&sc<=${TEXT_SCALE.max}))sc=${JSON.stringify(SIZE_TO_SCALE)}[p(${JSON.stringify(SIZES)},s.text_size,'md')];sc=Math.min(${TEXT_SCALE.max},Math.max(${TEXT_SCALE.min},Math.round(sc/${TEXT_SCALE.step})*${TEXT_SCALE.step}));d.style.setProperty('--text-scale',String(sc/100));d.dataset.textSize=sc<=90?'sm':sc<=110?'md':sc<=150?'lg':'xl';d.dataset.theme=p(${JSON.stringify(THEMES)},s.theme,'light');d.dataset.font=p(${JSON.stringify(FONTS)},s.font,'default')})();`;

//browser storage
function readLocal(): LocalSettings | null {
  try {
    const saved = window.localStorage.getItem(KEY);
    return saved ? normalizeSettings(JSON.parse(saved)) : null;
  } catch {
    return null;
  }
}
function writeLocal(s: LocalSettings) {
  try { window.localStorage.setItem(KEY, JSON.stringify(s)); } catch { /* keep going in memory */ }
}

//
let current: LocalSettings = DEFAULT_SETTINGS;
const listeners = new Set<() => void>();

export const getSettingsSnapshot = () => current;
export const getServerSettings = () => DEFAULT_SETTINGS;
export function subscribeSettings(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}

function same(a: LocalSettings, b: LocalSettings) {
  return a.text_scale === b.text_scale && a.theme === b.theme && a.font === b.font && a.read_aloud === b.read_aloud;
}

// The data-* attributes and --text-scale on <html> are what globals.css reads.
function applyToDocument(s: LocalSettings) {
  const root = document.documentElement;
  root.style.setProperty('--text-scale', String(s.text_scale / 100));
  root.dataset.textSize = s.text_size;
  root.dataset.theme = s.theme;
  root.dataset.font = s.font;
}

function setCurrent(next: LocalSettings) {
  if (same(next, current)) return;
  current = next;
  applyToDocument(next);
  listeners.forEach((fn) => fn());
}


// Call once from a mounted component. Returns the cleanup function.
export function initSettings(): () => void {
  const local = readLocal();
  if (local) setCurrent(local);
  return () => {};
}

export function updateSettings(patch: Partial<LocalSettings>) {
  // A change to text_size moves the percentage to that size's step.
  const next = normalizeSettings({
    ...current,
    ...patch,
    text_scale: patch.text_scale ?? (patch.text_size ? SIZE_TO_SCALE[patch.text_size] : current.text_scale),
  });
  if (same(next, current)) return;
  writeLocal(next);
  setCurrent(next);
}

export const resetSettings = () => updateSettings(DEFAULT_SETTINGS);