// S1-5.4 / S2-X.2 Playwright E2E - owner: Christofer Arias
// Sprint 1 critical path plus the Sprint 2 demo path. Runs in guest mode with the AI off
// (local and CI), or against the Render site with E2E_EMAIL / E2E_PASSWORD set.
//
// The setup page is being rebuilt (S2-1.5). Until that lands, main still has the Sprint 1 form
// (Easy / 15 min / Begin Interview). The helpers below detect which form is on the page and drive
// either one, so these specs pass on main today and keep passing when the new form merges.
// Steps whose feature is not on main yet are skipped with the task id they are waiting for.
import { test, expect, type Page } from '@playwright/test';

type Level = 'Easy' | 'Medium' | 'Hard';
type Length = 'Short' | 'Medium' | 'Long';
type InterviewType = 'Technical' | 'Behavioral' | 'Mixed';
type SetupOptions = { jobTitle: string; level?: Level; length?: Length; type?: InterviewType };

// Sprint 2 shows friendlier labels; the values sent to the API stay Easy / Medium / Hard and 15 / 30 / 45.
const LEVEL_LABEL: Record<Level, string> = { Easy: 'Warm-up', Medium: 'Standard', Hard: 'Challenge' };
const LENGTH_MINUTES: Record<Length, number> = { Short: 15, Medium: 30, Long: 45 };
const QUESTIONS: Record<Length, number> = { Short: 5, Medium: 8, Long: 10 };

// Soft labels (section 7 of the master doc). The overall label comes from the backend (S2-2.2).
const SOFT_LABEL = /^(Strong|Getting there|Room to grow)$/;
// Sprint 1 results say "Skipped · 0/100 ..."; S2-2.3 changes it to "Skipped: one to work on".
const SKIP_LABEL = /Skipped( ·|: one to work on)/;
const SOFT_SKIP_LABEL = 'Skipped: one to work on';
const GOOD_ANSWER = 'It uses memory and a pointer to each node; push and pop work on the top, LIFO.';

// Login builds (NEXT_PUBLIC_SUPABASE_* set, e.g. the Render site) need a test account:
// set E2E_EMAIL and E2E_PASSWORD. Guest-mode builds (local, CI) skip this.
test.beforeEach(async ({ page }) => {
  const email = process.env.E2E_EMAIL, password = process.env.E2E_PASSWORD;
  if (!email || !password) return;
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Log in', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
});

// ---------- helpers ----------

/** Which setup form is on /setup: the Sprint 1 one-page form, or the S2-1.5 form with a "What to expect" step. */
async function setupForm(page: Page): Promise<'sprint1' | 'sprint2'> {
  await expect(page.getByRole('heading', { name: 'Interview setup' })).toBeVisible();
  const submit = page.getByRole('button', { name: /^(Begin Interview|Continue)$/ });
  await expect(submit).toBeVisible();
  return (await submit.textContent())?.trim() === 'Continue' ? 'sprint2' : 'sprint1';
}

/** Role choices offered by the S2-1.5 form (empty until roles are seeded, S2-1.3). */
async function roleOptions(page: Page): Promise<string[]> {
  const options = await page.getByLabel('Role to practice').locator('option').allTextContents();
  return options.filter((o) => o.trim() && o !== 'Choose a role');
}

