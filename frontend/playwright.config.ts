// Playwright config. Critical-path spec owned by Christofer (S1-5.4).
// Start the backend (port 8000) and the front end (port 3000) first, or set E2E_BASE_URL
// to the Render URL to test the deployed site.
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:3000',
    launchOptions: process.env.PW_CHROMIUM_PATH ? { executablePath: process.env.PW_CHROMIUM_PATH } : {},
  },
});
