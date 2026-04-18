-- 000_create_users_table.sql
-- Apply BEFORE 001_create_assessments_table.sql (which FKs into users).

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- for gen_random_uuid()

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Seed the dev-mode user referenced by middleware.DevUserID. This row is
-- required so the assessments FK constraint succeeds in dev. Replace with
-- real user provisioning before production.
INSERT INTO users (id, email, password_hash)
VALUES ('00000000-0000-0000-0000-000000000001', 'dev@alif.om', 'dev_only_no_real_password')
ON CONFLICT (id) DO NOTHING;
