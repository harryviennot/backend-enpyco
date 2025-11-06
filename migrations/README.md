# Database Migrations

This directory contains database schema migrations for the Enpyco Memoir Generator project.

## Migration 001: Multi-Tenant Schema Foundation

**Status**: Ready for deployment
**Date**: 2025-11-06
**Duration**: ~2-3 minutes
**Dependencies**: PostgreSQL 14+, vector extension

### Overview

This migration transforms the database from a simple 4-table schema to a comprehensive multi-tenant SaaS architecture supporting:

- **Multi-tenancy**: Company isolation with `company_id` foreign keys
- **User Management**: Users with roles (admin, user, viewer)
- **Content Library**: Reusable content blocks with file attachments
- **Project Workflow**: 10-state workflow from draft to submission
- **AI Tracking**: Generation requests, quality scores, token usage
- **Audit Trail**: Security and compliance logging

### Changes Summary

#### New Tables (11)
- `companies` - Multi-tenant companies
- `users` - Company users with roles
- `content_blocks` - Reusable content library
- `files` - File metadata and storage URLs
- `block_files` - Many-to-many content-file relationships
- `past_projects` - Reference projects
- `section_templates` - Reusable section templates
- `rc_analysis` - RC document parsing results
- `content_matches` - Requirement-to-content mappings
- `generation_requests` - AI generation tracking
- `audit_log` - Security audit trail

#### Modified Tables (3)
- `projects` - Added multi-tenancy, workflow states, project details
- `sections` - Added generation metadata, review tracking
- `memoires` - Added multi-tenancy, metadata

#### Preserved Tables (1)
- `document_chunks` - RAG embeddings (unchanged)

### Files

- **001_multi_tenant_schema.sql** - Main migration script
- **001_seed_data.sql** - Development seed data (optional)
- **001_rollback.sql** - Complete rollback script
- **test_migration.py** - Validation test suite
- **README.md** - This file

## Running the Migration

### Prerequisites

1. **Backup your database** (CRITICAL!)
   ```bash
   # Using pg_dump
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

   # Or using Supabase dashboard: Settings > Database > Backup
   ```

2. **Verify PostgreSQL version** (14+ required)
   ```bash
   psql $DATABASE_URL -c "SELECT version();"
   ```

3. **Check vector extension** (should already be enabled)
   ```bash
   psql $DATABASE_URL -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
   ```

### Option 1: Using psql (Recommended)

```bash
# Navigate to backend directory
cd /Users/harry/LocalDocuments/Enpyco-memoir-generator/backend

# Run migration
psql $DATABASE_URL -f migrations/001_multi_tenant_schema.sql

# Load seed data (development only)
psql $DATABASE_URL -f migrations/001_seed_data.sql

# Validate migration
python3 migrations/test_migration.py
```

### Option 2: Using Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Create a new query
4. Copy contents of `001_multi_tenant_schema.sql`
5. Click **Run**
6. Repeat for `001_seed_data.sql` if needed

### Option 3: Using Python Script

```bash
# The test script provides instructions
python3 migrations/test_migration.py
```

## Post-Migration Validation

### 1. Run Test Suite

```bash
python3 migrations/test_migration.py
```

Expected output:
```
✅ Companies query: X rows
✅ Users query: X rows
✅ Content blocks query: X rows
✅ Projects query (with new columns): X rows
✅ Memoires query (with new columns): X rows
✅ Document chunks query (RAG): X rows

🎉 All tests passed! Migration successful!
```

### 2. Manual Validation

```sql
-- Check all new tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- Verify enum types
SELECT typname
FROM pg_type
WHERE typtype = 'e'
ORDER BY typname;

-- Check indexes
SELECT indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY indexname;

-- Verify foreign keys
SELECT conname, conrelid::regclass AS table_name, confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE contype = 'f'
ORDER BY conname;
```

### 3. Test Multi-Tenancy

```sql
-- Should see default company created
SELECT id, name, email FROM companies;

-- Should see migration user
SELECT id, email, full_name, role FROM users WHERE email = 'migration@system.local';

-- Existing memoires should have company_id
SELECT id, filename, company_id, uploaded_by FROM memoires LIMIT 5;

-- Existing projects should have company_id
SELECT id, name, company_id, created_by, status FROM projects LIMIT 5;
```

### 4. Verify RAG Functionality

```sql
-- Document chunks should be intact
SELECT COUNT(*) FROM document_chunks;

-- Vector index should exist
SELECT indexname FROM pg_indexes WHERE indexname LIKE '%embedding%';
```

## Rollback Procedure

**⚠️ WARNING: Rollback will DELETE all new tables and data!**

### Before Rollback

1. **Backup current state** if needed
2. **Understand data loss**: All companies, users, content_blocks, etc. will be deleted
3. **Communicate with team**: Ensure no one is actively using the new features

### Execute Rollback

```bash
# Using psql
psql $DATABASE_URL -f migrations/001_rollback.sql

# Verify rollback
psql $DATABASE_URL -c "\dt"  # Should show only original 4 tables
```

### After Rollback

The database will be reverted to its state before migration 001:
- ✅ Original tables intact: memoires, projects, sections, document_chunks
- ✅ All new tables removed
- ✅ All new columns removed from existing tables
- ✅ Enum types removed

## Development Seed Data

