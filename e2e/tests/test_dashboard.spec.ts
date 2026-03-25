import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('loads as home page for authenticated user', async ({ page }) => {
    await page.goto('/');

    // Authenticated user should be redirected to dashboard
    await page.waitForURL('**/dashboard**');
    await expect(page).toHaveURL(/\/dashboard/);

    // Page should render content
    await expect(page.locator('body')).not.toBeEmpty();
  });

  test('shows today events section', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Today's events heading (h2.text-section-title) should be visible
    await expect(
      page.locator('h2.text-section-title').first(),
    ).toBeVisible();
  });

  test('shows budget snapshot and quick-add', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');

    // Full event link to calendar should exist
    await expect(
      page.locator('a[href="/calendar?open=event-entry"]'),
    ).toBeVisible();

    // Dashboard should have multiple glass cards (events, week preview, budget)
    const glassCards = page.locator('.glass');
    const count = await glassCards.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });
});
