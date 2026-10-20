// ==========================================================================
// Interview Studio — S1-3.1: Interview question/answer screen
// Owner (Sprint 1): Hongli Pan   |   Story: US-3 Answer Interview Questions
//
// This file collects the parts of the shared Interview Studio prototype that
// Hongli Pan owns. The prototype was built by the team before tasks were
// assigned; from Sprint 1 on, Hongli maintains and extends this part.
// It is a reference copy — the running app still uses the original files.
//
// HOW IT WORKS
//  - Questions appear as chat bubbles. addAi() reveals the text letter by letter, while screen readers get the full text at once through a hidden copy.
//  - The answer box grows as you type; Enter sends, Shift+Enter adds a new line.
//  - The "Q 1/4" counter is the progress indicator; it updates after every answer.
//
// YOUR SPRINT 1 WORK (see the starter file in this folder)
//  - Build the Next.js session page: current question, text answer box, Submit button, progress bar (question X of N) and the countdown timer for 15/30/45 minutes.
//  - Keep the analyzing and typing animations, and turn them off when the user prefers reduced motion.
// ==========================================================================

// --------------------------------------------------------------------------
// FROM: static/index.html, lines 155-224
// WHAT IT DOES: Interview screen markup: chat column, answer box, live-score rail.
// --------------------------------------------------------------------------
/* --- HTML (static/index.html) ---
      <section class="view" id="view-interview" hidden>
        <div class="wrap" style="padding-block:24px 40px">
          <!-- "Ava is preparing" analyzing screen, shown while questions are generated -->
          <div class="panel analyzing" id="analyzing" hidden role="status" aria-live="polite">
            <div class="orb" aria-hidden="true">
              <span class="pulse p1"></span><span class="pulse p2"></span>
              <div class="core"><span></span><span></span><span></span><span></span><span></span></div>
            </div>
            <h2 class="an-title">Ava is preparing your interview</h2>
            <p class="muted an-sub" id="an-sub">Behavioral · Standard</p>
            <ol class="an-steps" id="an-steps"></ol>
            <div class="an-chips" id="an-chips" aria-label="Skills found"></div>
            <div class="an-progress" aria-hidden="true"><i id="an-bar"></i></div>
          </div>

          <div class="panel stage" id="stage">
            <div class="chat-col">
              <div class="chat-head">
                <span class="avatar" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M12 2a5 5 0 0 0-5 5v3a5 5 0 0 0 10 0V7a5 5 0 0 0-5-5Zm8 9a8 8 0 0 1-16 0M12 19v3M8 22h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
                <div><div class="who">Ava · AI Interviewer</div><div class="role" id="ctx-role">Behavioral · Standard</div></div>
                <span class="qcount" id="qcount">Q <b>1</b>/4</span>
                <div class="head-actions">
                  <button class="icon-btn" id="aloud-btn" aria-pressed="false" aria-label="Read questions aloud (text-to-speech)"><svg viewBox="0 0 24 24" fill="none"><path d="M11 5 6 9H3v6h3l5 4V5Z" fill="currentColor"/><path d="M16 9a3 3 0 0 1 0 6M18.5 6.5a7 7 0 0 1 0 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button>
                  <button class="icon-btn" id="pause-btn" aria-label="Pause and save interview"><svg viewBox="0 0 24 24" fill="none"><path d="M8 5v14M16 5v14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></button>
                </div>
              </div>

              <div class="messages" id="messages" role="log" aria-live="polite" aria-label="Interview conversation"></div>

              <div class="composer">
                <button class="mic" id="mic" aria-pressed="false" aria-label="Toggle voice input">
                  <svg viewBox="0 0 24 24" fill="none"><path d="M12 3a3 3 0 0 0-3 3v5a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3ZM6 11a6 6 0 0 0 12 0M12 17v4M9 21h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
                <div class="inpwrap">
                  <label class="sr-only" for="answer">Your answer</label>
                  <textarea id="answer" rows="1" placeholder="Type your answer, or tap the mic to speak…"></textarea>
                  <button class="send" id="send" aria-label="Send answer" disabled><svg viewBox="0 0 24 24" fill="none"><path d="M4 12 20 4l-6 16-3-7-7-1Z" fill="currentColor"/></svg></button>
                </div>
              </div>
              <div class="hint listening" id="listen-hint" hidden>● Listening… speak your answer, tap the mic when done.</div>
            </div>

            <aside class="rail" id="rail" aria-label="Live feedback">
              <div>
                <h4>Live score</h4>
                <div class="score-ring">
                  <svg class="ring" viewBox="0 0 42 42" aria-hidden="true">
                    <circle cx="21" cy="21" r="16" fill="none" stroke="var(--line)" stroke-width="5"/>
                    <circle id="ring-fg" cx="21" cy="21" r="16" fill="none" stroke="var(--amber)" stroke-width="5" stroke-linecap="round" stroke-dasharray="100.5" stroke-dashoffset="100.5" transform="rotate(-90 21 21)"/>
                    <text id="ring-num" x="21" y="24.5" text-anchor="middle" font-size="11" fill="var(--ink)" font-family="var(--font-mono)">–</text>
                  </svg>
                  <div><div class="slabel">Confidence on your last answer</div></div>
                </div>
              </div>
              <div class="meter">
                <h4 style="margin-bottom:12px">Breakdown</h4>
                <div class="row"><span>Structure (STAR)</span><span class="v" id="v-structure">–</span></div>
                <div class="bar"><i id="bar-structure"></i></div>
                <div class="row"><span>Clarity</span><span class="v" id="v-clarity">–</span></div>
                <div class="bar"><i id="bar-clarity"></i></div>
                <div class="row"><span>Relevance</span><span class="v" id="v-relevance">–</span></div>
                <div class="bar"><i id="bar-relevance"></i></div>
                <div class="row"><span>Completeness</span><span class="v" id="v-completeness">–</span></div>
                <div class="bar"><i id="bar-completeness"></i></div>
              </div>
              <div class="tip"><span class="k">Coaching</span><span id="tip-body">Answer the question to see your live score and one concrete tip.</span></div>
            </aside>
          </div>
        </div>
      </section>
--- end HTML --- */

