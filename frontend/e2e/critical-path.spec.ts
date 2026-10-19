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
