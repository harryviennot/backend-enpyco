-- =====================================================
-- Enpyco Memoir Generator - Complete Database Schema
-- =====================================================
-- Multi-Tenant SaaS Architecture
-- Version: 2.0 (Post-Migration 001)
-- Last Updated: 2025-11-06
--
-- IMPORTANT: This schema is for DOCUMENTATION ONLY
-- To create or update the database, use the migration scripts:
--   - migrations/001_multi_tenant_schema.sql
--   - migrations/001_seed_data.sql (development)
--
-- Run this in Supabase SQL Editor ONLY for fresh setup
-- Dashboard → SQL Editor → New Query → Paste & Run
-- =====================================================

-- =====================================================
-- SECTION 1: EXTENSIONS
-- =====================================================

-- Enable pgvector extension for RAG embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- =====================================================
-- SECTION 2: ENUM TYPES
-- =====================================================

-- User role enumeration
CREATE TYPE user_role_enum AS ENUM ('admin', 'user', 'viewer');

-- Project status workflow (10 states)
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

-- Content block types (7 types)
CREATE TYPE content_block_type_enum AS ENUM (
    'company-profile',
    'person-cv',
    'equipment',
    'procedure',
    'certification',
    'methodology-template',
    'past-project-reference'
);

-- Generation request status
CREATE TYPE generation_status_enum AS ENUM (
    'pending',
    'in_progress',
    'completed',
    'failed'
);

-- File relationship types
CREATE TYPE file_relationship_enum AS ENUM (
    'main-file',
    'photo',
    'certificate',
    'datasheet'
);

-- =====================================================
-- SECTION 3: BASE TABLES (Multi-Tenancy Foundation)
-- =====================================================

-- Companies table: Multi-tenancy root
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    city VARCHAR(100),
    postal_code VARCHAR(20),
    phone VARCHAR(50),
    email VARCHAR(255),
    logo_url TEXT,
    certifications TEXT[],
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Users table: Company users with roles
CREATE TABLE users (
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

-- =====================================================
-- SECTION 4: CONTENT LIBRARY SYSTEM
-- =====================================================

-- Content blocks: Reusable content library
CREATE TABLE content_blocks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    type content_block_type_enum NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    tags TEXT[],
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Files: File storage metadata
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(100),
    storage_url TEXT NOT NULL,
    size_bytes BIGINT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    metadata JSONB DEFAULT '{}'
);

-- Block-File relationships: Many-to-many
CREATE TABLE block_files (
    block_id UUID NOT NULL REFERENCES content_blocks(id) ON DELETE CASCADE,
    file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    relationship file_relationship_enum NOT NULL,
    PRIMARY KEY (block_id, file_id)
);

-- Past projects: Reference projects
CREATE TABLE past_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    client VARCHAR(255),
    year INTEGER,
    project_type VARCHAR(100),
    description TEXT,
    techniques_used TEXT[],
    success_factors TEXT[],
    photos TEXT[],
    is_referenceable BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Section templates: Reusable templates
CREATE TABLE section_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    section_type VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    template_content TEXT NOT NULL,
    placeholders JSONB DEFAULT '{}',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- SECTION 5: MEMOIR PROJECTS (Core Business Logic)
-- =====================================================

-- Projects table: Memoir generation projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    client VARCHAR(255),
    location VARCHAR(255),
    lot VARCHAR(100),
    project_type VARCHAR(100),
    size VARCHAR(100),
    deadline TIMESTAMP WITH TIME ZONE,
    rc_storage_path VARCHAR(500),
    rc_context TEXT,
    status project_status_enum DEFAULT 'draft',
    final_document_url TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sections table: Generated memoir sections
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    section_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    order_num INTEGER,
    generated_by_ai BOOLEAN DEFAULT FALSE,
    source_blocks UUID[],
    quality_score FLOAT,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewer_id UUID REFERENCES users(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- RC analysis: RC document parsing results
CREATE TABLE rc_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID UNIQUE NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    rc_file_url TEXT NOT NULL,
    project_info JSONB DEFAULT '{}',
    required_sections JSONB DEFAULT '[]',
    special_requirements JSONB DEFAULT '[]',
    format JSONB DEFAULT '{}',
    scoring_criteria JSONB DEFAULT '{}',
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score FLOAT
);

-- Content matches: Requirement-to-content mappings
CREATE TABLE content_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    requirement_id VARCHAR(100) NOT NULL,
    matched_blocks UUID[],
    confidence FLOAT,
    match_reason TEXT,
    needs_generation BOOLEAN DEFAULT FALSE,
    needs_upload BOOLEAN DEFAULT FALSE,
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Generation requests: AI content generation tracking
CREATE TABLE generation_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    section_type VARCHAR(100) NOT NULL,
    status generation_status_enum DEFAULT 'pending',
    request_context JSONB DEFAULT '{}',
    generated_content TEXT,
    quality_score FLOAT,
    model_used VARCHAR(100),
    tokens_used INTEGER,
    cost_usd DECIMAL(10, 6),
    latency_seconds FLOAT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- =====================================================
