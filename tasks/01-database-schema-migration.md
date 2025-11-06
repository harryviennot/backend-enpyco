# Task 01: Database Schema Migration & Multi-Tenancy Foundation

## Overview
Migrate from the current simple schema to a comprehensive multi-tenant architecture supporting the full content library, user management, and project workflow.

## Current State
- Simple schema with: `memoires`, `projects`, `sections`, `document_chunks`
- No user authentication
- No multi-tenancy
- Basic RAG functionality exists

## Goal
Complete database schema supporting:
- Multi-tenant companies and users
- Content library system
- Project workflow management
- RC analysis results storage
- Audit logging

## Database Changes Required

### New Tables to Create

1. **companies** - Tenant companies
   - id (UUID, PK)
   - name, address, city, postal_code, phone, email
   - logo_url (nullable)
   - certifications (text array)
   - settings (JSONB)
   - created_at

2. **users** - Company users
   - id (UUID, PK)
   - company_id (FK to companies)
   - email (unique)
   - password_hash
   - full_name
   - role (enum: 'admin', 'user', 'viewer')
   - is_active (boolean)
   - created_at
   - last_login (nullable)

3. **content_blocks** - Reusable content library
   - id (UUID, PK)
   - company_id (FK to companies)
   - type (enum: 'company-profile', 'person-cv', 'equipment', 'procedure', 'certification', 'methodology-template', 'past-project-reference')
   - title
   - content (text)
   - metadata (JSONB) - flexible structure per type
   - tags (text array)
   - version (integer)
   - is_active (boolean)
   - created_at, updated_at
   - created_by (FK to users)

4. **files** - File storage metadata
   - id (UUID, PK)
   - company_id (FK to companies)
   - filename
   - file_type
   - storage_url (S3 path)
   - size_bytes
   - uploaded_at
   - uploaded_by (FK to users)
   - metadata (JSONB)

5. **block_files** - Many-to-many relationship
   - block_id (FK to content_blocks)
   - file_id (FK to files)
   - relationship (enum: 'main-file', 'photo', 'certificate', 'datasheet')
   - PRIMARY KEY (block_id, file_id)

6. **past_projects** - Reference projects
   - id (UUID, PK)
   - company_id (FK to companies)
   - name, client, year
   - project_type
   - description (text)
   - techniques_used (text array)
   - success_factors (text array)
   - photos (text array - S3 URLs)
   - is_referenceable (boolean)
   - metadata (JSONB)
   - created_at

7. **section_templates** - Template sections
   - id (UUID, PK)
   - company_id (FK to companies)
   - section_type
   - title
   - template_content (text with placeholders)
   - placeholders (JSONB)
   - usage_count (integer)
   - created_at

8. **rc_analysis** - RC parsing results
   - id (UUID, PK)
   - project_id (FK to projects, unique)
   - rc_file_url (S3 path)
   - project_info (JSONB)
   - required_sections (JSONB array)
   - special_requirements (JSONB array)
   - format (JSONB)
   - scoring_criteria (JSONB)
   - analyzed_at
   - confidence_score (float)

9. **content_matches** - Requirement-to-content mappings
   - id (UUID, PK)
   - project_id (FK to projects)
   - requirement_id (text)
   - matched_blocks (UUID array)
   - confidence (float)
   - match_reason (text)
   - needs_generation (boolean)
   - needs_upload (boolean)
   - approved (boolean)
   - created_at

10. **generation_requests** - AI generation tracking
    - id (UUID, PK)
    - project_id (FK to projects)
    - section_type (enum)
    - status (enum: 'pending', 'in_progress', 'completed', 'failed')
    - request_context (JSONB)
    - generated_content (text, nullable)
    - quality_score (float, nullable)
    - model_used (text)
    - tokens_used (integer)
    - cost_usd (decimal)
    - latency_seconds (float)
    - error_message (text, nullable)
    - created_at, completed_at

11. **audit_log** - Security audit trail
    - id (UUID, PK)
    - action (text)
    - user_id (FK to users, nullable)
    - resource_type (text)
    - resource_id (UUID, nullable)
    - details (JSONB)
    - ip_address (inet)
    - user_agent (text)
    - timestamp (default NOW())

### Tables to Modify

1. **projects** - Add multi-tenancy and workflow fields
   - ADD company_id (FK to companies)
   - ADD created_by (FK to users)
   - ADD client, location, lot, project_type, size
   - ADD deadline (timestamp)
   - ADD status (enum: 'draft', 'rc_analyzing', 'rc_analyzed', 'matching', 'matched', 'generating', 'generated', 'reviewing', 'completed', 'submitted')
   - ADD final_document_url (S3 path, nullable)
   - ADD metadata (JSONB)

2. **sections** - Add generation metadata
   - ADD generated_by_ai (boolean)
   - ADD source_blocks (UUID array)
   - ADD quality_score (float, nullable)
   - ADD reviewed (boolean)
   - ADD reviewer_id (FK to users, nullable)
   - ADD reviewed_at (timestamp, nullable)

3. **memoires** - Add multi-tenancy
   - ADD company_id (FK to companies)
   - ADD uploaded_by (FK to users)
   - ADD project_type, techniques_used (text array)
   - ADD metadata (JSONB)

4. **document_chunks** - Keep as is (already working for RAG)

### Indexes to Create

```sql
-- Performance indexes
CREATE INDEX idx_content_blocks_company ON content_blocks(company_id);
CREATE INDEX idx_content_blocks_type ON content_blocks(type);
CREATE INDEX idx_content_blocks_tags ON content_blocks USING GIN(tags);
CREATE INDEX idx_content_blocks_active ON content_blocks(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_past_projects_company ON past_projects(company_id);
CREATE INDEX idx_past_projects_type ON past_projects(project_type);
CREATE INDEX idx_projects_company_status ON projects(company_id, status);
CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_audit_log_user ON audit_log(user_id, timestamp);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
```

## Implementation Steps

1. **Create migration file**: `migrations/001_multi_tenant_schema.sql`
2. **Create enum types** for status fields, roles, content types
3. **Create new tables** in dependency order
4. **Modify existing tables** with ALTER statements
5. **Create indexes** for performance
6. **Seed development data** (optional seed script)
7. **Test migration** on local database
8. **Create rollback script**: `migrations/001_rollback.sql`

## Testing Checklist

- [ ] Migration runs successfully on empty database
- [ ] Migration runs successfully on existing database with sample data
- [ ] All foreign key constraints work correctly
- [ ] Indexes are created and improve query performance
- [ ] Rollback script successfully reverts all changes
- [ ] Multi-tenancy isolation works (queries filter by company_id)

## Dependencies
- PostgreSQL 14+ (for JSONB and better GIN indexes)
- Existing Supabase connection from `services/supabase.py`

## Estimated Effort
**2-3 days**

## Success Criteria
- All tables created with proper constraints
- Multi-tenant data isolation enforced at database level
- Migration is idempotent (can run multiple times safely)
- Comprehensive indexes for all query patterns
- Clear rollback path

## Notes
- Keep existing `document_chunks` table and RAG functionality unchanged
- Ensure all UUIDs use `gen_random_uuid()` for PostgreSQL compatibility
- Use JSONB for flexible metadata (not JSON) for better performance
- Consider row-level security (RLS) policies for multi-tenancy in Supabase
