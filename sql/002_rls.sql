-- =========================================================
-- CareMinder Backend - Day 3 RLS Policies
-- File: sql/002_rls.sql
-- =========================================================

-- Helper: check if current user is admin
create or replace function public.is_admin()
returns boolean
language sql
stable
security definer
set search_path = public 
as $$
  select exists (
    select 1
    from public.profiles p
    where p.user_id = auth.uid()
      and p.role = 'admin'
  );
$$;

-- Helper: check if current user is provider
create or replace function public.is_provider()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.profiles p
    where p.user_id = auth.uid()
      and p.role = 'provider'
  );
$$;

-- Helper: can provider access a target user?
create or replace function public.provider_can_access(target_user uuid)
returns boolean
language sql
stable
security definer
set search_path = public 
as $$
  select exists (
    select 1
    from public.provider_permissions pp
    where pp.provider_id = auth.uid()
      and pp.user_id = target_user
      and pp.revoked_at is null
  );
$$;

-- =========================================================
-- Enable RLS on tables
-- =========================================================

alter table public.profiles enable row level security;
alter table public.provider_permissions enable row level security;

alter table public.devices enable row level security;
alter table public.biomarker_readings enable row level security;
alter table public.health_thresholds enable row level security;
alter table public.alerts enable row level security;
alter table public.notifications enable row level security;

alter table public.clinical_notes enable row level security;
alter table public.reports enable row level security;
alter table public.daily_summaries enable row level security;
alter table public.audit_logs enable row level security;

-- =========================================================
-- PROFILES
-- =========================================================

drop policy if exists "profiles_select_own_or_admin" on public.profiles;
create policy "profiles_select_own_or_admin"
on public.profiles
for select
using (auth.uid() = user_id or public.is_admin());

drop policy if exists "profiles_update_own_or_admin" on public.profiles;
create policy "profiles_update_own_or_admin"
on public.profiles
for update
using (auth.uid() = user_id or public.is_admin())
with check (auth.uid() = user_id or public.is_admin());

drop policy if exists "profiles_insert_own_or_admin" on public.profiles;
create policy "profiles_insert_own_or_admin"
on public.profiles
for insert
with check (auth.uid() = user_id or public.is_admin());

-- =========================================================
-- PROVIDER PERMISSIONS
-- User grants/revokes access; admin can manage too
-- =========================================================

drop policy if exists "pp_select_involved_or_admin" on public.provider_permissions;
create policy "pp_select_involved_or_admin"
on public.provider_permissions
for select
using (
  public.is_admin()
  or auth.uid() = user_id
  or auth.uid() = provider_id
);

drop policy if exists "pp_user_grant_or_admin" on public.provider_permissions;
create policy "pp_user_grant_or_admin"
on public.provider_permissions
for insert
with check (
  public.is_admin()
  or auth.uid() = user_id
);

drop policy if exists "pp_user_revoke_or_admin" on public.provider_permissions;
create policy "pp_user_revoke_or_admin"
on public.provider_permissions
for update
using (
  public.is_admin()
  or auth.uid() = user_id
)
with check (
  public.is_admin()
  or auth.uid() = user_id
);

-- =========================================================
-- DEVICES (owned by user; admin can see all)
-- =========================================================

drop policy if exists "devices_select_own_or_admin" on public.devices;
create policy "devices_select_own_or_admin"
on public.devices
for select
using (auth.uid() = user_id or public.is_admin());

drop policy if exists "devices_insert_own_or_admin" on public.devices;
create policy "devices_insert_own_or_admin"
on public.devices
for insert
with check (auth.uid() = user_id or public.is_admin());

drop policy if exists "devices_update_own_or_admin" on public.devices;
create policy "devices_update_own_or_admin"
on public.devices
for update
using (auth.uid() = user_id or public.is_admin())
with check (auth.uid() = user_id or public.is_admin());

-- =========================================================
-- BIOMARKER READINGS
-- User can access own; provider can access permitted; admin all
-- =========================================================

drop policy if exists "biomarkers_select_owner_provider_admin" on public.biomarker_readings;
create policy "biomarkers_select_owner_provider_admin"
on public.biomarker_readings
for select
using (
  public.is_admin()
  or auth.uid() = user_id
  or (public.is_provider() and public.provider_can_access(user_id))
);

