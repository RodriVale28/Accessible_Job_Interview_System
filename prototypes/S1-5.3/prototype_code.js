// ==========================================================================
// Interview Studio — S1-5.3: Results and feedback screen
// Owner (Sprint 1): Shegofa Ahmadi   |   Story: US-5 Evaluate Answers + Results
//
// This file collects the parts of the shared Interview Studio prototype that
// Shegofa Ahmadi owns. The prototype was built by the team before tasks were
// assigned; from Sprint 1 on, Shegofa maintains and extends this part.
// It is a reference copy — the running app still uses the original files.
//
// HOW IT WORKS
//  - The score ring is an SVG circle; its stroke-dashoffset is set from the score so the ring fills to the right percentage.
//  - Each question gets a card with the prompt, the user's answer, the score and the tip.
//
// YOUR SPRINT 1 WORK (see the starter file in this folder)
//  - Build the Next.js results page from Aisha's feedback payload: overall score, per-answer feedback, missing-answer notes, and Retry / Start new session buttons.
//  - Keep it accessible: headings in order, the score also given as text, buttons reachable by keyboard.
// ==========================================================================

// --------------------------------------------------------------------------
// FROM: static/index.html, lines 227-254
// WHAT IT DOES: Results screen markup: score ring, strengths, improvements, question-by-question list.
// --------------------------------------------------------------------------
/* --- HTML (static/index.html) ---
      <section class="view" id="view-report" hidden>
        <div class="wrap" style="padding-block:34px 40px">
          <p class="section-label">Interview report</p>
          <div class="panel pad">
            <div class="report-hero">
              <svg class="big-ring" viewBox="0 0 42 42" aria-hidden="true">
                <circle cx="21" cy="21" r="16" fill="none" stroke="var(--line)" stroke-width="4"/>
                <circle id="rep-ring" cx="21" cy="21" r="16" fill="none" stroke="var(--amber)" stroke-width="4" stroke-linecap="round" stroke-dasharray="100.5" stroke-dashoffset="100.5" transform="rotate(-90 21 21)"/>
                <text id="rep-score" x="21" y="25" text-anchor="middle" font-size="12" fill="var(--ink)" font-family="var(--font-mono)">–</text>
              </svg>
              <div>
                <h2>Nice work — here's how it went</h2>
                <p class="muted" style="margin:0">Your overall score, strengths, and where to focus next.</p>
              </div>
            </div>
            <div class="rband">
              <div class="rcard good"><h5>Strengths</h5><p id="rep-strengths" style="margin:0"></p></div>
              <div class="rcard grow"><h5>Where to improve</h5><p id="rep-improve" style="margin:0"></p></div>
            </div>
            <p class="section-label" style="margin-top:26px">Question-by-question</p>
            <div class="hist" id="rep-transcript"></div>
            <div style="display:flex;gap:10px;margin-top:22px;flex-wrap:wrap">
              <button class="btn amber" id="rep-new">Practice again</button>
              <button class="btn primary" id="rep-history">View history</button>
            </div>
          </div>
        </div>
      </section>
--- end HTML --- */

// --------------------------------------------------------------------------
// FROM: static/js/app.js, lines 404-418
// WHAT IT DOES: Fills the results screen from the API response.
// --------------------------------------------------------------------------
  function renderReport(report, transcript) {
    $("#rep-score").textContent = report.overall;
    $("#rep-ring").setAttribute("stroke-dashoffset", (100.5 * (1 - report.overall / 100)).toFixed(1));
    $("#rep-strengths").textContent = report.strengths;
    $("#rep-improve").textContent = report.improvements;
    const list = $("#rep-transcript"); list.innerHTML = "";
    (transcript || []).forEach((row) => {
      const d = document.createElement("div"); d.className = "rcard";
      d.innerHTML = `<h5>Q${row.q_index} · ${row.confidence != null ? row.confidence + "/100" : "—"}</h5>
        <p style="margin:0 0 8px;font-weight:600">${escapeHtml(row.prompt)}</p>
        <p style="margin:0 0 8px" class="muted">${escapeHtml(row.answer || "(no answer)")}</p>
        ${row.tip ? `<p style="margin:0" class="muted"><b>Tip:</b> ${escapeHtml(row.tip)}</p>` : ""}`;
      list.appendChild(d);
    });
  }

