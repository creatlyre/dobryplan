-- Create missing covering indexes for foreign keys
CREATE INDEX IF NOT EXISTS ix_calendar_invitations_calendar_id ON public.calendar_invitations (calendar_id);
CREATE INDEX IF NOT EXISTS ix_calendar_invitations_inviter_user_id ON public.calendar_invitations (inviter_user_id);
CREATE INDEX IF NOT EXISTS ix_calendars_owner_user_id ON public.calendars (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_events_created_by_user_id ON public.events (created_by_user_id);
CREATE INDEX IF NOT EXISTS ix_events_last_edited_by_user_id ON public.events (last_edited_by_user_id);

-- Drop unused indexes
DROP INDEX IF EXISTS ix_events_start_at;
DROP INDEX IF EXISTS ix_events_start_end;

-- Drop multiple permissive policies on expenses
DROP POLICY IF EXISTS "Allow all for service_role" ON public.expenses;
DROP POLICY IF EXISTS "expenses_all_access" ON public.expenses;

-- Add a unified policy for expenses
DROP POLICY IF EXISTS "Users can manage their own expenses" ON public.expenses;
CREATE POLICY "Users can manage their own expenses" ON public.expenses FOR ALL USING (
    calendar_id IN (SELECT calendar_id FROM public.users WHERE id = (SELECT auth.uid())::text)
);

-- Fix auth_rls_initplan in carry_forward_overrides
DROP POLICY IF EXISTS "Users can manage their own carry-forward overrides" ON public.carry_forward_overrides;
CREATE POLICY "Users can manage their own carry-forward overrides" ON public.carry_forward_overrides FOR ALL USING (
    calendar_id IN (SELECT calendar_id FROM public.users WHERE id = (SELECT auth.uid())::text)
);
