\# S1-5.3 · Shegofa Ahmadi



\*\*Results and feedback screen\*\*  

US-5 Evaluate Answers + Results · UX / AI



\## Files in this folder



\- `prototype\_code.js` — the prototype code you own, with explanations (reference copy; the app runs from the original files).

\- `results\_page.tsx` — your Sprint 1 starter. The structure and TODOs are there; you write the implementation.



\## Where it is in the prototype



\- static/index.html: section id="view-report"

\- static/js/app.js: renderReport() — score ring, strengths, improvements, question-by-question cards, Practice again



\## How it works



\- The score ring is an SVG circle; its stroke-dashoffset is set from the score so the ring fills to the right percentage.

\- Each question gets a card with the prompt, the user's answer, the score and the tip.



\## What you build for Sprint 1



\- Build the Next.js results page from Aisha's feedback payload: overall score, per-answer feedback, missing-answer notes, and Retry / Start new session buttons.

\- Keep it accessible: headings in order, the score also given as text, buttons reachable by keyboard.



\## Done when



Accessible results screen integrated with the US-5 API response.



\## Explain it in one sentence



> I built the results screen that shows the overall score and per-question feedback, with a button to practise again.



\## Workflow



1\. Branch: `feature/S1-5.3-results\_and\_feedback\_screen`

2\. Implement the TODOs in your starter file, add tests, open a pull request.

3\. Get one review, make sure CI passes, then merge.