/** Fill the setup form and submit it. On the Sprint 2 form this stops on "What to expect". */
async function fillSetup(page: Page, opts: SetupOptions): Promise<'sprint1' | 'sprint2'> {
  const form = await setupForm(page);
  const level = opts.level ?? 'Easy';
  const length = opts.length ?? 'Short';

  if (form === 'sprint1') {
    await page.getByLabel('Job title').fill(opts.jobTitle);
    await page.getByRole('button', { name: new RegExp(`^${level}`) }).click();
    await page.getByRole('button', { name: new RegExp(`^${LENGTH_MINUTES[length]} min`) }).click();
    await page.getByRole('button', { name: 'Begin Interview' }).click();
    return form;
  }

  await page.getByLabel('Job title').fill(opts.jobTitle);
  await page.getByLabel('Job title').blur(); // leaving the field runs role matching
  const submit = page.getByRole('button', { name: 'Continue' });
  await expect(submit).toBeEnabled(); // "Matching your role…" while the match is running
  // If the title did not match a role, pick the first one offered.
  const role = page.getByLabel('Role to practice');
  if (!(await role.inputValue()) && (await roleOptions(page)).length > 0) {
    await role.selectOption({ index: 1 });
  }
  // Interview type is set after the role, because choosing a role resets it.
  if (opts.type) {
    await page.getByRole('group', { name: 'Interview type' }).getByRole('button', { name: opts.type }).click();
  }
  await page.getByRole('group', { name: 'Difficulty' }).getByRole('button', { name: LEVEL_LABEL[level] }).click();
  await page.getByRole('group', { name: 'Interview length' }).getByRole('button', { name: new RegExp(`^${length}`) }).click();
  await submit.click();
  return form;
}

/** Set up an interview from /setup and land on question 1. */
async function startInterview(page: Page, opts: SetupOptions) {
  const form = await fillSetup(page, opts);
  if (form === 'sprint2') {
    const expectHeading = page.getByRole('heading', { name: 'What to expect' });
    const noRole = page.getByText('Choose the role you want to practice for.');
    await expect(expectHeading.or(noRole)).toBeVisible();
    // With no roles to choose (none seeded yet), S2-1.5 must still let the user start (role_id null).
    expect(await noRole.count(), 'setup is blocked: no role to choose. S2-1.5 should fall back to role_id null until roles are seeded').toBe(0);
    await expect(expectHeading).toBeFocused();
    await page.getByRole('button', { name: 'Start interview' }).click();
  }
  await expect(page).toHaveURL(/\/session\/\d+/);
  await expect(page.getByText(`Question 1 of ${QUESTIONS[opts.length ?? 'Short']}`)).toBeVisible();
}

/** Check that an element's text and background are gray (no strong hue), e.g. a skipped answer. */
async function expectNeutral(page: Page, text: string) {
  const colors = await page.getByText(text).first().evaluate((el) => {
    const s = getComputedStyle(el);
    return [s.color, s.backgroundColor];
  });
  for (const c of colors) {
    const [r, g, b, a = 1] = (c.match(/[\d.]+/g) ?? []).map(Number);
    if (a === 0) continue; // transparent background
    expect(Math.max(r, g, b) - Math.min(r, g, b), `${text} should be gray, got ${c}`).toBeLessThanOrEqual(30);
  }
}

// ---------- Sprint 1 critical path ----------

test('Sprint 1 critical path', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: /^Set up a/ }).click();

  // US-1 configure
  await expect(page.getByText('Set up your session')).toBeVisible();
  await startInterview(page, { jobTitle: 'Junior Software Engineer', level: 'Easy', length: 'Short' });

  // US-2/US-3 answer one question at a time
  for (let i = 1; i <= 5; i++) {
    await expect(page.getByText(`Question ${i} of 5`)).toBeVisible();
    if (i === 3) {
      await page.getByRole('button', { name: 'Skip question' }).click();
    } else {
      await page.getByLabel('Your answer').fill(GOOD_ANSWER);
      await page.getByRole('button', { name: /Send answer/ }).click();
    }
  }

  // US-5 results
  await expect(page).toHaveURL(/\/results\/\d+/);
  await expect(page.getByRole('heading', { name: /Overall score: \d+ out of 100/ })).toBeVisible();
  await expect(page.locator('li.qcard')).toHaveCount(5);
  await expect(page.getByText(SKIP_LABEL).first()).toBeVisible();

  // US-4 saved: reload still shows the same results
  const heading = await page.getByRole('heading', { name: /Overall score/ }).textContent();
  await page.reload();
  await expect(page.getByRole('heading', { name: /Overall score/ })).toHaveText(heading ?? '');

  // retry starts a new session
  await page.getByRole('button', { name: 'Retry with same setup' }).click();
  await expect(page.getByText('Question 1 of 5')).toBeVisible();
});

