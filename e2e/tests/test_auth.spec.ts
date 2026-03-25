import { test, expect, type Browser } from '@playwright/test';

test.describe('Auth', () => {
  test.describe('unauthenticated flows', () => {
    test.use({ storageState: { cookies: [], origins: [] } });

    test('valid login redirects to dashboard', async ({ page }) => {
      await page.goto('/auth/login');
      await expect(page.locator('#loginForm')).toBeVisible();

      await page.locator('#email').fill(process.env.E2E_PRO_EMAIL!);
      await page.locator('#password').fill(process.env.E2E_PRO_PASSWORD!);
      await page.locator('.btn-primary').click();

      await page.waitForURL('**/dashboard**');
      await expect(page).toHaveURL(/\/dashboard/);
    });

    test('invalid login shows error message', async ({ page }) => {
      await page.goto('/auth/login');

      await page.locator('#email').fill('wrong@example.com');
      await page.locator('#password').fill('wrongpassword123');
      await page.locator('.btn-primary').click();

      await expect(page.locator('#error')).toBeVisible();
      await expect(page.locator('#error')).not.toBeEmpty();
      await expect(page).toHaveURL(/\/auth\/login/);
    });

    test('register page renders form', async ({ page }) => {
      await page.goto('/auth/register');

      await expect(page.locator('#registerForm')).toBeVisible();
      await expect(page.locator('#email')).toBeVisible();
      await expect(page.locator('#password')).toBeVisible();
      await expect(page.locator('.btn-primary')).toBeVisible();
      // DO NOT submit — would create a real user in production
    });
  });

  test('logout clears session and redirects to login', async ({ page }) => {
    // Verify initially authenticated (uses stored auth from pro project)
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/dashboard/);

    // Navigate to logout
    await page.goto('/auth/logout');
    await page.waitForURL('**/auth/login**');
    await expect(page).toHaveURL(/\/auth\/login/);

    // Verify session cleared — accessing dashboard should redirect to login
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/auth\/login/);
  });
});
