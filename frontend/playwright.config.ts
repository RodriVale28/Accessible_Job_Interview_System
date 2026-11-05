// Playwright config. E2E specs owned by Christofer (S1-5.4, S2-X.2).
// Start the backend (port 8000, ALLOW_GUEST=1, AI_ENABLED=0) and the front end (port 3000) first,
// or set E2E_BASE_URL to the Render URL to test the deployed site (with E2E_EMAIL / E2E_PASSWORD).
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  forbidOnly: !!process.env.CI, // a stray test.only must not hide the rest of the suite in CI
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    launchOptions: process.env.PW_CHROMIUM_PATH ? { executablePath: process.env.PW_CHROMIUM_PATH } : {},
    // keep what is needed to debug a failure: a trace (npx playwright show-trace) and a screenshot
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
});
