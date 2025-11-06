-- ============================================================================
-- Migration 001: Multi-Tenant Schema Foundation (v2 - Fixed)
-- ============================================================================
-- Description: Migrate from simple 4-table schema to comprehensive multi-tenant
--              architecture with companies, users, content library, and workflow
-- Author: Claude AI Assistant
-- Date: 2025-11-06 (Updated)
-- Estimated Duration: 2-3 minutes
-- Dependencies: PostgreSQL 14+, vector extension (already enabled)
--
-- CHANGES FROM V1:
-- - Renamed 'users' table to 'app_users' to avoid conflict with existing users table
-- - All foreign keys now reference 'app_users' instead of 'users'
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: ENUM TYPES
-- ============================================================================

-- User role enumeration
DO $$ BEGIN
    CREATE TYPE user_role_enum AS ENUM ('admin', 'user', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Project status workflow enumeration (10 states)
DO $$ BEGIN
    CREATE TYPE project_status_enum AS ENUM (
        'draft',           -- Initial state
        'rc_analyzing',    -- RC document being analyzed
        'rc_analyzed',     -- RC analysis complete
        'matching',        -- Matching requirements to content
        'matched',         -- Content matching complete
        'generating',      -- AI generating new content
        'generated',       -- Generation complete
        'reviewing',       -- Human review in progress
        'completed',       -- Memoir finalized
        'submitted'        -- Submitted to client
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Content block type enumeration (7 types)
DO $$ BEGIN
    CREATE TYPE content_block_type_enum AS ENUM (
        'company-profile',           -- Company overview and capabilities
        'person-cv',                 -- Staff CVs and qualifications
        'equipment',                 -- Equipment descriptions
        'procedure',                 -- Technical procedures
        'certification',             -- Certifications and standards
        'methodology-template',      -- Methodology templates
        'past-project-reference'     -- Reference to past projects
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Generation request status enumeration
DO $$ BEGIN
    CREATE TYPE generation_status_enum AS ENUM (
        'pending',
        'in_progress',
        'completed',
        'failed'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- File relationship type enumeration
DO $$ BEGIN
    CREATE TYPE file_relationship_enum AS ENUM (
        'main-file',
        'photo',
        'certificate',
        'datasheet'
    );
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- SECTION 2: BASE TABLES (No Dependencies)
-- ============================================================================

-- Companies table: Multi-tenancy root
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(255),
    logo_url TEXT,
    certifications TEXT[],  -- Array of certification names/numbers
    settings JSONB DEFAULT '{}',  -- Company-specific settings
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Audit log table: Security and compliance tracking
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(100) NOT NULL,  -- e.g., 'user.login', 'project.create', 'content.delete'
    user_id UUID,  -- Can be NULL for system actions
    resource_type VARCHAR(50),  -- e.g., 'project', 'content_block', 'user'
    resource_id UUID,
    details JSONB DEFAULT '{}',  -- Additional context
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SECTION 3: USER MANAGEMENT
-- ============================================================================

-- App users table: Company users with roles (renamed from 'users' to avoid conflict)
CREATE TABLE IF NOT EXISTS app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role_enum NOT NULL DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- SECTION 4: CONTENT SYSTEM
-- ============================================================================

-- Content blocks: Reusable content library
CREATE TABLE IF NOT EXISTS content_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    type content_block_type_enum NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',  -- Type-specific metadata
    tags TEXT[],  -- Search tags
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID NOT NULL REFERENCES app_users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Files: File storage metadata
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),  -- MIME type
    storage_url TEXT NOT NULL,  -- Supabase storage URL
    size_bytes BIGINT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by UUID NOT NULL REFERENCES app_users(id) ON DELETE RESTRICT,
    metadata JSONB DEFAULT '{}'  -- Additional file metadata
);

-- Block-File relationship: Many-to-many with relationship type
CREATE TABLE IF NOT EXISTS block_files (
    block_id UUID NOT NULL REFERENCES content_blocks(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    relationship file_relationship_enum NOT NULL,
    PRIMARY KEY (block_id, file_id)
);

-- Past projects: Reference projects for content reuse
CREATE TABLE IF NOT EXISTS past_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    client VARCHAR(255),
    year INTEGER,
    project_type VARCHAR(100),
    description TEXT,
    techniques_used TEXT[],
    success_factors TEXT[],
    photos TEXT[],  -- Array of storage URLs
    is_referenceable BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Section templates: Reusable section templates
CREATE TABLE IF NOT EXISTS section_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    section_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    template_content TEXT NOT NULL,
    placeholders JSONB DEFAULT '{}',  -- {placeholder_name: description}
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SECTION 5: PROJECT WORKFLOW TABLES
-- ============================================================================

-- RC analysis: Results from RC document parsing
CREATE TABLE IF NOT EXISTS rc_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID UNIQUE NOT NULL,  -- Will reference projects after ALTER
    rc_file_url TEXT NOT NULL,
    project_info JSONB DEFAULT '{}',  -- Client, location, lot, project type
    required_sections JSONB DEFAULT '[]',  -- Array of required sections
    special_requirements JSONB DEFAULT '[]',  -- Array of special requirements
    format JSONB DEFAULT '{}',  -- Format requirements (page limits, etc.)
    scoring_criteria JSONB DEFAULT '{}',  -- How memoir will be scored
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score FLOAT  -- 0.0-1.0 confidence in analysis
);

-- Content matches: Requirement to content block mappings
CREATE TABLE IF NOT EXISTS content_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,  -- Will reference projects after ALTER
    requirement_id VARCHAR(100) NOT NULL,  -- ID from rc_analysis.required_sections
    matched_blocks UUID[],  -- Array of content_block IDs
    confidence FLOAT,  -- 0.0-1.0 match confidence
    match_reason TEXT,  -- Explanation of why content was matched
    needs_generation BOOLEAN DEFAULT FALSE,  -- No suitable content found
    needs_upload BOOLEAN DEFAULT FALSE,  -- New file upload required
    approved BOOLEAN DEFAULT FALSE,  -- User approved the match
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generation requests: AI content generation tracking
CREATE TABLE IF NOT EXISTS generation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,  -- Will reference projects after ALTER
    section_type VARCHAR(100) NOT NULL,
    status generation_status_enum DEFAULT 'pending',
    request_context JSONB DEFAULT '{}',  -- Requirements, constraints
    generated_content TEXT,
    quality_score FLOAT,  -- 0.0-1.0 AI-assessed quality
    model_used VARCHAR(100),  -- e.g., 'claude-3-5-sonnet-20241022'
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_seconds FLOAT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- SECTION 6: MODIFY EXISTING TABLES
-- ============================================================================

-- Add multi-tenancy and workflow to projects table
DO $$ BEGIN
    -- Add company_id column
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'company_id'
    ) THEN
        ALTER TABLE projects ADD COLUMN company_id UUID REFERENCES companies(id) ON DELETE CASCADE;
    END IF;

    -- Add created_by column (references app_users, not users)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE projects ADD COLUMN created_by UUID REFERENCES app_users(id) ON DELETE SET NULL;
    END IF;

    -- Add client information
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'client'
    ) THEN
        ALTER TABLE projects ADD COLUMN client VARCHAR(255);
    END IF;

    -- Add location
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'location'
    ) THEN
        ALTER TABLE projects ADD COLUMN location VARCHAR(255);
    END IF;

    -- Add lot
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'lot'
    ) THEN
        ALTER TABLE projects ADD COLUMN lot VARCHAR(100);
    END IF;

    -- Add project_type
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'project_type'
    ) THEN
        ALTER TABLE projects ADD COLUMN project_type VARCHAR(100);
    END IF;

    -- Add size
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'size'
    ) THEN
        ALTER TABLE projects ADD COLUMN size VARCHAR(100);
    END IF;

    -- Add deadline
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'deadline'
    ) THEN
        ALTER TABLE projects ADD COLUMN deadline TIMESTAMP WITH TIME ZONE;
    END IF;

    -- Add final_document_url
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'final_document_url'
    ) THEN
        ALTER TABLE projects ADD COLUMN final_document_url TEXT;
    END IF;

    -- Add metadata
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE projects ADD COLUMN metadata JSONB DEFAULT '{}';
    END IF;