// --------------------------------------------------------------------------
// FROM: static/js/app.js, lines 228-239
// WHAT IT DOES: Resets the screen for a new interview and shows the first question.
// --------------------------------------------------------------------------
  function setupStage(r) {
    messages.innerHTML = "";
    $("#ctx-role").textContent = `${state.track} · ${state.difficulty}`;
    $("#qcount").innerHTML = state.mode === "practice"
      ? "Practice" : `Q <b>${r.q_index}</b>/${r.total}`;
    $("#pause-btn").hidden = state.mode === "practice";
    resetRail();
    addAi(r.question, r.tag);
    $("#aloud-btn").setAttribute("aria-pressed", state.readAloud.toString());
    if (state.readAloud) speak(r.question);
    $("#answer").value = ""; $("#send").disabled = true;
  }

// --------------------------------------------------------------------------
// FROM: static/js/app.js, lines 241-268
// WHAT IT DOES: Ava's message bubble with typewriter effect; screen readers get the full text immediately.
// --------------------------------------------------------------------------
  function addAi(text, tag, animate = true) {
    const el = document.createElement("div");
    el.className = "msg ai";
    el.innerHTML =
      `<span class="ava" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none"><path d="M12 2a5 5 0 0 0-5 5v3a5 5 0 0 0 10 0V7a5 5 0 0 0-5-5Zm8 9a8 8 0 0 1-16 0M12 19v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
       <div><div class="name">Ava</div><div class="b new"><span class="sr-only"></span><span class="tw" aria-hidden="true"></span></div>
       <button class="speak" aria-label="Read this question aloud"><svg viewBox="0 0 24 24" fill="none"><path d="M11 5 6 9H3v6h3l5 4V5Z" fill="currentColor"/><path d="M16 9a3 3 0 0 1 0 6M18.5 6.5a7 7 0 0 1 0 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>Read aloud</button></div>`;
    const b = el.querySelector(".b"), tw = el.querySelector(".tw");
    el.querySelector(".sr-only").textContent = text;
    el.querySelector(".speak").addEventListener("click", () => speak(text));
    messages.appendChild(el);
    const addTag = () => { if (tag) { const s=document.createElement("span"); s.className="tag"; s.textContent=tag; b.appendChild(s); } messages.scrollTop = messages.scrollHeight; };
    if (!animate || reduce) { tw.textContent = text; addTag(); return Promise.resolve(); }
    // typewriter: ~18ms per character, capped at ~2.2s total for long questions
    const step = Math.max(1, Math.ceil(text.length / 120));
    const caret = document.createElement("span"); caret.className = "caret";
    tw.after(caret);
    return new Promise((res) => {
      let i = 0;
      (function tick() {
        i = Math.min(text.length, i + step);
        tw.textContent = text.slice(0, i);
        messages.scrollTop = messages.scrollHeight;
        if (i < text.length) setTimeout(tick, 18);
        else { caret.remove(); addTag(); res(); }
      })();
    });
  }

// --------------------------------------------------------------------------
// FROM: static/js/app.js, lines 269-274
// WHAT IT DOES: The user's message bubble.
// --------------------------------------------------------------------------
  function addMe(text) {
    const el = document.createElement("div"); el.className = "msg me";
    el.innerHTML = `<div><div class="name">You</div><div class="b"></div></div>`;
    el.querySelector(".b").textContent = text;
    messages.appendChild(el); messages.scrollTop = messages.scrollHeight;
  }

// --------------------------------------------------------------------------
// FROM: static/js/app.js, lines 275-290
// WHAT IT DOES: 'Ava is reading your answer…' bubble with rotating status labels.
// --------------------------------------------------------------------------
  function addTyping(labels) {
    const el = document.createElement("div"); el.className = "msg ai"; el.id = "typing";
    el.innerHTML = `<span class="ava"></span><div class="b thinking"><div class="typing"><span></span><span></span><span></span></div><span class="lbl"></span></div>`;
    messages.appendChild(el); messages.scrollTop = messages.scrollHeight;
    const lbl = el.querySelector(".lbl"); let k = 0, timer = null;
    if (labels && labels.length) {
      lbl.textContent = labels[0];
      if (!reduce) timer = setInterval(() => { k = Math.min(k + 1, labels.length - 1); lbl.textContent = labels[k]; }, 900);
    }
    const started = Date.now();
    const origRemove = el.remove.bind(el);
    el.remove = () => { if (timer) clearInterval(timer); origRemove(); };
    // keep the "thinking" bubble up long enough to be readable (no flash on fast replies)
    el.minWait = () => new Promise((r) => setTimeout(r, reduce ? 0 : Math.max(0, 1400 - (Date.now() - started))));
    return el;
  }

