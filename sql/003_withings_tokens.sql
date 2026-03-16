create table if not exists withings_tokens (
  user_id uuid primary key,
  withings_user_id text,
  access_token text not null,
  refresh_token text not null,
  expires_in int,
  scope text,
  token_type text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);