END $$;

-- Modify status column to use enum (requires recreation)
-- Note: This preserves existing status values if they match enum values
DO $$ BEGIN
    -- Check if status column is already the enum type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects'
        AND column_name = 'status'
        AND udt_name != 'project_status_enum'
    ) THEN
        -- Add temporary column with enum type
        ALTER TABLE projects ADD COLUMN status_new project_status_enum;

        -- Migrate existing data (map old values to new enum)
        UPDATE projects SET status_new =
            CASE
                WHEN status = 'draft' THEN 'draft'::project_status_enum
                WHEN status = 'analyzing' THEN 'rc_analyzing'::project_status_enum
                WHEN status = 'in_progress' THEN 'matching'::project_status_enum
                WHEN status = 'completed' THEN 'completed'::project_status_enum
                ELSE 'draft'::project_status_enum
            END;

        -- Drop old column and rename new one
        ALTER TABLE projects DROP COLUMN status;
        ALTER TABLE projects RENAME COLUMN status_new TO status;
    END IF;

    -- Set default if not exists
    ALTER TABLE projects ALTER COLUMN status SET DEFAULT 'draft'::project_status_enum;
END $$;

-- Add generation metadata to sections table
DO $$ BEGIN
    -- Add generated_by_ai
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sections' AND column_name = 'generated_by_ai'
    ) THEN
        ALTER TABLE sections ADD COLUMN generated_by_ai BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add source_blocks
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sections' AND column_name = 'source_blocks'
    ) THEN
        ALTER TABLE sections ADD COLUMN source_blocks UUID[];
    END IF;

    -- Add quality_score
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sections' AND column_name = 'quality_score'
    ) THEN
        ALTER TABLE sections ADD COLUMN quality_score FLOAT;
    END IF;

    -- Add reviewed
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sections' AND column_name = 'reviewed'
    ) THEN
        ALTER TABLE sections ADD COLUMN reviewed BOOLEAN DEFAULT FALSE;
    END IF;

    -- Add reviewer_id (references app_users, not users)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sections' AND column_name = 'reviewer_id'
    ) THEN
        ALTER TABLE sections ADD COLUMN reviewer_id UUID REFERENCES app_users(id) ON DELETE SET NULL;
    END IF;

    -- Add reviewed_at
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'sections' AND column_name = 'reviewed_at'
    ) THEN
        ALTER TABLE sections ADD COLUMN reviewed_at TIMESTAMP WITH TIME ZONE;
    END IF;
