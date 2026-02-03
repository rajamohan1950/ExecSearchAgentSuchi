-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255),
    phone           VARCHAR(50),
    location        VARCHAR(255),
    linkedin_url    VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Profile versions: append-only immutable snapshots
CREATE TABLE IF NOT EXISTS profile_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL,
    source_type     VARCHAR(50) NOT NULL DEFAULT 'linkedin_pdf',
    source_filename VARCHAR(255),

    -- Parsed LinkedIn sections
    headline        VARCHAR(500),
    summary         TEXT,
    experience      JSONB NOT NULL DEFAULT '[]',
    education       JSONB NOT NULL DEFAULT '[]',
    skills          JSONB NOT NULL DEFAULT '[]',
    certifications  JSONB NOT NULL DEFAULT '[]',
    languages       JSONB NOT NULL DEFAULT '[]',
    volunteer       JSONB NOT NULL DEFAULT '[]',
    patents         JSONB NOT NULL DEFAULT '[]',
    publications    JSONB NOT NULL DEFAULT '[]',
    awards          JSONB NOT NULL DEFAULT '[]',
    projects        JSONB NOT NULL DEFAULT '[]',
    courses         JSONB NOT NULL DEFAULT '[]',
    raw_parsed_data JSONB,

    -- PDF storage
    pdf_storage_key VARCHAR(500),

    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_user_version UNIQUE(user_id, version)
);

CREATE INDEX IF NOT EXISTS idx_profile_versions_user_id ON profile_versions(user_id);
CREATE INDEX IF NOT EXISTS idx_profile_versions_current ON profile_versions(user_id, is_current) WHERE is_current = TRUE;
