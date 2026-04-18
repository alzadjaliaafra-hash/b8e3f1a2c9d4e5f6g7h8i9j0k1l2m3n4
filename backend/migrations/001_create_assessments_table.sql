-- 001_create_assessments_table.sql
-- Stores complete financial viability assessments: inputs, calculations, AI analysis.

CREATE TABLE IF NOT EXISTS assessments (
    id UUID PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('draft', 'processing', 'completed', 'failed')),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Financial input data stored as JSONB for flexibility
    inputs JSONB NOT NULL,

    -- Calculation results stored as JSONB
    results JSONB,

    -- Murshidi AI analysis stored as JSONB
    murshidi_analysis JSONB,

    -- Metadata for external integrations
    source VARCHAR(50) DEFAULT 'manual',
    external_system_id VARCHAR(100),
    external_reference_id VARCHAR(255),

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    CONSTRAINT assessments_company_name_check CHECK (char_length(company_name) >= 2)
);

CREATE INDEX IF NOT EXISTS idx_assessments_user_id       ON assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_assessments_status        ON assessments(status);
CREATE INDEX IF NOT EXISTS idx_assessments_created_at    ON assessments(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_assessments_company_name  ON assessments(company_name);
CREATE INDEX IF NOT EXISTS idx_assessments_external_ref  ON assessments(external_system_id, external_reference_id);

CREATE INDEX IF NOT EXISTS idx_assessments_inputs_gin    ON assessments USING GIN (inputs);
CREATE INDEX IF NOT EXISTS idx_assessments_results_gin   ON assessments USING GIN (results);

COMMENT ON TABLE  assessments                    IS 'Stores complete financial viability assessments including inputs, calculations, and AI analysis';
COMMENT ON COLUMN assessments.inputs             IS 'JSONB structure containing all RVSv4Input financial data';
COMMENT ON COLUMN assessments.results            IS 'JSONB structure containing all RVSv4Output calculation results';
COMMENT ON COLUMN assessments.murshidi_analysis  IS 'JSONB structure containing Murshidi AI diagnostic analysis';
