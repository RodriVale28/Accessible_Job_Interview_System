// ==========================================================================
// Interview Studio — S1-1.1: Interview setup screen (Next.js)
// Owner (Sprint 1): Kobra Amiri   |   Story: US-1 Configure Technical Interview
//
// This file collects the parts of the shared Interview Studio prototype that
// Kobra Amiri owns. The prototype was built by the team before tasks were
// assigned; from Sprint 1 on, Kobra maintains and extends this part.
// It is a reference copy — the running app still uses the original files.
//
// HOW IT WORKS
//  - Every choice the user makes is stored in one JavaScript object called state (track, difficulty, length, mode).
//  - Each option is a button with aria-pressed="true/false"; bindSeg() switches which button is pressed and writes the value into state.
//  - Clicking Begin calls startInterview(), which sends state to the server with POST /api/interviews and then opens the interview screen.
//
// YOUR SPRINT 1 WORK (see the starter file in this folder)
//  - Create the Next.js setup page with: job title input, interview type fixed to Technical, difficulty selector, 15/30/45-minute selector, and a Begin Interview button.
//  - Keep the selections in React state and send them to Owen's start-session endpoint (S1-1.2).
//  - Reuse the look of the prototype (cards + segmented buttons) so the demo stays consistent.
// ==========================================================================

// --------------------------------------------------------------------------
// FROM: static/index.html, lines 84-152
// WHAT IT DOES: The setup screen markup: track cards, difficulty/length/mode buttons, accessibility toggles, job-description box, Begin button.
// --------------------------------------------------------------------------
/* --- HTML (static/index.html) ---
      <section class="view" id="view-setup" hidden>
        <div class="wrap hero">
          <p class="section-label">Set up your session</p>
          <div class="panel pad">
            <div class="setup-grid">
              <div>
                <div class="opt-group">
                  <span class="glabel">Interview track</span>
                  <div class="tracks" id="track-group" role="group" aria-label="Interview track">
                    <button class="track" data-track="Behavioral" aria-pressed="true">
                      <span class="ico"><svg viewBox="0 0 24 24" fill="none"><path d="M8 12h8M8 8h8m-8 8h5M4 4h16v12H8l-4 4V4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg></span>
                      <span><span class="tt">Behavioral</span><span class="td">STAR stories & judgment</span></span><span class="chk"></span>
                    </button>
                    <button class="track" data-track="Technical / Coding" aria-pressed="false">
                      <span class="ico"><svg viewBox="0 0 24 24" fill="none"><path d="m8 9-3 3 3 3m8-6 3 3-3 3m-3-9-2 12" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></span>
                      <span><span class="tt">Technical / Coding</span><span class="td">Problem-solving out loud</span></span><span class="chk"></span>
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <div class="opt-group">
                  <span class="glabel">Difficulty</span>
                  <div class="seg" id="diff-group" role="group" aria-label="Difficulty">
                    <button data-difficulty="Warm-up" aria-pressed="false">Warm-up</button>
                    <button data-difficulty="Standard" aria-pressed="true">Standard</button>
                    <button data-difficulty="Onsite" aria-pressed="false">Onsite</button>
                  </div>
                </div>
                <div class="opt-group">
                  <span class="glabel">Length</span>
                  <div class="seg" id="len-group" role="group" aria-label="Session length">
                    <button data-length="15" aria-pressed="true">15 min</button>
                    <button data-length="30" aria-pressed="false">30 min</button>
                    <button data-length="45" aria-pressed="false">45 min</button>
                  </div>
                </div>
                <div class="opt-group">
                  <span class="glabel">Mode</span>
                  <div class="seg" id="mode-group" role="group" aria-label="Mode">
                    <button data-mode="mock" aria-pressed="true">Full mock</button>
                    <button data-mode="practice" aria-pressed="false">One-off question</button>
                  </div>
                </div>
                <div class="opt-group">
                  <div class="toggle-row">
                    <span><span class="tt">Read questions aloud</span><span class="td">Text-to-speech</span></span>
                    <button class="switch" id="aloud-switch" role="switch" aria-checked="false" aria-label="Read questions aloud"></button>
                  </div>
                  <div class="toggle-row">
                    <span><span class="tt">Voice answers</span><span class="td">Speak instead of typing</span></span>
                    <button class="switch" id="voice-switch" role="switch" aria-checked="false" aria-label="Voice answers"></button>
                  </div>
                </div>
              </div>
            </div>

            <!-- job-description based questions (F2, R5) -->
            <div class="opt-group" id="jd-wrap">
              <span class="glabel">Tailor to a job (optional)</span>
              <div class="form-row"><input type="text" id="f-jobtitle" placeholder="Job title — e.g. Junior Mobile Developer"></div>
              <div class="form-row"><textarea id="f-jd" rows="3" placeholder="Paste a job description and questions will be generated from the skills it names."></textarea></div>
            </div>

            <button class="btn amber full" id="begin-btn"><svg viewBox="0 0 24 24" fill="none"><path d="M5 3.5 19 12 5 20.5V3.5Z" fill="currentColor"/></svg>Begin interview</button>
          </div>
        </div>
      </section>
--- end HTML --- */

