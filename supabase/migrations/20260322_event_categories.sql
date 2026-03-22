-- Event categories table
create table if not exists public.event_categories (
  id uuid primary key default gen_random_uuid(),
  calendar_id text not null references public.calendars(id) on delete cascade,
  name text not null,
  color text not null,
  is_preset boolean not null default false,
  sort_order int not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (calendar_id, name)
);

alter table public.event_categories enable row level security;

create policy "Users can manage their own event categories"
  on public.event_categories
  for all
  using (
    calendar_id in (
      select u.calendar_id from public.users u
      where u.google_id::text = auth.uid()::text
         or lower(u.email::text) = lower(coalesce(auth.jwt() ->> 'email', ''))
    )
  )
  with check (
    calendar_id in (
      select u.calendar_id from public.users u
      where u.google_id::text = auth.uid()::text
         or lower(u.email::text) = lower(coalesce(auth.jwt() ->> 'email', ''))
    )
  );

-- Add category_id to events table
alter table public.events add column if not exists category_id uuid references public.event_categories(id) on delete set null;
