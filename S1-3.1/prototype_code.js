/**
 * Interview Studio prototype helpers for the interview session screen.
 * These functions are framework independent so the static prototype can use
 * the same interaction patterns as the Next.js session page.
 */

const DEFAULT_THINKING_LABELS = [
  'Checking your answer…',
  'Looking for clear examples…',
  'Preparing your next question…',
];

/** Initialize the conversation view for a question. */
export function setupStage({
  messages,
  question,
  questionIndex,
  total,
  track,
  difficulty,
  mode = 'interview',
  readAloud = false,
  speak = () => {},
  resetFeedback = () => {},
}) {
  messages.replaceChildren();
  resetFeedback();
  const role = document.querySelector('#ctx-role');
  if (role) role.textContent = `${track} · ${difficulty}`;
  const counter = document.querySelector('#qcount');
  if (counter) counter.textContent = mode === 'practice' ? 'Practice' : `Q ${questionIndex}/${total}`;
  const pause = document.querySelector('#pause-btn');
  if (pause) pause.hidden = mode === 'practice';
  const aloud = document.querySelector('#aloud-btn');
  if (aloud) aloud.setAttribute('aria-pressed', String(readAloud));
  const answer = document.querySelector('#answer');
  if (answer) answer.value = '';
  const send = document.querySelector('#send');
  if (send) send.disabled = true;
  appendQuestion({ messages, text: question.text, tag: question.tag, speak });
  if (readAloud) speak(question.text);
}

/** Add an interviewer message, announcing its full text immediately to AT. */
export function appendQuestion({ messages, text, tag, speak = () => {}, reduceMotion = prefersReducedMotion() }) {
  const message = document.createElement('article');
  message.className = 'msg ai';
  const body = document.createElement('div');
  body.className = 'b';
  const accessibleText = document.createElement('span');
  accessibleText.className = 'sr-only';
  accessibleText.textContent = text;
  const visualText = document.createElement('span');
  visualText.className = 'tw';
  visualText.setAttribute('aria-hidden', 'true');
  body.append(accessibleText, visualText);

  const readButton = document.createElement('button');
  readButton.type = 'button';
  readButton.className = 'speak';
  readButton.textContent = 'Read aloud';
  readButton.setAttribute('aria-label', 'Read this question aloud');
  readButton.addEventListener('click', () => speak(text));
  message.append(body, readButton);
  messages.append(message);

  const addTag = () => {
    if (tag) {
      const badge = document.createElement('span');
      badge.className = 'tag';
      badge.textContent = tag;
      body.append(badge);
    }
    messages.scrollTop = messages.scrollHeight;
  };
  if (reduceMotion || !text) {
    visualText.textContent = text;
    addTag();
    return Promise.resolve();
  }

  const caret = document.createElement('span');
  caret.className = 'caret';
  caret.setAttribute('aria-hidden', 'true');
  visualText.after(caret);
  const step = Math.max(1, Math.ceil(text.length / 120));
  return new Promise((resolve) => {
    let index = 0;
    const tick = () => {
      index = Math.min(text.length, index + step);
      visualText.textContent = text.slice(0, index);
      messages.scrollTop = messages.scrollHeight;
      if (index < text.length) window.setTimeout(tick, 18);
      else {
        caret.remove();
        addTag();
        resolve();
      }
    };
    tick();
  });
}

/** Append the candidate's answer as plain text. */
export function appendAnswer(messages, text) {
  const message = document.createElement('article');
  message.className = 'msg me';
  const body = document.createElement('div');
  body.className = 'b';
  body.textContent = text;
  message.append(body);
  messages.append(message);
  messages.scrollTop = messages.scrollHeight;
}

/** Add a disposable, reduced-motion-aware analyzing indicator. */
export function appendAnalyzing(messages, labels = DEFAULT_THINKING_LABELS, { reduceMotion = prefersReducedMotion(), minimumDuration = 1400 } = {}) {
  const message = document.createElement('div');
  message.className = 'msg ai';
  message.setAttribute('role', 'status');
  message.setAttribute('aria-live', 'polite');
  const body = document.createElement('span');
  body.className = 'b thinking';
  const label = document.createElement('span');
  label.className = 'lbl';
  label.textContent = labels[0] || 'Analyzing your answer…';
  body.append(label);
  if (!reduceMotion) {
    const dots = document.createElement('span');
    dots.className = 'typing';
    dots.setAttribute('aria-hidden', 'true');
    for (let i = 0; i < 3; i += 1) dots.append(document.createElement('i'));
    body.prepend(dots);
  }
  message.append(body);
  messages.append(message);
  messages.scrollTop = messages.scrollHeight;

  const started = Date.now();
  let labelIndex = 0;
  const interval = !reduceMotion && labels.length > 1
    ? window.setInterval(() => {
      labelIndex = Math.min(labelIndex + 1, labels.length - 1);
      label.textContent = labels[labelIndex];
    }, 900)
    : undefined;
  return {
    element: message,
    wait: () => new Promise((resolve) => window.setTimeout(resolve, reduceMotion ? 0 : Math.max(0, minimumDuration - (Date.now() - started)))),
    remove() {
      if (interval !== undefined) window.clearInterval(interval);
      message.remove();
    },
  };
}

export function prefersReducedMotion() {
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}
