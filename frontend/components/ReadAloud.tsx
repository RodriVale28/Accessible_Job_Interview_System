'use client';

import { useEffect, useRef, useState, useSyncExternalStore } from 'react';
import { getSettingsSnapshot, subscribeSettings } from '../lib/settings';

const noSubscribe = () => () => {};
const speechSupported = () =>
  typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;

const SpeakerIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4Z" fill="currentColor" /><path d="M16.5 8.5a5 5 0 0 1 0 7M19 6a8.5 8.5 0 0 1 0 12" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
);
const StopIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" /></svg>
);

const BAD_STOPS = ['canceled', 'interrupted'];

// Prefer a voice for the page language; the browser default otherwise.
function pickVoice(synth: SpeechSynthesis, base: string) {
  const voices = synth.getVoices().filter((v) => v.lang.toLowerCase().startsWith(base));
  return voices.find((v) => v.default) ?? voices[0];
}

export function ReadAloud({ text, className, label = 'Read aloud', force = false }: {
  text: string; className?: string; label?: string; force?: boolean;
}) {
  const enabled = useSyncExternalStore(subscribeSettings, () => getSettingsSnapshot().read_aloud, () => false);
  const supported = useSyncExternalStore(noSubscribe, speechSupported, () => false);
  const [speaking, setSpeaking] = useState(false);
  const [failed, setFailed] = useState(false);
  const utterance = useRef<SpeechSynthesisUtterance | null>(null);

  // Stop talking when the text changes (next question) or the button goes away.
  useEffect(() => () => {
    if (utterance.current) {
      utterance.current = null;
      window.speechSynthesis.cancel();
      setSpeaking(false);
    }
  }, [text]);

  if ((!enabled && !force) || !supported) return null;

  const clean = text.replace(/\s+/g, ' ').trim();

  function toggle() {
    const synth = window.speechSynthesis;
    if (speaking) {
      utterance.current = null;
      synth.cancel();
      setSpeaking(false);
      return;
    }
    if (!clean) return;
    setFailed(false);

    const u = new SpeechSynthesisUtterance(clean);
    const base = (document.documentElement.lang || 'en').split('-')[0].toLowerCase();
    const voice = pickVoice(synth, base);
    if (voice) { u.voice = voice; u.lang = voice.lang; } else { u.lang = base === 'en' ? 'en-US' : base; }

    let started = false;
    const finished = (ok: boolean) => {
      if (utterance.current !== u) return;
      utterance.current = null;
      setSpeaking(false);
      if (!ok) setFailed(true);
    };
    u.onstart = () => { started = true; };
    u.onend = () => finished(true);
    u.onerror = (e) => finished(BAD_STOPS.includes(e.error));
    utterance.current = u; // keep a reference so the browser cannot collect it mid-speech
    setSpeaking(true);

    const go = () => {
      if (utterance.current !== u) return;
      synth.resume(); // some browsers start paused
      synth.speak(u);
      // No sound and no error (no voice installed, audio blocked): say so instead of doing nothing.
      window.setTimeout(() => {
        if (utterance.current === u && !started) { synth.cancel(); finished(false); }
      }, 4000);
    };
    if (synth.speaking || synth.pending) { synth.cancel(); window.setTimeout(go, 80); } else go();
  }

  return (
    <>
      <button type="button" className={`chip-btn read-aloud${className ? ` ${className}` : ''}`} onClick={toggle} disabled={!clean}>
        {speaking ? <StopIcon /> : <SpeakerIcon />}
        {speaking ? 'Stop reading' : label}
      </button>
      {failed && <span role="status" className="small muted">Could not play audio. Check your volume and that your browser has a voice installed.</span>}
    </>
  );
}

export default ReadAloud;
