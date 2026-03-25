import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  globalSetup: './global-setup.ts',
  testDir: '.',
  timeout: 60_000,
  expect: {
    timeout: 10_000,
  },
  retries: 1,
  reporter: process.env.CI ? 'github' : 'html',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'https://synco-production-e9da.up.railway.app',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    navigationTimeout: 60_000,
  },
  projects: [
    {
      name: 'setup',
      testMatch: '**/auth.setup.ts',
      fullyParallel: false,
    },
    {
      name: 'free',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/playwright/.auth/free.json',
      },
      dependencies: ['setup'],
      testDir: './tests',
    },
    {
      name: 'pro',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/playwright/.auth/pro.json',
      },
      dependencies: ['setup'],
      testDir: './tests',
    },
    {
      name: 'family-plus',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'e2e/playwright/.auth/family-plus.json',
      },
      dependencies: ['setup'],
      testDir: './tests',
    },
  ],
});
