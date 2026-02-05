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

-- ============================================================================
-- OUTREACH AGENT TABLES
-- ============================================================================

-- Executive search firms (bulk-uploaded)
CREATE TABLE IF NOT EXISTS outreach_firms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(500) NOT NULL,
    website         VARCHAR(500),
    industry_focus  VARCHAR(255),
    location        VARCHAR(255),
    notes           TEXT,
    status          VARCHAR(50) NOT NULL DEFAULT 'new',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_firms_status ON outreach_firms(status);
CREATE INDEX IF NOT EXISTS idx_outreach_firms_name_trgm ON outreach_firms USING gin(name gin_trgm_ops);

-- Individual contacts at firms
CREATE TABLE IF NOT EXISTS outreach_contacts (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    firm_id           UUID NOT NULL REFERENCES outreach_firms(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    email             VARCHAR(255) NOT NULL,
    title             VARCHAR(255),
    phone             VARCHAR(50),
    is_primary        BOOLEAN NOT NULL DEFAULT FALSE,
    status            VARCHAR(50) NOT NULL DEFAULT 'new',
    last_contacted_at TIMESTAMPTZ,
    next_followup_at  TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outreach_contacts_firm ON outreach_contacts(firm_id);
CREATE INDEX IF NOT EXISTS idx_outreach_contacts_email ON outreach_contacts(email);
CREATE INDEX IF NOT EXISTS idx_outreach_contacts_status ON outreach_contacts(status);
CREATE INDEX IF NOT EXISTS idx_outreach_contacts_next_followup ON outreach_contacts(next_followup_at)
    WHERE next_followup_at IS NOT NULL;

-- Email conversation threads (one per contact)
CREATE TABLE IF NOT EXISTS conversation_threads (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id        UUID NOT NULL REFERENCES outreach_contacts(id) ON DELETE CASCADE,
    gmail_thread_id   VARCHAR(255),
    subject           VARCHAR(500),
    status            VARCHAR(50) NOT NULL DEFAULT 'active',
    escalation_level  INTEGER NOT NULL DEFAULT 0,
    strategy          VARCHAR(100) NOT NULL DEFAULT 'standard',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_threads_contact ON conversation_threads(contact_id);
CREATE INDEX IF NOT EXISTS idx_threads_gmail ON conversation_threads(gmail_thread_id);

-- Individual messages within threads
CREATE TABLE IF NOT EXISTS conversation_messages (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id         UUID NOT NULL REFERENCES conversation_threads(id) ON DELETE CASCADE,
    gmail_message_id  VARCHAR(255),
    direction         VARCHAR(10) NOT NULL,
    from_email        VARCHAR(255) NOT NULL,
    to_email          VARCHAR(255) NOT NULL,
    subject           VARCHAR(500),
    body_text         TEXT,
    body_html         TEXT,
    sentiment         VARCHAR(50),
    llm_analysis      JSONB,
    sent_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_thread ON conversation_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_direction ON conversation_messages(direction);

-- Agent audit log (every decision the agent makes)
CREATE TABLE IF NOT EXISTS agent_actions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id        UUID REFERENCES outreach_contacts(id) ON DELETE SET NULL,
    thread_id         UUID REFERENCES conversation_threads(id) ON DELETE SET NULL,
    action_type       VARCHAR(100) NOT NULL,
    description       TEXT,
    input_data        JSONB,
    output_data       JSONB,
    llm_model_used    VARCHAR(50),
    llm_tokens_used   INTEGER,
    status            VARCHAR(50) NOT NULL DEFAULT 'completed',
    error_message     TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_actions_contact ON agent_actions(contact_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_type ON agent_actions(action_type);
CREATE INDEX IF NOT EXISTS idx_agent_actions_created ON agent_actions(created_at);

-- Scheduled tasks (persistent task queue)
CREATE TABLE IF NOT EXISTS agent_scheduled_tasks (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id        UUID REFERENCES outreach_contacts(id) ON DELETE CASCADE,
    task_type         VARCHAR(100) NOT NULL,
    scheduled_for     TIMESTAMPTZ NOT NULL,
    executed_at       TIMESTAMPTZ,
    status            VARCHAR(50) NOT NULL DEFAULT 'pending',
    retry_count       INTEGER NOT NULL DEFAULT 0,
    max_retries       INTEGER NOT NULL DEFAULT 3,
    payload           JSONB,
    error_message     TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status ON agent_scheduled_tasks(status, scheduled_for);
CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_contact ON agent_scheduled_tasks(contact_id);

-- Daily briefing records
CREATE TABLE IF NOT EXISTS daily_briefings (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    briefing_date     DATE NOT NULL UNIQUE,
    summary_text      TEXT NOT NULL,
    stats             JSONB NOT NULL,
    email_sent        BOOLEAN NOT NULL DEFAULT FALSE,
    gmail_message_id  VARCHAR(255),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_briefings_date ON daily_briefings(briefing_date);