-- SECTION 6: RAG SYSTEM (Reference Documents)
-- =====================================================

-- Memoires table: Reference documents
CREATE TABLE memoires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    client VARCHAR(255),
    year INTEGER,
    project_type VARCHAR(100),
    techniques_used TEXT[],
    indexed BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document chunks: RAG embeddings (unchanged from v1)
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memoire_id UUID NOT NULL REFERENCES memoires(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI text-embedding-3-small
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- SECTION 7: AUDIT & SECURITY
-- =====================================================

-- Audit log: Security and compliance tracking
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action VARCHAR(100) NOT NULL,
    user_id UUID,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- SECTION 8: PERFORMANCE INDEXES
-- =====================================================

-- Companies indexes
CREATE INDEX idx_companies_name ON companies(name);

-- Users indexes
CREATE INDEX idx_users_company_id ON users(company_id);
CREATE INDEX idx_users_email ON users(email);

-- Content blocks indexes
CREATE INDEX idx_content_blocks_company_type ON content_blocks(company_id, type);
CREATE INDEX idx_content_blocks_tags ON content_blocks USING GIN(tags);
CREATE INDEX idx_content_blocks_metadata ON content_blocks USING GIN(metadata);

-- Files indexes
CREATE INDEX idx_files_company_id ON files(company_id);
CREATE INDEX idx_files_uploaded_by ON files(uploaded_by);

-- Past projects indexes
CREATE INDEX idx_past_projects_company_id ON past_projects(company_id);
CREATE INDEX idx_past_projects_techniques ON past_projects USING GIN(techniques_used);

-- Section templates indexes
CREATE INDEX idx_section_templates_company_type ON section_templates(company_id, section_type);

-- Projects indexes (multi-tenant queries)
CREATE INDEX idx_projects_company_id ON projects(company_id);
CREATE INDEX idx_projects_company_status ON projects(company_id, status);
CREATE INDEX idx_projects_created_by ON projects(created_by);

-- Sections indexes
CREATE INDEX idx_sections_project_id ON sections(project_id, order_num);
CREATE INDEX idx_sections_reviewer_id ON sections(reviewer_id);
CREATE INDEX idx_sections_source_blocks ON sections USING GIN(source_blocks);

-- RC analysis indexes
CREATE INDEX idx_rc_analysis_project_id ON rc_analysis(project_id);

-- Content matches indexes
CREATE INDEX idx_content_matches_project_id ON content_matches(project_id);
CREATE INDEX idx_content_matches_blocks ON content_matches USING GIN(matched_blocks);

-- Generation requests indexes
CREATE INDEX idx_generation_requests_project_id ON generation_requests(project_id);
CREATE INDEX idx_generation_requests_status ON generation_requests(status);

-- Memoires indexes (multi-tenant queries)
CREATE INDEX idx_memoires_company_id ON memoires(company_id);
CREATE INDEX idx_memoires_uploaded_by ON memoires(uploaded_by);
CREATE INDEX idx_memoires_techniques ON memoires USING GIN(techniques_used);

-- Document chunks indexes
CREATE INDEX idx_chunks_memoire ON document_chunks(memoire_id);

-- Audit log indexes
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp DESC);

-- Vector similarity index (IVFFlat) for RAG
CREATE INDEX ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 10);

-- =====================================================
-- SECTION 9: FUNCTIONS
-- =====================================================

-- RAG semantic search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    memoire_ids uuid[] DEFAULT NULL,
    min_similarity float DEFAULT 0.0
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.content,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) as similarity
    FROM document_chunks
    WHERE
        CASE
            WHEN memoire_ids IS NOT NULL THEN memoire_id = ANY(memoire_ids)
            ELSE true
        END
        AND (1 - (document_chunks.embedding <=> query_embedding)) >= min_similarity
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- =====================================================
-- SCHEMA SUMMARY
-- =====================================================
-- Total Tables: 15
--
-- Multi-Tenancy:
--   ✓ companies (1)
--   ✓ users (1)
--
-- Content Library:
--   ✓ content_blocks (7 types)
--   ✓ files
--   ✓ block_files (junction)
--   ✓ past_projects
--   ✓ section_templates
--
-- Memoir Projects:
--   ✓ projects (10-state workflow)
--   ✓ sections
--   ✓ rc_analysis
--   ✓ content_matches
--   ✓ generation_requests
--
-- RAG System:
--   ✓ memoires
--   ✓ document_chunks (vector embeddings)
--
-- Security:
--   ✓ audit_log
--
-- Indexes: 25+
-- Functions: 1 (match_documents for RAG)
-- Enum Types: 5
-- =====================================================
