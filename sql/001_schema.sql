-- =========================================================
-- CareMinder Backend - Schema v1
-- =========================================================

create extension if not exists "uuid-ossp";
create extension if not exists pgcrypto;

do $$ begin
  create type user_role as enum ('user', 'provider', 'admin');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type device_status as enum ('active', 'inactive', 'disconnected');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type biomarker_type as enum (
    'heart_rate',
    'blood_pressure_systolic',
    'blood_pressure_diastolic',
    'blood_glucose',
    'spo2',
    'steps',
    'sleep_minutes'
  );
exception when duplicate_object then null;
end $$;

do $$ begin
  create type alert_severity as enum ('low', 'medium', 'high', 'critical');
exception when duplicate_object then null;
end $$;

-- -------------------------
-- Identity / Roles
-- -------------------------

create table if not exists profiles (
  user_id uuid primary key,
  full_name text,
  role user_role not null default 'user',
  date_of_birth date,
  gender text,
  height_cm numeric(5,2),
  weight_kg numeric(5,2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists provider_permissions (
  id uuid primary key default gen_random_uuid(),
  provider_id uuid not null,
  user_id uuid not null,
  granted_by uuid,
  granted_at timestamptz not null default now(),
  revoked_at timestamptz,
  unique (provider_id, user_id)
);

-- -------------------------
-- Devices + Biomarkers
-- -------------------------

create table if not exists devices (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  device_name text not null,
  vendor text,
  model text,
  status device_status not null default 'active',
  battery_percent int,
  last_sync_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists biomarker_readings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  device_id uuid,
  type biomarker_type not null,
  value numeric(12,4) not null,
  unit text,
  recorded_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists health_thresholds (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  type biomarker_type not null,
  min_value numeric(12,4),
  max_value numeric(12,4),
  severity alert_severity not null default 'medium',
  created_at timestamptz not null default now(),
  unique (user_id, type)
);

create table if not exists alerts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  type biomarker_type not null,
  reading_id uuid,
  severity alert_severity not null,
  message text not null,
  is_acknowledged boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists notifications (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  title text not null,
  body text not null,
  is_read boolean not null default false,
  created_at timestamptz not null default now()
);

-- -------------------------
-- Provider notes + Reports
-- -------------------------

create table if not exists clinical_notes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  provider_id uuid not null,
  note text not null,
  created_at timestamptz not null default now()
);

create table if not exists reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  generated_by uuid,
  title text not null,
  storage_path text,
  created_at timestamptz not null default now()
);

create table if not exists daily_summaries (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  summary_date date not null,
  content jsonb not null,
  created_at timestamptz not null default now(),
  unique (user_id, summary_date)
);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_id uuid,
  action text not null,
  target_user_id uuid,
  resource text,
  metadata jsonb,
  created_at timestamptz not null default now()
);

-- -------------------------
-- Indexes
-- -------------------------

create index if not exists idx_devices_user_id on devices(user_id);
create index if not exists idx_biomarkers_user_time on biomarker_readings(user_id, recorded_at desc);
create index if not exists idx_biomarkers_type_time on biomarker_readings(type, recorded_at desc);
create index if not exists idx_alerts_user_time on alerts(user_id, created_at desc);
create index if not exists idx_notes_user_time on clinical_notes(user_id, created_at desc);
create index if not exists idx_permissions_provider on provider_permissions(provider_id);
create index if not exists idx_permissions_user on provider_permissions(user_id);