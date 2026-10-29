// S2 Playwright E2E: timed and untimed interviews, and the fallback to untimed.
// Written ahead of the feature: each test skips until the setup page offers a "Timed" choice.
// Expected UI: setup has "Timed" and "Untimed" choices (toggle buttons or radios), and
// POST /api/sessions sends `timed`. A timed interview shows role="timer" counting down;
// an untimed one shows no timer and never ends on its own. If the timer data is missing
// or broken, the page runs the interview untimed instead of failing.
import { test, expect, type Page, type Request } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  const email = process.env.E2E_EMAIL, password = process.env.E2E_PASSWORD;
  if (!email || !password) return;
  await page.goto('/login');
  await page.getByLabel('Email').fill(email);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Log in', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Log out' })).toBeVisible();
});

const choice = (page: Page, name: RegExp) =>
  page.getByRole('button', { name }).or(page.getByRole('radio', { name }));
const timedChoice = (page: Page) => choice(page, /^Timed\b/);
const untimedChoice = (page: Page) => choice(page, /^Untimed\b/);

async function openSetup(page: Page) {
  await page.goto('/setup');
  await expect(page.getByText('Set up your session')).toBeVisible();
  test.skip((await timedChoice(page).count()) === 0, 'Timed interviews not on the setup page yet');
}

// Fill the setup form, press Begin Interview and return the start request.
async function begin(page: Page, timed: boolean): Promise<Request> {
  await page.getByLabel('Job title').fill('Junior Software Engineer');
  await page.getByRole('button', { name: /^Easy/ }).click();
  await page.getByRole('button', { name: /^15 min/ }).click();
  await (timed ? timedChoice(page) : untimedChoice(page)).click();
  const started = page.waitForRequest((r) => r.method() === 'POST' && new URL(r.url()).pathname === '/api/sessions');
  await page.getByRole('button', { name: 'Begin Interview' }).click();
  const request = await started;
  await expect(page).toHaveURL(/\/session\/\d+/);
  await expect(page.getByText('Question 1 of 5')).toBeVisible();
  return request;
}

async function secondsShown(page: Page): Promise<number> {
  const label = (await page.getByRole('timer').getAttribute('aria-label')) ?? '';
  const m = label.match(/(\d+):(\d{2})/);
  expect(m, `timer label "${label}" shows m:ss`).not.toBeNull();
  return Number(m![1]) * 60 + Number(m![2]);
}

// Make the backend's answer look like the timer failed, for every session request.
async function breakTimer(page: Page, patch: Record<string, unknown>) {
  await page.route(/\/api\/sessions(\/\d+)?$/, async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({ response, json: response.ok() ? { ...body, ...patch } : body });
  });
}

async function expectRunsUntimed(page: Page) {
  await expect(page.getByRole('timer')).toHaveCount(0);
  await page.waitForTimeout(2_500); // a broken deadline would end the interview at once
  await expect(page).toHaveURL(/\/session\/\d+/);
  await expect(page.getByText("Time's up")).toHaveCount(0);
  await page.getByLabel('Your answer').fill('A stack is LIFO: push adds to the top and pop removes it.');
  await page.getByRole('button', { name: /Send answer/ }).click();
  await expect(page.getByText('Question 2 of 5')).toBeVisible();
}

test('timer starts when the user chooses Timed and begins the interview', async ({ page }) => {
  await openSetup(page);
  await expect(page.getByRole('timer')).toHaveCount(0); // nothing is running before Begin

  const request = await begin(page, true);

  expect(request.postDataJSON()).toMatchObject({ timed: true });
  await expect(page.getByRole('timer')).toBeVisible();
  const first = await secondsShown(page);
  expect(first).toBeGreaterThan(14 * 60);
  expect(first).toBeLessThanOrEqual(15 * 60);
  await expect.poll(() => secondsShown(page), { timeout: 5_000 }).toBeLessThan(first);
});

test('timer keeps counting after a reload instead of restarting', async ({ page }) => {
  await openSetup(page);
  await begin(page, true);
  await page.waitForTimeout(3_000);

  await page.reload();

  await expect(page.getByRole('timer')).toBeVisible();
  expect(await secondsShown(page)).toBeLessThanOrEqual(15 * 60 - 2);
});

test('untimed interview shows no timer', async ({ page }) => {
  await openSetup(page);

  const request = await begin(page, false);

  expect(request.postDataJSON()).toMatchObject({ timed: false });
  await expectRunsUntimed(page);
});

test('falls back to untimed when the server could not start the timer', async ({ page }) => {
  await openSetup(page);
  await breakTimer(page, { timed: false, expires_at: null, seconds_left: null });

  const request = await begin(page, true);

  expect(request.postDataJSON()).toMatchObject({ timed: true });
  await expectRunsUntimed(page);
});

test('falls back to untimed when the timer data is broken', async ({ page }) => {
  await openSetup(page);
  await breakTimer(page, { timed: true, expires_at: null, seconds_left: null });

  await begin(page, true);

  await expectRunsUntimed(page);
});
