'use client';

import { useEffect, useId, useRef, useSyncExternalStore } from 'react';
import ReadAloud from './ReadAloud';
import {
  TEXT_SCALE, getServerSettings, getSettingsSnapshot, initSettings, resetSettings, subscribeSettings, updateSettings,
} from '../lib/settings';

const SAMPLE = 'Tell me about a time you solved a hard problem.';


type Option<T extends string> = { value: T; label: string; swatch?: string; faceClass?: string };

function Choice<T extends string>({ legend, name, value, options, onChange, describedBy }: {
  legend: string; name: string; value: T; options: Option<T>[]; onChange: (v: T) => void; describedBy?: string;
}) {
  return (
    <fieldset className="set-group" aria-describedby={describedBy}>
      <legend className="set-legend">{legend}</legend>
      <div className="set-choices">
        {options.map((o) => (
          <label key={o.value} className="set-opt">
            <input type="radio" className="sr-only" name={name} value={o.value}
              checked={value === o.value} onChange={() => onChange(o.value)} />
            <span className={`set-opt-face${o.faceClass ? ` ${o.faceClass}` : ''}`}>
              {o.swatch && <span className="swatch" data-pv={o.swatch} aria-hidden="true" />}
              {o.label}
            </span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

// Text size as a percentage slider (native range input: arrow keys, Home/End, touch and screen readers just work).
function SizeSlider({ id, value, onChange }: { id: string; value: number; onChange: (v: number) => void }) {
  return (
    <div className="set-group">
      <div className="set-range-head">
        <label htmlFor={id} className="set-legend">Text size</label>
        <span className="set-value" aria-hidden="true">{value}%</span>
      </div>
      <input id={id} type="range" className="set-range" min={TEXT_SCALE.min} max={TEXT_SCALE.max} step={TEXT_SCALE.step}
        value={value} aria-valuetext={`${value} percent`}
        onChange={(e) => onChange(Number(e.target.value))} />
      <div className="set-ticks" aria-hidden="true">
        <span>{TEXT_SCALE.min}%</span><span>{TEXT_SCALE.max}%</span>
      </div>
    </div>
  );
}

// The controls, shared by the dialog and the /settings page.
export function SettingsForm({ onDone }: { onDone?: () => void }) {
  const settings = useSyncExternalStore(subscribeSettings, getSettingsSnapshot, getServerSettings);
  const uid = useId(); // keeps ids and radio names unique when the dialog and the page are both mounted
  const fontHint = `${uid}-font-hint`;
  const readHint = `${uid}-read-hint`;

  return (
    <>
      <SizeSlider id={`${uid}-size`} value={settings.text_scale}
        onChange={(text_scale) => updateSettings({ text_scale })} />

      <Choice legend="Theme" name={`${uid}-theme`} value={settings.theme}
        onChange={(theme) => updateSettings({ theme })}
        options={[
          { value: 'light', label: 'Light', swatch: 'light' },
          { value: 'dark', label: 'Dark', swatch: 'dark' },
          { value: 'contrast', label: 'High contrast', swatch: 'contrast' },
        ]} />

      <Choice legend="Font" name={`${uid}-font`} value={settings.font}
        onChange={(font) => updateSettings({ font })} describedBy={fontHint}
        options={[
          { value: 'default', label: 'Standard', faceClass: 'face-std' },
          { value: 'dyslexic', label: 'Dyslexia-friendly', faceClass: 'face-dys' },
        ]} />
      <p id={fontHint} className="set-hint">Dyslexia-friendly uses Atkinson Hyperlegible</p>

      <div className="set-group">
        <label className="set-switch">
          <input type="checkbox" role="switch" checked={settings.read_aloud}
            aria-describedby={readHint}
            onChange={(e) => updateSettings({ read_aloud: e.target.checked })} />
          <span>Read-aloud buttons</span>
        </label>
        <p id={readHint} className="set-hint">Adds a Read aloud button next to each question</p>
      </div>

      <div className="set-sample">
        <span>{SAMPLE}</span>
        <ReadAloud text={SAMPLE} label="Test voice" force />
      </div>

      <div className="set-actions">
        <button type="button" className="chip-btn" onClick={resetSettings}>Reset to defaults</button>
        {onDone && <button type="button" className="btn primary" onClick={onDone}>Done</button>}
      </div>
    </>
  );
}

// Top-bar button,loads the saved settings once per page load.
export function SettingsPanel() {
  const dialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    document.documentElement.dataset.settingsReady = '1'; // lets e2e tests wait until the page is interactive
    return initSettings();
  }, []);

  return (
    <>
      <button type="button" className="chip-btn set-trigger" aria-haspopup="dialog"
        onClick={() => dialog.current?.showModal()}>
        Settings
      </button>

      <dialog ref={dialog} className="set-dialog" aria-labelledby="set-title"
        onClose={() => window.speechSynthesis?.cancel()}
        onClick={(e) => { if (e.target === e.currentTarget) dialog.current?.close(); }}>
        <div className="set-body">
          <h2 id="set-title" className="set-title">Accessibility settings</h2>
          <SettingsForm onDone={() => dialog.current?.close()} />
        </div>
      </dialog>
    </>
  );
}

export default SettingsPanel;