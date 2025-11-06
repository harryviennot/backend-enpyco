-- ============================================================================
-- Rollback Script for Migration 001: Multi-Tenant Schema
-- ============================================================================
-- Description: Completely reverts all changes from 001_multi_tenant_schema.sql
-- Author: Claude AI Assistant
-- Date: 2025-11-06
-- WARNING: This will DROP tables and data! Use with extreme caution!
-- ============================================================================
-- Usage:
--   psql -h <host> -U <user> -d <database> -f 001_rollback.sql
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: DROP FOREIGN KEY CONSTRAINTS FROM MODIFIED TABLES
-- ============================================================================

-- Drop FK constraints added to rc_analysis, content_matches, generation_requests
ALTER TABLE IF EXISTS rc_analysis DROP CONSTRAINT IF EXISTS rc_analysis_project_id_fkey;
ALTER TABLE IF EXISTS content_matches DROP CONSTRAINT IF EXISTS content_matches_project_id_fkey;
ALTER TABLE IF EXISTS generation_requests DROP CONSTRAINT IF EXISTS generation_requests_project_id_fkey;

-- ============================================================================
-- SECTION 2: REVERT EXISTING TABLES TO ORIGINAL STATE
-- ============================================================================

-- Revert projects table
DO $$ BEGIN
    -- Drop added columns
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS company_id;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS created_by;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS client;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS location;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS lot;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS project_type;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS size;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS deadline;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS final_document_url;
    ALTER TABLE IF EXISTS projects DROP COLUMN IF EXISTS metadata;

    -- Revert status column to VARCHAR if it was changed to enum
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects'
        AND column_name = 'status'
        AND udt_name = 'project_status_enum'
    ) THEN
        ALTER TABLE projects ADD COLUMN status_old VARCHAR(50);
        UPDATE projects SET status_old = status::TEXT;
        ALTER TABLE projects DROP COLUMN status;
        ALTER TABLE projects RENAME COLUMN status_old TO status;
        ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'draft';
    END IF;
END $$;

-- Revert sections table
DO $$ BEGIN
    ALTER TABLE IF EXISTS sections DROP COLUMN IF EXISTS generated_by_ai;
    ALTER TABLE IF EXISTS sections DROP COLUMN IF EXISTS source_blocks;
    ALTER TABLE IF EXISTS sections DROP COLUMN IF EXISTS quality_score;
    ALTER TABLE IF EXISTS sections DROP COLUMN IF EXISTS reviewed;
    ALTER TABLE IF EXISTS sections DROP COLUMN IF EXISTS reviewer_id;
    ALTER TABLE IF EXISTS sections DROP COLUMN IF EXISTS reviewed_at;
END $$;

-- Revert memoires table
DO $$ BEGIN
    ALTER TABLE IF EXISTS memoires DROP COLUMN IF EXISTS company_id;
    ALTER TABLE IF EXISTS memoires DROP COLUMN IF EXISTS uploaded_by;
    ALTER TABLE IF EXISTS memoires DROP COLUMN IF EXISTS project_type;
    ALTER TABLE IF EXISTS memoires DROP COLUMN IF EXISTS techniques_used;
    ALTER TABLE IF EXISTS memoires DROP COLUMN IF EXISTS metadata;
END $$;

-- ============================================================================
-- SECTION 3: DROP NEW TABLES (In Reverse Dependency Order)
-- ============================================================================

-- Drop project workflow tables
DROP TABLE IF EXISTS generation_requests CASCADE;
DROP TABLE IF EXISTS content_matches CASCADE;
DROP TABLE IF EXISTS rc_analysis CASCADE;

-- Drop content system tables
DROP TABLE IF EXISTS section_templates CASCADE;
DROP TABLE IF EXISTS past_projects CASCADE;
DROP TABLE IF EXISTS block_files CASCADE;
DROP TABLE IF EXISTS files CASCADE;
DROP TABLE IF EXISTS content_blocks CASCADE;

-- Drop user management
DROP TABLE IF EXISTS users CASCADE;

-- Drop base tables
DROP TABLE IF EXISTS audit_log CASCADE;
DROP TABLE IF EXISTS companies CASCADE;

-- ============================================================================
-- SECTION 4: DROP ENUM TYPES
-- ============================================================================

DROP TYPE IF EXISTS file_relationship_enum CASCADE;
DROP TYPE IF EXISTS generation_status_enum CASCADE;
DROP TYPE IF EXISTS content_block_type_enum CASCADE;
DROP TYPE IF EXISTS project_status_enum CASCADE;
DROP TYPE IF EXISTS user_role_enum CASCADE;

-- ============================================================================
-- SECTION 5: DROP INDEXES (Cleanup)
-- ============================================================================

-- Note: Most indexes are dropped automatically with CASCADE above
-- But explicitly drop any that might remain

-- Companies indexes
DROP INDEX IF EXISTS idx_companies_name;

-- Users indexes
DROP INDEX IF EXISTS idx_users_company_id;
DROP INDEX IF EXISTS idx_users_email;

-- Content blocks indexes
DROP INDEX IF EXISTS idx_content_blocks_company_type;
DROP INDEX IF EXISTS idx_content_blocks_tags;
DROP INDEX IF EXISTS idx_content_blocks_metadata;

-- Files indexes
DROP INDEX IF EXISTS idx_files_company_id;
DROP INDEX IF EXISTS idx_files_uploaded_by;

-- Past projects indexes
DROP INDEX IF EXISTS idx_past_projects_company_id;
DROP INDEX IF EXISTS idx_past_projects_techniques;

-- Section templates indexes
DROP INDEX IF EXISTS idx_section_templates_company_type;

-- RC analysis indexes
DROP INDEX IF EXISTS idx_rc_analysis_project_id;

-- Content matches indexes
DROP INDEX IF EXISTS idx_content_matches_project_id;
DROP INDEX IF EXISTS idx_content_matches_blocks;

-- Generation requests indexes
DROP INDEX IF EXISTS idx_generation_requests_project_id;
DROP INDEX IF EXISTS idx_generation_requests_status;

-- Projects indexes
DROP INDEX IF EXISTS idx_projects_company_id;
DROP INDEX IF EXISTS idx_projects_company_status;
DROP INDEX IF EXISTS idx_projects_created_by;

-- Sections indexes
DROP INDEX IF EXISTS idx_sections_project_id;
DROP INDEX IF EXISTS idx_sections_reviewer_id;
DROP INDEX IF EXISTS idx_sections_source_blocks;

-- Memoires indexes
DROP INDEX IF EXISTS idx_memoires_company_id;
DROP INDEX IF EXISTS idx_memoires_uploaded_by;
DROP INDEX IF EXISTS idx_memoires_techniques;

-- Audit log indexes
DROP INDEX IF EXISTS idx_audit_log_user_id;
DROP INDEX IF EXISTS idx_audit_log_resource;
DROP INDEX IF EXISTS idx_audit_log_timestamp;

COMMIT;

-- ============================================================================
-- ROLLBACK COMPLETE
-- ============================================================================
-- The database schema has been reverted to its state before migration 001.
-- Original tables (memoires, projects, sections, document_chunks) restored.
-- All new tables, enums, and indexes removed.
-- ============================================================================
-- IMPORTANT: Verify the following after rollback:
-- 1. Check that memoires, projects, sections tables exist and have original columns
-- 2. Verify document_chunks table is intact (RAG functionality)
-- 3. Test existing API endpoints
-- 4. Check that no orphaned data remains
-- ============================================================================
