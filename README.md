# S1-1.1 · Kobra Amiri

**Interview setup screen (Next.js)**  
US-1 Configure Technical Interview · PM / UX

## Files in this folder

- `prototype_code.js` — the prototype code you own, with explanations (reference copy; the app runs from the original files).
- `setup_page.tsx` — your Sprint 1 starter. The structure and TODOs are there; you write the implementation.

## Where it is in the prototype

- static/index.html: the section with id="view-setup" (track cards, difficulty, length, mode, job title, Begin button)
- static/js/app.js: the SETUP block (state object, bindSeg(), startInterview())

## How it works

- Every choice the user makes is stored in one JavaScript object called state (track, difficulty, length, mode).
- Each option is a button with aria-pressed="true/false"; bindSeg() switches which button is pressed and writes the value into state.
- Clicking Begin calls startInterview(), which sends state to the server with POST /api/interviews and then opens the interview screen.

## What you build for Sprint 1

- Create the Next.js setup page with: job title input, interview type fixed to Technical, difficulty selector, 15/30/45-minute selector, and a Begin Interview button.
- Keep the selections in React state and send them to Owen's start-session endpoint (S1-1.2).
- Reuse the look of the prototype (cards + segmented buttons) so the demo stays consistent.

## Done when

Usable setup UI connected to local state and the agreed API contract.

## Explain it in one sentence

> I built the page where the user picks job title, difficulty and length; it saves those choices in state and starts the session through the API.

## Workflow

1. Branch: `feature/S1-1.1-interview_setup_screen_next_js`
2. Implement the TODOs in your starter file, add tests, open a pull request.
3. Get one review, make sure CI passes, then merge.
