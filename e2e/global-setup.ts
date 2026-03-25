import { request } from '@playwright/test';

/**
 * Warm up the Railway server before tests to avoid cold-start timeouts.
 */
async function globalSetup() {
  const baseURL = process.env.E2E_BASE_URL || 'https://synco-production-e9da.up.railway.app';

  console.log(`Warming up server at ${baseURL}...`);
  const ctx = await request.newContext({ baseURL });

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const response = await ctx.get('/auth/login', { timeout: 60_000 });
      console.log(`Server warm (attempt ${attempt}): status ${response.status()}`);
      await ctx.dispose();
      return;
    } catch (e) {
      console.log(`Warmup attempt ${attempt} failed, retrying...`);
    }
  }

  await ctx.dispose();
  console.warn('Server warmup failed after 3 attempts — tests may be slow');
}

export default globalSetup;