END $$;

-- Add multi-tenancy to memoires table
DO $$ BEGIN
    -- Add company_id
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memoires' AND column_name = 'company_id'
    ) THEN
        ALTER TABLE memoires ADD COLUMN company_id UUID REFERENCES companies(id) ON DELETE CASCADE;
    END IF;

    -- Add uploaded_by (references app_users, not users)
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memoires' AND column_name = 'uploaded_by'
    ) THEN
        ALTER TABLE memoires ADD COLUMN uploaded_by UUID REFERENCES app_users(id) ON DELETE SET NULL;
    END IF;

    -- Add project_type
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memoires' AND column_name = 'project_type'
    ) THEN
        ALTER TABLE memoires ADD COLUMN project_type VARCHAR(100);
    END IF;

    -- Add techniques_used
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memoires' AND column_name = 'techniques_used'
    ) THEN
        ALTER TABLE memoires ADD COLUMN techniques_used TEXT[];
    END IF;

    -- Add metadata
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memoires' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE memoires ADD COLUMN metadata JSONB DEFAULT '{}';
    END IF;
END $$;

-- Add foreign key constraints to rc_analysis, content_matches, generation_requests
-- (These reference projects which now has company_id)
DO $$ BEGIN
    -- Add FK for rc_analysis.project_id if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'rc_analysis_project_id_fkey'
    ) THEN
        ALTER TABLE rc_analysis
        ADD CONSTRAINT rc_analysis_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;

    -- Add FK for content_matches.project_id if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'content_matches_project_id_fkey'
    ) THEN
        ALTER TABLE content_matches
        ADD CONSTRAINT content_matches_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;

    -- Add FK for generation_requests.project_id if not exists
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'generation_requests_project_id_fkey'
    ) THEN
        ALTER TABLE generation_requests
        ADD CONSTRAINT generation_requests_project_id_fkey
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================================================
-- SECTION 7: PERFORMANCE INDEXES
-- ============================================================================

-- Companies indexes
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

-- App users indexes
CREATE INDEX IF NOT EXISTS idx_app_users_company_id ON app_users(company_id);
CREATE INDEX IF NOT EXISTS idx_app_users_email ON app_users(email);

-- Content blocks indexes
CREATE INDEX IF NOT EXISTS idx_content_blocks_company_type ON content_blocks(company_id, type);
CREATE INDEX IF NOT EXISTS idx_content_blocks_tags ON content_blocks USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_content_blocks_metadata ON content_blocks USING GIN(metadata);

-- Files indexes
CREATE INDEX IF NOT EXISTS idx_files_company_id ON files(company_id);
CREATE INDEX IF NOT EXISTS idx_files_uploaded_by ON files(uploaded_by);

-- Past projects indexes
CREATE INDEX IF NOT EXISTS idx_past_projects_company_id ON past_projects(company_id);
CREATE INDEX IF NOT EXISTS idx_past_projects_techniques ON past_projects USING GIN(techniques_used);

-- Section templates indexes
CREATE INDEX IF NOT EXISTS idx_section_templates_company_type ON section_templates(company_id, section_type);