test('setup shows accessible errors for missing fields', async ({ page }) => {
  await page.goto('/setup');
  if ((await setupForm(page)) === 'sprint1') {
    await page.getByRole('button', { name: 'Begin Interview' }).click();
    await expect(page.getByRole('alert').first()).toContainText('Please fix 3 fields');
    await expect(page.getByText('Choose a difficulty')).toBeVisible();
  } else {
    // S2-1.5 preselects type, difficulty and length, so only the job title can be missing.
    await page.getByRole('button', { name: 'Continue' }).click();
    await expect(page.getByText('Enter the job title you are preparing for.')).toBeVisible();
  }
  await expect(page.getByLabel('Job title')).toBeFocused();
  await expect(page.getByLabel('Job title')).toHaveAttribute('aria-invalid', 'true');
  await expect(page).toHaveURL(/\/setup$/);
});

test('TC-002 rejects job titles with only numbers or special characters', async ({ page }) => {
  await page.goto('/setup');
  const form = await setupForm(page);

  for (const title of ['12345', '!!!@@', '123!!']) {
    await fillSetup(page, { jobTitle: title });
    if (form === 'sprint1') await expect(page.getByRole('alert').first()).toContainText('Please fix 1 field');
    await expect(page.getByText('Job title must include letters')).toBeVisible();
    await expect(page.getByLabel('Job title')).toBeFocused();
    await expect(page.getByLabel('Job title')).toHaveAttribute('aria-invalid', 'true');
    await expect(page).toHaveURL(/\/setup$/);
  }

  // titles with letters plus numbers or symbols are still fine
  await startInterview(page, { jobTitle: 'C++ Developer' });
});

test('empty answer asks the user to type or skip', async ({ page }) => {
  await page.goto('/setup');
  await startInterview(page, { jobTitle: 'Backend Developer', level: 'Medium', length: 'Medium' });
  await page.getByRole('button', { name: 'Send answer' }).click();
  await expect(page.locator('p.field-err[role=alert]')).toContainText('Skip question');
  await page.getByRole('button', { name: 'End now' }).click();
  await expect(page.getByRole('heading', { name: 'Overall score: 0 out of 100' })).toBeVisible();
  await expect(page.getByText(/Not answered ·|Skipped: one to work on/).first()).toBeVisible();
});

test('US-4 past interviews list reopens saved results', async ({ page }) => {
  await page.goto('/setup');
  await startInterview(page, { jobTitle: 'Data Engineer' });
  await page.getByRole('button', { name: 'End now' }).click();
  await expect(page).toHaveURL(/\/results\/\d+/);
  const resultsUrl = page.url();

  // leave and come back: the finished interview is listed and opens its results
  await page.goto('/');
  const past = page.getByRole('region', { name: 'Your past interviews' });
  await expect(past.getByRole('link', { name: 'Data Engineer' }).first()).toBeVisible();
  await past.getByRole('link', { name: 'Data Engineer' }).first().click();
  await expect(page).toHaveURL(resultsUrl);
});

// ---------- Sprint 2 demo path (S2-X.2) ----------
// One run through the demo: job title -> role, untimed Short interview with a skip, soft labels and a gray
// skip, history, practice, a Behavioral interview, and a settings change that survives a reload.

