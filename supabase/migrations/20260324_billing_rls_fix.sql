-- Fix billing tables RLS and GRANT permissions
-- The backend accesses these tables server-side (no user JWT), so auth.uid() is NULL.
-- Previous policies blocked server-side reads/inserts because they required auth.uid().

-- 1. GRANT table permissions to all roles
GRANT SELECT, INSERT, UPDATE ON subscriptions TO anon, authenticated, service_role;
GRANT SELECT, INSERT ON billing_events TO anon, authenticated, service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated, service_role;

-- 2. Fix SELECT policies: allow server-side reads (auth.uid() IS NULL)
--    while preserving user-level reads via JWT
DROP POLICY IF EXISTS "Users can read own subscription" ON subscriptions;
CREATE POLICY "Allow subscription reads" ON subscriptions
  FOR SELECT USING (
    auth.uid() = user_id OR auth.uid() IS NULL
  );

DROP POLICY IF EXISTS "Users can read own billing events" ON billing_events;
CREATE POLICY "Allow billing event reads" ON billing_events
  FOR SELECT USING (
    auth.uid() = user_id OR auth.uid() IS NULL
  );
