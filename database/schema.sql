create table users (
    id uuid primary key,
    name text not null,
    created_at timestamptz default now()
);

create table nights (
    id uuid primary key,
    title text not null,
    started_at timestamptz not null,
    ended_at timestamptz,
    status text not null,
    created_at timestamptz default now()
);

create table night_participants (
    night_id uuid references nights(id) on delete cascade,
    user_id uuid references users(id) on delete cascade,
    joined_at timestamptz,
    left_at timestamptz,
    primary key (night_id, user_id)
);

create table location_points (
    id bigint generated always as identity primary key,
    night_id uuid references nights(id) on delete cascade,
    user_id uuid references users(id) on delete cascade,
    recorded_at timestamptz not null,
    latitude double precision not null,
    longitude double precision not null
);

create table personal_locations (
    id uuid primary key,
    user_id uuid references users(id) on delete cascade,
    name text not null,
    latitude double precision not null,
    longitude double precision not null,
    radius_meters double precision default 50,
    created_at timestamptz default now()
);

create table resolved_venues (
    id bigint generated always as identity primary key,
    night_id uuid references nights(id) on delete cascade,
    external_venue_id text,
    venue_name text not null,
    category text,
    source text not null,
    latitude double precision,
    longitude double precision,
    arrived_at timestamptz not null,
    left_at timestamptz not null,
    confidence text,
    score double precision
);

create table recaps (
    id bigint generated always as identity primary key,
    night_id uuid unique references nights(id) on delete cascade,
    recap_data jsonb not null,
    generated_at timestamptz default now()
);