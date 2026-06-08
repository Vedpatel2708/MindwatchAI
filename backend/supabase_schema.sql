-- =============================================================================
-- MINDWATCH — Mental Health Crisis Detection Engine
-- Supabase Schema
-- Run this in Supabase SQL Editor to create all tables.
-- =============================================================================

-- assessments: each text submission analyzed by the system
CREATE TABLE IF NOT EXISTS assessments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID,                           -- links to a user session
    input_text          TEXT             NOT NULL,       -- the raw text submitted
    input_type          VARCHAR(20)      NOT NULL DEFAULT 'journal', -- journal | chat | note | speech
    -- ML scoring output
    crisis_score        NUMERIC(5, 4),                  -- 0.0-1.0 overall risk
    depression_score    NUMERIC(5, 4),                  -- depression signal
    anxiety_score       NUMERIC(5, 4),                  -- anxiety signal
    crisis_signal       NUMERIC(5, 4),                  -- acute crisis/suicidality signal
    sentiment_score     NUMERIC(5, 4),                  -- -1.0 to 1.0
    dominant_emotion    VARCHAR(30),                    -- e.g. "sadness", "fear", "hopelessness"
    detected_symptoms   JSONB,                          -- list of DSM-5 symptom strings
    risk_level          VARCHAR(20)      NOT NULL DEFAULT 'analyzing', -- safe|low|moderate|high|crisis
    -- Agent output
    agent_summary       TEXT,
    recommendations     JSONB,
    resources           JSONB,
    -- Lifecycle
    status              VARCHAR(20)      NOT NULL DEFAULT 'pending',
    submitted_at        TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    analyzed_at         TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_assessments_session    ON assessments(session_id);
CREATE INDEX IF NOT EXISTS idx_assessments_risk       ON assessments(risk_level);
CREATE INDEX IF NOT EXISTS idx_assessments_submitted  ON assessments(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_crisis     ON assessments(crisis_score DESC);

-- sessions: tracks a user's longitudinal mental health journey
CREATE TABLE IF NOT EXISTS sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_label       TEXT             DEFAULT 'Anonymous Session',
    assessment_count    INTEGER          NOT NULL DEFAULT 0,
    avg_crisis_score    NUMERIC(5, 4),
    trend               VARCHAR(20),    -- improving | stable | worsening
    last_risk_level     VARCHAR(20),
    created_at          TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);

-- risk_alerts: created when crisis_score exceeds threshold
CREATE TABLE IF NOT EXISTS risk_alerts (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID             NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    session_id          UUID,
    crisis_score        NUMERIC(5, 4)   NOT NULL,
    risk_level          VARCHAR(20)      NOT NULL,
    threshold_used      NUMERIC(5, 4)   NOT NULL,
    status              VARCHAR(20)      NOT NULL DEFAULT 'open', -- open | reviewed | resolved
    created_at          TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_alerts_assessment ON risk_alerts(assessment_id);
CREATE INDEX IF NOT EXISTS idx_alerts_status     ON risk_alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_created    ON risk_alerts(created_at DESC);

-- analysis_steps: ReAct agent reasoning trace per assessment
CREATE TABLE IF NOT EXISTS analysis_steps (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id       UUID             NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    step_number         INTEGER          NOT NULL,
    step_type           VARCHAR(20)      NOT NULL, -- thought|action|observation|final_answer
    tool_name           VARCHAR(60),
    tool_input          JSONB,
    tool_output         JSONB,
    content             TEXT,
    is_error            BOOLEAN          NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ      NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_steps_assessment ON analysis_steps(assessment_id, step_number);

-- =============================================================================
-- TABLE: rag_documents
-- Stores knowledge base documents with their embeddings for RAG retrieval.
-- The embedding column stores the 384-dim all-MiniLM-L6-v2 vector as JSONB.
-- Run POST /rag/ingest after setup to populate this table.
-- =============================================================================
CREATE TABLE IF NOT EXISTS rag_documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_id      VARCHAR(20)  NOT NULL UNIQUE,  -- e.g. "dep-001"
    title       TEXT         NOT NULL,
    category    VARCHAR(30)  NOT NULL,          -- depression | anxiety | crisis | coping | therapy | self-care
    source      TEXT,
    content     TEXT         NOT NULL,
    tags        JSONB,
    embedding   JSONB,                          -- 384-dim float array from all-MiniLM-L6-v2
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rag_doc_id   ON rag_documents(doc_id);
CREATE INDEX IF NOT EXISTS idx_rag_category ON rag_documents(category);