// --------------------------------------------------------------------------
// FROM: static/js/app.js, lines 105-222
// WHAT IT DOES: Setup logic: button groups write into `state`; startInterview() sends state to POST /api/interviews and shows the 'Ava is preparing' animation while it waits.
// --------------------------------------------------------------------------
  /* =========================================================================
     SETUP (R3, R4, R5, F2, F8)
     ========================================================================= */
  $$("#track-group .track").forEach((btn) =>
    btn.addEventListener("click", () => {
      $$("#track-group .track").forEach((b) => b.setAttribute("aria-pressed", "false"));
      btn.setAttribute("aria-pressed", "true");
      state.track = btn.dataset.track;
    })
  );
  bindSeg("#diff-group", "difficulty", (v) => (state.difficulty = v));
  bindSeg("#len-group", "length", (v) => (state.length = parseInt(v)));
  bindSeg("#mode-group", "mode", (v) => {
    state.mode = v;
    $("#jd-wrap").hidden = false; // job description available in both modes
  });

  function bindSeg(sel, key, cb) {
    const btns = $$(sel + " button");
    btns.forEach((b) =>
      b.addEventListener("click", () => {
        btns.forEach((x) => x.setAttribute("aria-pressed", "false"));
        b.setAttribute("aria-pressed", "true");
        cb(b.dataset[key]);
      })
    );
  }

  $("#voice-switch").addEventListener("click", () => toggleSwitch("#voice-switch", (on)=>state.voice=on));
  $("#aloud-switch").addEventListener("click", () => toggleSwitch("#aloud-switch", (on)=>{
    state.readAloud=on;
    if(state.user) api("/api/prefs","POST",{text_scale:{sm:90,md:100,lg:115,xl:130}[document.body.dataset.scale||"md"],read_aloud:on}).catch(()=>{});
  }));
  function toggleSwitch(sel, cb){ const el=$(sel); const on=el.getAttribute("aria-checked")==="true"; el.setAttribute("aria-checked",(!on).toString()); cb(!on); }

  $("#begin-btn").addEventListener("click", startInterview);

  async function startInterview() {
    $("#begin-btn").disabled = true;
    const jd = $("#f-jd").value.trim();
    // show the "Ava is preparing" screen right away
    $("#stage").hidden = true; $("#analyzing").hidden = false;
    show("interview");
    const anim = runAnalyzing(jd);
    try {
      const [r] = await Promise.all([
        api("/api/interviews", "POST", {
          track: state.track, difficulty: state.difficulty, mode: state.mode,
          length: state.length,
          job_title: $("#f-jobtitle").value, job_description: jd,
        }),
        anim.done,
      ]);
      await anim.finish();
      state.interviewId = r.interview_id; state.qIndex = r.q_index;
      state.total = r.total; state.currentQ = r.question;
      $("#analyzing").hidden = true;
      const st = $("#stage"); st.hidden = false; st.classList.remove("enter"); void st.offsetWidth; st.classList.add("enter");
      setupStage(r);
    } catch (err) {
      anim.cancel(); $("#analyzing").hidden = true; $("#stage").hidden = false;
      show("setup");
      alert(err.message); // NF12 retry-friendly
    } finally { $("#begin-btn").disabled = false; }
  }

  /* ---- "Ava is preparing your interview" step animation ----
     Purely visual: it runs while the real /api/interviews call is in flight,
     then the last step completes once the questions have actually arrived. */
  const SKILL_WORDS = ["python","java","javascript","typescript","react","node","flask","django","sql","mysql",
    "postgres","mongodb","aws","azure","docker","kubernetes","git","rest","api","swift","kotlin","flutter",
    "android","ios","c++","c#","html","css","linux","agile","scrum","machine learning","data structures",
    "algorithms","testing","ci/cd","communication","leadership","teamwork","cloud","security"];
  function findSkills(text) {
    const t = " " + text.toLowerCase() + " ";
    return SKILL_WORDS.filter((w) => {
      const esc = w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
      return new RegExp("(^|[^a-z])" + esc + "([^a-z]|$)").test(t);
    }).slice(0, 8);
  }
  function runAnalyzing(jd) {
    const steps = [
      `Reading your session setup`,
      jd ? `Analyzing the job description for key skills` : `Searching the ${state.track} question bank`,
      `Generating tailored questions with AI`,
      `Calibrating to ${state.difficulty} difficulty`,
      `Ava is ready`,
    ];
    $("#an-sub").textContent = `${state.track} · ${state.difficulty} · ${state.mode === "practice" ? "One-off question" : state.length + " min"}`;
    const list = $("#an-steps"); list.innerHTML = "";
    const chips = $("#an-chips"); chips.innerHTML = "";
    const items = steps.map((t) => { const li = document.createElement("li"); li.innerHTML = `<span class="dot"></span><span></span>`; li.lastChild.textContent = t; list.appendChild(li); return li; });
    const bar = $("#an-bar"); bar.style.width = "0%";
    const skills = jd ? findSkills(jd) : [];
    const STEP_MS = reduce ? 0 : 650;
    let cancelled = false;
    const wait = (ms) => new Promise((res) => setTimeout(res, ms));
    const mark = (i, cls) => { items[i].className = cls; bar.style.width = Math.round(((i + (cls === "done" ? 1 : .5)) / items.length) * 100) + "%"; };

    // steps 0..3 animate on a timer; step 4 waits for the real API response
    const done = (async () => {
      for (let i = 0; i < 4 && !cancelled; i++) {
        mark(i, "active");
        if (i === 1 && skills.length) {
          for (const sk of skills) { if (cancelled) break; const c = document.createElement("span"); c.textContent = sk; chips.appendChild(c); await wait(reduce ? 0 : 140); }
        }
        await wait(STEP_MS);
        mark(i, "done");
      }
      if (!cancelled) mark(4, "active");
    })();
    return {
      done,
      finish: async () => { mark(4, "done"); await wait(reduce ? 0 : 450); },
      cancel: () => { cancelled = true; },
    };
  }

