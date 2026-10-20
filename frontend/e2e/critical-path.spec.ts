// S1-5.4 Playwright E2E: configure -> question -> answer -> complete -> results - owner: Christofer Arias
import { test, expect } from '@playwright/test';

test('Sprint 1 critical path', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'Set up a technical interview' }).click();

  // US-1 configure
  await expect(page.getByText('Set up your session')).toBeVisible();
  await page.getByLabel('Job title').fill('Junior Software Engineer');
  await page.getByRole('button', { name: /^Easy/ }).click();
  await page.getByRole('button', { name: /^15 min/ }).click();
  await page.getByRole('button', { name: 'Begin Interview' }).click();

  // US-2/US-3 answer one question at a time
  await expect(page).toHaveURL(/\/session\/\d+/);
  for (let i = 1; i <= 5; i++) {
    await expect(page.getByText(`Question ${i} of 5`)).toBeVisible();
    if (i === 3) {
      await page.getByRole('button', { name: 'Skip question' }).click();
    } else {
      await page.getByLabel('Your answer').fill('It uses memory and a pointer to each node; push and pop work on the top, LIFO.');
      await page.getByRole('button', { name: /Send answer/ }).click();
    }
  }

  // US-5 results
  await expect(page).toHaveURL(/\/results\/\d+/);
  await expect(page.getByRole('heading', { name: /Overall score: \d+ out of 100/ })).toBeVisible();
  await expect(page.locator('li.qcard')).toHaveCount(5);
  await expect(page.getByText('Skipped ·')).toBeVisible();

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
  await page.getByRole('button', { name: 'Begin Interview' }).click();
  await expect(page.getByRole('alert').first()).toContainText('Please fix 3 fields');
  await expect(page.getByLabel('Job title')).toBeFocused();
  await expect(page.getByLabel('Job title')).toHaveAttribute('aria-invalid', 'true');
  await expect(page.getByText('Choose a difficulty')).toBeVisible();
});

test('TC-002 rejects job titles with only numbers or special characters', async ({ page }) => {
  await page.goto('/setup');
  await page.getByRole('button', { name: /^Easy/ }).click();
  await page.getByRole('button', { name: /^15 min/ }).click();

  for (const title of ['12345', '!!!@@', '123!!']) {
    await page.getByLabel('Job title').fill(title);
    await page.getByRole('button', { name: 'Begin Interview' }).click();
    await expect(page.getByRole('alert').first()).toContainText('Please fix 1 field');
    await expect(page.getByText('Job title must include letters')).toBeVisible();
    await expect(page.getByLabel('Job title')).toBeFocused();
    await expect(page.getByLabel('Job title')).toHaveAttribute('aria-invalid', 'true');
    await expect(page).toHaveURL(/\/setup$/);
  }

  // titles with letters plus numbers or symbols are still fine
  await page.getByLabel('Job title').fill('C++ Developer');
  await page.getByRole('button', { name: 'Begin Interview' }).click();
  await expect(page).toHaveURL(/\/session\/\d+/);
});

test('empty answer asks the user to type or skip', async ({ page }) => {
  await page.goto('/setup');
  await page.getByLabel('Job title').fill('Backend Developer');
  await page.getByRole('button', { name: /^Medium/ }).click();
  await page.getByRole('button', { name: /^30 min/ }).click();
  await page.getByRole('button', { name: 'Begin Interview' }).click();
  await expect(page.getByText('Question 1 of 8')).toBeVisible();
  await page.getByRole('button', { name: 'Send answer' }).click();
  await expect(page.locator('p.field-err[role=alert]')).toContainText('Skip question');
  await page.getByRole('button', { name: 'End now' }).click();
  await expect(page.getByRole('heading', { name: 'Overall score: 0 out of 100' })).toBeVisible();
  await expect(page.getByText('Not answered ·')).toBeVisible();
});