-- RC analysis indexes
CREATE INDEX IF NOT EXISTS idx_rc_analysis_project_id ON rc_analysis(project_id);

-- Content matches indexes
CREATE INDEX IF NOT EXISTS idx_content_matches_project_id ON content_matches(project_id);
CREATE INDEX IF NOT EXISTS idx_content_matches_blocks ON content_matches USING GIN(matched_blocks);

-- Generation requests indexes
CREATE INDEX IF NOT EXISTS idx_generation_requests_project_id ON generation_requests(project_id);
CREATE INDEX IF NOT EXISTS idx_generation_requests_status ON generation_requests(status);

-- Projects indexes (multi-tenant queries)
CREATE INDEX IF NOT EXISTS idx_projects_company_id ON projects(company_id);
CREATE INDEX IF NOT EXISTS idx_projects_company_status ON projects(company_id, status);
CREATE INDEX IF NOT EXISTS idx_projects_created_by ON projects(created_by);

-- Sections indexes
CREATE INDEX IF NOT EXISTS idx_sections_project_id ON sections(project_id);
CREATE INDEX IF NOT EXISTS idx_sections_reviewer_id ON sections(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_sections_source_blocks ON sections USING GIN(source_blocks);

-- Memoires indexes (multi-tenant queries)
CREATE INDEX IF NOT EXISTS idx_memoires_company_id ON memoires(company_id);
CREATE INDEX IF NOT EXISTS idx_memoires_uploaded_by ON memoires(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_memoires_techniques ON memoires USING GIN(techniques_used);

-- Audit log indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp DESC);

-- ============================================================================
-- SECTION 8: DATA MIGRATION (For Existing Data)
-- ============================================================================

-- Create default company for existing data migration
DO $$
DECLARE
    default_company_id UUID;
    migration_user_id UUID;
BEGIN
    -- Only create if companies table is empty
    IF NOT EXISTS (SELECT 1 FROM companies LIMIT 1) THEN
        INSERT INTO companies (name, email, settings)
        VALUES ('Enpyco (Migrated Data)', 'contact@enpyco.com', '{"migrated": true}')
        RETURNING id INTO default_company_id;

        -- Create migration user for tracking historical data
        INSERT INTO app_users (company_id, email, password_hash, full_name, role, is_active)
        VALUES (
            default_company_id,
            'migration@system.local',
            'MIGRATION_USER_NO_LOGIN',  -- Invalid hash prevents login
            'System Migration User',
            'admin',
            FALSE  -- Inactive to prevent login
        )
        RETURNING id INTO migration_user_id;

        -- Migrate existing memoires to default company
        UPDATE memoires
        SET
            company_id = default_company_id,
            uploaded_by = migration_user_id
        WHERE company_id IS NULL;

        -- Migrate existing projects to default company
        UPDATE projects
        SET
            company_id = default_company_id,
            created_by = migration_user_id
        WHERE company_id IS NULL;

        RAISE NOTICE 'Migration complete: Created default company (%) and migration user (%)',
                     default_company_id, migration_user_id;
    END IF;
END $$;

-- ============================================================================
-- SECTION 9: FINALIZATION
-- ============================================================================

-- Add NOT NULL constraints after data migration
DO $$ BEGIN
    -- Projects company_id NOT NULL
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'projects'
        AND column_name = 'company_id'
        AND is_nullable = 'YES'
    ) THEN
        -- Only add constraint if all rows have company_id
        IF NOT EXISTS (SELECT 1 FROM projects WHERE company_id IS NULL) THEN
            ALTER TABLE projects ALTER COLUMN company_id SET NOT NULL;
        ELSE
            RAISE WARNING 'Cannot set projects.company_id to NOT NULL - null values exist';
        END IF;
    END IF;

    -- Memoires company_id NOT NULL
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'memoires'
        AND column_name = 'company_id'
        AND is_nullable = 'YES'
    ) THEN
        -- Only add constraint if all rows have company_id
        IF NOT EXISTS (SELECT 1 FROM memoires WHERE company_id IS NULL) THEN
            ALTER TABLE memoires ALTER COLUMN company_id SET NOT NULL;
        ELSE
            RAISE WARNING 'Cannot set memoires.company_id to NOT NULL - null values exist';
        END IF;
    END IF;
END $$;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Summary:
-- - 5 enum types created
-- - 11 new tables created (app_users instead of users to avoid conflict)
-- - 3 existing tables modified (projects, sections, memoires)
-- - 25+ indexes created for performance
-- - Existing data migrated to default company
-- - Multi-tenant architecture ready for use
-- ============================================================================