The `001_seed_data.sql` file creates:

- **1 Demo Company**: "Enpyco Demo Company"
- **3 Demo Users**:
  - `admin@enpyco.com` / `password123` (admin role)
  - `user@enpyco.com` / `password123` (user role)
  - `viewer@enpyco.com` / `password123` (viewer role)
- **7 Content Blocks**: One of each type
- **1 Past Project**: Sample reference project
- **1 Section Template**: Sample template
- **1 Sample Project**: Demo memoir project

**⚠️ Only use seed data in development environments!**

## Troubleshooting

### Migration Fails: "relation already exists"

The migration is idempotent. If it fails partway through, you can re-run it safely. It checks for existing tables/columns before creating them.

### Migration Fails: "cannot add NOT NULL constraint"

This happens if you have existing memoires/projects without company_id. The migration handles this by:
1. Creating a default company first
2. Migrating existing data
3. Adding NOT NULL constraints only after data migration

If it still fails, check:
```sql
-- Any memoires without company_id?
SELECT COUNT(*) FROM memoires WHERE company_id IS NULL;

-- Any projects without company_id?
SELECT COUNT(*) FROM projects WHERE company_id IS NULL;
```

### Enum Type Errors

If you see "type already exists" errors:
```sql
-- Check existing enums
SELECT typname FROM pg_type WHERE typtype = 'e';

-- Drop and recreate if needed (careful!)
DROP TYPE IF EXISTS user_role_enum CASCADE;
-- Then re-run migration
```

### Foreign Key Violations

If you see FK constraint errors:
```sql
-- Check orphaned data
SELECT * FROM projects WHERE company_id NOT IN (SELECT id FROM companies);
SELECT * FROM memoires WHERE company_id NOT IN (SELECT id FROM companies);
```

### Performance Issues After Migration

If queries are slow:
```sql
-- Analyze tables to update statistics
ANALYZE companies;
ANALYZE users;
ANALYZE content_blocks;
ANALYZE projects;
ANALYZE memoires;
ANALYZE sections;

-- Verify indexes were created
SELECT schemaname, tablename, indexname FROM pg_indexes WHERE schemaname = 'public';
```

## Migration Checklist

Use this checklist when running the migration:

- [ ] Database backup created and verified
- [ ] PostgreSQL version 14+ confirmed
- [ ] Vector extension enabled confirmed
- [ ] Team notified of maintenance window
- [ ] Migration executed successfully
- [ ] Test suite passed (test_migration.py)
- [ ] Manual validation queries executed
- [ ] Multi-tenancy isolation verified
- [ ] RAG functionality verified (document_chunks intact)
- [ ] Existing API endpoints tested
- [ ] Seed data loaded (development only)
- [ ] Documentation updated
- [ ] Rollback script tested (optional, on test DB)

## Next Steps After Migration

Once migration 001 is complete, you can proceed with:

1. **Task 02**: Authentication & Authorization
   - Implement JWT token authentication
   - Add login/register endpoints
   - Implement role-based permissions
   - Uses `users` and `companies` tables

2. **Task 03**: Content Library API
   - CRUD endpoints for content blocks
   - File upload/management
   - Content search and filtering
   - Uses `content_blocks`, `files`, `block_files` tables

3. **Task 04**: RC Analyzer Service
   - Parse RC documents
   - Extract requirements
   - Store in `rc_analysis` table

## Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Review migration logs for error messages
3. Verify prerequisites are met
4. Check Supabase dashboard for error details
5. Consult the main project documentation in `UPDATE.md`

## Schema Diagram

```
companies (multi-tenancy root)
    ├── users (company users with roles)
    ├── content_blocks (reusable content)
    │   ├── files (file metadata)
    │   └── block_files (junction table)
    ├── past_projects (reference projects)
    ├── section_templates (templates)
    ├── projects (memoir projects) ← modified
    │   ├── rc_analysis (RC parsing results)
    │   ├── content_matches (requirement mappings)
    │   ├── generation_requests (AI tracking)
    │   └── sections (generated content) ← modified
    └── memoires (reference documents) ← modified
        └── document_chunks (RAG embeddings) ← unchanged

audit_log (security tracking, independent)
```

## Technical Details

### Enum Types Created
- `user_role_enum`: admin, user, viewer
- `project_status_enum`: draft, rc_analyzing, rc_analyzed, matching, matched, generating, generated, reviewing, completed, submitted
- `content_block_type_enum`: company-profile, person-cv, equipment, procedure, certification, methodology-template, past-project-reference
- `generation_status_enum`: pending, in_progress, completed, failed
- `file_relationship_enum`: main-file, photo, certificate, datasheet

### Indexes Created (25+)
- GIN indexes for JSONB fields (metadata, settings, placeholders)
- GIN indexes for array fields (tags, techniques_used, matched_blocks)
- B-tree indexes for foreign keys and lookup fields
- Composite indexes for multi-tenant queries (company_id + status)

### Cascade Behavior
- `ON DELETE CASCADE`: Deleting a company deletes all related data
- `ON DELETE SET NULL`: Deleting a user sets created_by/uploaded_by to NULL
- `ON DELETE RESTRICT`: Prevents deletion if referenced (content_blocks.created_by)

---

**Migration prepared by**: Claude AI Assistant
**Last updated**: 2025-11-06
**Version**: 1.0
