import { test, expect } from '@playwright/test';

test.describe('Notifications', () => {
  test('bell icon visible in navbar', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    await expect(page.locator('#notification-bell-container')).toBeVisible();
    await expect(page.locator('#notification-bell')).toBeVisible();
  });

  test('bell click loads notification dropdown', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Bell button should be visible
    await expect(page.locator('#notification-bell')).toBeVisible();

    // Click bell and wait for HTMX dropdown response
    await Promise.all([
      page.waitForResponse(
        (resp) =>
          resp.url().includes('/notifications/dropdown') &&
          resp.status() === 200,
      ),
      page.locator('#notification-bell').click(),
    ]);

    // Notification panel should become visible after HTMX loads content
    await expect(page.locator('#notification-panel')).toBeVisible();
  });
});
