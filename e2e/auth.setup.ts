import { test as setup, expect } from '@playwright/test';

const accounts = [
  {
    name: 'free',
    email: process.env.E2E_FREE_EMAIL!,
    password: process.env.E2E_FREE_PASSWORD!,
    file: 'e2e/playwright/.auth/free.json',
  },
  {
    name: 'pro',
    email: process.env.E2E_PRO_EMAIL!,
    password: process.env.E2E_PRO_PASSWORD!,
    file: 'e2e/playwright/.auth/pro.json',
  },
  {
    name: 'family-plus',
    email: process.env.E2E_FAMILY_PLUS_EMAIL!,
    password: process.env.E2E_FAMILY_PLUS_PASSWORD!,
    file: 'e2e/playwright/.auth/family-plus.json',
  },
] as const;

for (const account of accounts) {
  setup(`authenticate as ${account.name}`, async ({ page }) => {
    await page.goto('/auth/login', { timeout: 30_000 });
    await page.locator('#email').fill(account.email);
    await page.locator('#password').fill(account.password);
    await page.locator('.btn-primary').click();

    // Wait for the fetch-based login to complete and redirect to dashboard
    await page.waitForURL('**/dashboard', { timeout: 30_000 });

    // Verify we landed on an authenticated page (not redirected back to login)
    await expect(page).not.toHaveURL(/\/auth\/login/);

    // Save storage state for reuse across tests
    await page.context().storageState({ path: account.file });
  });
}