test('Sprint 2 demo path', async ({ page }) => {
  test.setTimeout(120_000);
  const jobTitle = `Junior Data Analyst ${Date.now() % 100000}`; // unique, so history shows this run

  await test.step('setup: "Junior Data Analyst" is matched to Data Analyst', async (step) => {
    await page.goto('/setup');
    const form = await setupForm(page);
    step.skip(form === 'sprint1', 'waiting for S2-1.5 (new setup page)');
    step.skip((await roleOptions(page)).length === 0, 'waiting for roles to be seeded (S2-1.3 roles_data)');
    await page.getByLabel('Job title').fill('Junior Data Analyst');
    await page.getByLabel('Job title').blur();
    await expect(page.getByText('We matched this to Data Analyst')).toBeVisible();
    await expect(page.getByLabel('Role to practice').locator('option:checked')).toHaveText('Data Analyst');
  });

  await test.step('untimed Short interview with one skip', async () => {
    await page.goto('/setup');
    // The session page loads its state once; check the API says there is no countdown.
    const sessionState = page.waitForResponse((r) => /\/api\/sessions\/\d+$/.test(r.url()) && r.request().method() === 'GET');
    await startInterview(page, { jobTitle, length: 'Short' });
    const state = await (await sessionState).json();
    expect(state.seconds_left, 'interview should be untimed').toBeNull();
    for (let i = 1; i <= QUESTIONS.Short; i++) {
      await expect(page.getByText(`Question ${i} of ${QUESTIONS.Short}`)).toBeVisible();
      if (i === 2) {
        await page.getByRole('button', { name: 'Skip question' }).click();
      } else {
        await page.getByLabel('Your answer').fill(GOOD_ANSWER);
        await page.getByRole('button', { name: /Send answer/ }).click();
      }
    }
    await expect(page).toHaveURL(/\/results\/\d+/);
  });

  await test.step('results show a soft label', async () => {
    await expect(page.getByText(SOFT_LABEL).first()).toBeVisible();
    await expect(page.getByText(SKIP_LABEL).first()).toBeVisible();
  });

  await test.step('results show the skip in neutral gray', async (step) => {
    step.skip(await page.getByText(SOFT_SKIP_LABEL).count() === 0, 'waiting for S2-2.3 (results page)');
    await expectNeutral(page, SOFT_SKIP_LABEL);
  });

  await test.step('history lists the interview', async () => {
    const resultsUrl = page.url();
    await page.goto('/');
    const past = page.getByRole('region', { name: 'Your past interviews' });
    await expect(past.getByRole('link', { name: jobTitle })).toBeVisible();
    await past.getByRole('link', { name: jobTitle }).click();
    await expect(page).toHaveURL(resultsUrl);
  });

  await test.step('practice one question', async () => {
    await page.goto('/practice');
    await page.getByLabel('Your answer').fill(GOOD_ANSWER);
    await page.getByRole('button', { name: 'See feedback' }).click();
    await expect(page.getByText(SOFT_LABEL).first()).toBeVisible();
    await expect(page.getByRole('button', { name: 'Try again' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Another question' })).toBeVisible();
  });

  await test.step('a Behavioral interview', async (step) => {
    await page.goto('/setup');
    step.skip((await setupForm(page)) === 'sprint1', 'waiting for S2-1.5 (interview type on the setup page)');
    await startInterview(page, { jobTitle: 'Customer Service Representative', type: 'Behavioral', length: 'Short' });
    await page.getByRole('button', { name: 'End now' }).click();
    await expect(page).toHaveURL(/\/results\/\d+/);
    await expect(page.getByText(/· Behavioral ·/)).toBeVisible();
  });

  await test.step('a settings change survives a reload', async (step) => {
    // Settings are applied as data-text-size / data-theme / data-font on <html> (S2-6.1).
    // TODO S2-6.1: check the control name against the settings panel when it merges, then remove the skip.
    step.skip(true, 'waiting for S2-6.1 / S2-4.1 (accessibility settings)');
    await page.goto('/');
    await page.getByLabel(/Text size/i).selectOption('lg');
    await expect(page.locator('html')).toHaveAttribute('data-text-size', 'lg');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-text-size', 'lg');
  });
});