drop policy if exists "biomarkers_insert_owner_or_admin" on public.biomarker_readings;
create policy "biomarkers_insert_owner_or_admin"
on public.biomarker_readings
for insert
with check (
  public.is_admin()
  or auth.uid() = user_id
);

drop policy if exists "biomarkers_update_owner_or_admin" on public.biomarker_readings;
create policy "biomarkers_update_owner_or_admin"
on public.biomarker_readings
for update
using (
  public.is_admin()
  or auth.uid() = user_id
)
with check (
  public.is_admin()
  or auth.uid() = user_id
);

-- =========================================================
-- THRESHOLDS / ALERTS / NOTIFICATIONS
-- Owned by user; provider can read alerts if permitted
-- =========================================================

drop policy if exists "thresholds_owner_or_admin" on public.health_thresholds;
create policy "thresholds_owner_or_admin"
on public.health_thresholds
for all
using (public.is_admin() or auth.uid() = user_id)
with check (public.is_admin() or auth.uid() = user_id);

drop policy if exists "alerts_select_owner_provider_admin" on public.alerts;
create policy "alerts_select_owner_provider_admin"
on public.alerts
for select
using (
  public.is_admin()
  or auth.uid() = user_id
  or (public.is_provider() and public.provider_can_access(user_id))
);

drop policy if exists "alerts_owner_or_admin_write" on public.alerts;
create policy "alerts_owner_or_admin_write"
on public.alerts
for insert
with check (public.is_admin() or auth.uid() = user_id);

drop policy if exists "notifications_owner_or_admin" on public.notifications;
create policy "notifications_owner_or_admin"
on public.notifications
for all
using (public.is_admin() or auth.uid() = user_id)
with check (public.is_admin() or auth.uid() = user_id);

-- =========================================================
-- CLINICAL NOTES
-- Provider can write notes only if permitted; user can read own; admin all
-- =========================================================

drop policy if exists "notes_select_owner_provider_admin" on public.clinical_notes;
create policy "notes_select_owner_provider_admin"
on public.clinical_notes
for select
using (
  public.is_admin()
  or auth.uid() = user_id
  or (public.is_provider() and public.provider_can_access(user_id))
);

drop policy if exists "notes_insert_provider_or_admin" on public.clinical_notes;
create policy "notes_insert_provider_or_admin"
on public.clinical_notes
for insert
with check (
  public.is_admin()
  or (public.is_provider() and provider_id = auth.uid() and public.provider_can_access(user_id))
);

-- =========================================================
-- REPORTS / SUMMARIES (owner; provider can read if permitted)
-- =========================================================

drop policy if exists "reports_select_owner_provider_admin" on public.reports;
create policy "reports_select_owner_provider_admin"
on public.reports
for select
using (
  public.is_admin()
  or auth.uid() = user_id
  or (public.is_provider() and public.provider_can_access(user_id))
);

drop policy if exists "reports_insert_owner_provider_admin" on public.reports;
create policy "reports_insert_owner_provider_admin"
on public.reports
for insert
with check (
  public.is_admin()
  or auth.uid() = user_id
  or (public.is_provider() and generated_by = auth.uid() and public.provider_can_access(user_id))
);

drop policy if exists "summaries_select_owner_provider_admin" on public.daily_summaries;
create policy "summaries_select_owner_provider_admin"
on public.daily_summaries
for select
using (
  public.is_admin()
  or auth.uid() = user_id
  or (public.is_provider() and public.provider_can_access(user_id))
);

drop policy if exists "summaries_insert_owner_or_admin" on public.daily_summaries;
create policy "summaries_insert_owner_or_admin"
on public.daily_summaries
for insert
with check (
  public.is_admin()
  or auth.uid() = user_id
);

-- =========================================================
-- AUDIT LOGS
-- Simplest: only admin can read; inserts allowed for authenticated users.
-- =========================================================

drop policy if exists "audit_insert_authenticated" on public.audit_logs;
create policy "audit_insert_authenticated"
on public.audit_logs
for insert
to authenticated
with check (true);

drop policy if exists "audit_select_admin_only" on public.audit_logs;
create policy "audit_select_admin_only"
on public.audit_logs
for select.
using (public.is_admin());