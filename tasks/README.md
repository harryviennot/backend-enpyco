# Technical Memoir Generator - Development Tasks

This directory contains detailed task specifications for building the AI-powered construction technical memoir generator. Each task is designed to be worked on independently by Claude Code agents or development teams.

## Project Overview

An intelligent document assembly system that reduces technical memoir creation time from **4-5 days to 1-2 hours** by:

1. Analyzing construction consultation requirements (RC) with AI
2. Matching requirements to reusable company content
3. Generating project-specific sections with Claude AI
4. Assembling professional Word documents with proper formatting

**Target Users:** Construction companies (Gros Œuvre contractors)
**Primary Client:** ENPYCO / Groupe BERNADET

## Technology Stack

- **Backend:** FastAPI (Python), Supabase, Redis, Supabase Storage
- **AI:** Claude 3.5 Sonnet (Anthropic), RAG with pgvector
- **Document:** python-docx, PyPDF2, pdfplumber, Pillow
- **Real-time:** WebSockets
- **Deployment:** Docker, Kubernetes (optional), GitHub Actions

## Task Breakdown

### Phase 1: Foundation (Weeks 1-4)

#### [Task 01: Database Schema Migration](./01-database-schema-migration.md)

**Effort:** 2-3 days
**Dependencies:** None

Migrate from simple schema to comprehensive multi-tenant architecture.

**Key Deliverables:**

- Multi-tenant tables (companies, users)
- Content library system (content_blocks, files, past_projects)
- Project workflow tables (rc_analysis, content_matches, generation_requests)
- Audit logging
- Performance indexes

**Database Tables:**

- `companies`, `users` (multi-tenancy)
- `content_blocks`, `files`, `block_files` (content library)
- `past_projects`, `section_templates`
- `rc_analysis`, `content_matches`, `generation_requests`
- `audit_log`

---

#### [Task 02: Authentication & Authorization](./02-authentication-authorization.md)

**Effort:** 3-4 days
**Dependencies:** Task 01

Implement JWT-based auth with role-based access control.

**Key Deliverables:**

- User registration and login
- JWT token generation/validation
- Role-based permissions (admin, user, viewer)
- Multi-tenant data isolation
- Audit logging for security events

**API Endpoints:**

- `POST /auth/register`, `/auth/login`, `/auth/refresh`
- `GET /auth/me`
- `GET/POST/PATCH/DELETE /api/users` (admin only)

---

#### [Task 03: Content Library API & File Management](./03-content-library-api.md)

**Effort:** 4-5 days
**Dependencies:** Task 01, 02

Build content library for reusable blocks (CVs, equipment, procedures).

**Key Deliverables:**

- CRUD for content blocks (7 types)
- File upload to Supabase Storage
- Full-text search and tagging
- Past projects management
- Version control

**Content Block Types:**

- company-profile, person-cv, equipment
- procedure, certification
- methodology-template, past-project-reference

**API Endpoints:**

- `GET/POST/PATCH/DELETE /api/content-blocks`
- `POST /api/files/upload`
- `GET /api/past-projects/similar`

---

### Phase 2: RC Analysis (Weeks 5-6)

#### [Task 04: RC Analyzer Service](./04-rc-analyzer-service.md)

**Effort:** 5-6 days
**Dependencies:** Task 01, 02

Extract structured requirements from French PDF documents using Claude.

**Key Deliverables:**

- PDF text extraction (PyPDF2, pdfplumber)
- Claude API integration for analysis
- Requirement extraction (sections, scoring, special requirements)
- WebSocket progress updates
- Error handling and retry logic

**Extracted Data:**

- Project info (name, client, location, deadline)
- Required sections with point values
- Special technical requirements
- Scoring criteria breakdown
- Format constraints

**API Endpoints:**

- `POST /api/projects/{id}/analyze-rc`
- `GET /api/projects/{id}/analysis`
- `GET /api/projects/{id}/analysis/status`

**Cost:** ~$0.10 per RC analysis

---

### Phase 3: Content Matching (Weeks 7-8)

#### [Task 05: Content Matcher Service](./05-content-matcher-service.md)

**Effort:** 5-6 days
**Dependencies:** Task 01-04

Intelligently match RC requirements to company content blocks.

**Key Deliverables:**

- Rule-based matching for standard sections
- AI semantic matching for complex requirements
- Confidence scoring
- Gap identification (needs generation/upload)
- Chat customization interface

**Matching Strategies:**

- Rule-based: Fast, deterministic (70% of cases)
- AI semantic: Claude analyzes requirement intent (30% of cases)

**API Endpoints:**

- `POST /api/projects/{id}/match`
- `GET /api/projects/{id}/matches`
- `POST /api/projects/{id}/matches/customize` (chat)
- `POST /api/projects/{id}/matches/approve`

**Cost:** ~$0.20-$0.30 per project

---

### Phase 4: AI Content Generation (Weeks 9-10)

#### [Task 06: AI Content Generation](./06-ai-content-generation.md)

**Effort:** 6-7 days
**Dependencies:** Task 01-05, existing RAG service

Generate project-specific memoir sections using Claude.

**Key Deliverables:**

- Section generation (8 types)
- RAG integration for context
- Quality assessment
- Retry logic for low-quality output
- Cost tracking

**Section Types:**

- Methodology (3000-4000 words) - Main section
- Hypotheses (50-70 bullet points)
- Site organization (1000-2000 words)
- Planning narrative, safety, quality, etc.

**API Endpoints:**

- `POST /api/projects/{id}/generate`
- `GET /api/projects/{id}/generation/status`
- `POST /api/projects/{id}/sections/{sid}/regenerate`
- `PATCH /api/projects/{id}/sections/{sid}` (manual edit)

**Cost:** ~$1.00-$2.00 per memoir

---

### Phase 5: Document Generation (Weeks 11-12)

#### [Task 07: Word Document Generator](./07-document-generator-service.md)

**Effort:** 5-6 days
**Dependencies:** Task 01-06

Assemble professional Word documents with python-docx.

**Key Deliverables:**

- Document assembly from sections
- Company branding and styling
- Cover page, table of contents
- Image embedding and optimization
- Headers, footers, page numbers
- Quality assurance checks

**Document Structure:**

1. Cover page (logo, project info)
2. Table of contents
3. Numbered sections (1-8)
4. Annexes (CVs, certifications)

**API Endpoints:**

- `POST /api/projects/{id}/document/generate`
- `GET /api/projects/{id}/document/download`
- `POST /api/templates/upload` (custom templates)

**Performance:** <1 minute for 40-page memoir

---

### Phase 6: Real-Time & Workflow (Weeks 13-14)

#### [Task 08: WebSocket Real-Time Updates](./08-websocket-real-time-updates.md)

**Effort:** 2-3 days
**Dependencies:** Task 01-07

Implement WebSocket for progress updates during long operations.

**Key Deliverables:**

- WebSocket connection management
- Authentication via JWT query params
- Progress updates for RC analysis, matching, generation, document build
- Error and completion notifications

**WebSocket Endpoints:**

- `ws://api/ws/projects/{id}?token={jwt}`

**Message Types:**

- `rc_analysis_progress`
- `matching_progress`
- `generation_progress`
- `document_generation_progress`
- `error`, `completion`

---

#### [Task 09: Project Workflow Orchestration](./09-project-workflow-orchestration.md)

**Effort:** 3-4 days
**Dependencies:** Task 01-08

Manage complete workflow from draft to submitted.

**Key Deliverables:**

- State machine (draft → submitted)
- Automatic workflow progression
- Manual intervention points
- Error recovery and retry
- Background job management

**Project States:**

1. draft → rc_uploaded → rc_analyzing → rc_analyzed
2. → matching → matched → match_approved
3. → generating → generated → reviewing
4. → building_document → document_ready
5. → completed → submitted

**API Endpoints:**

- `POST /api/projects/{id}/workflow/analyze-rc`
- `POST /api/projects/{id}/workflow/match-content`
- `POST /api/projects/{id}/workflow/approve-matches`
- `POST /api/projects/{id}/workflow/generate`
- `POST /api/projects/{id}/workflow/build-document`
- `POST /api/projects/{id}/workflow/retry`

---

### Phase 7: Testing & Quality (Weeks 15-16)

#### [Task 10: Comprehensive Testing & QA](./10-testing-quality-assurance.md)

**Effort:** 4-5 days
**Dependencies:** All previous tasks

Production-ready test suite and CI/CD pipeline.

**Key Deliverables:**

- Unit tests (>80% coverage)
- Integration tests (API endpoints)
- End-to-end workflow tests
- Load testing (100 concurrent users)
- Security testing
- GitHub Actions CI/CD pipeline

**Test Coverage:**

- Services: >85%
- API routers: >80%
- Critical paths: >95%

---

## Task Dependencies Graph

```
01 Database Schema
  ├─> 02 Authentication
  │     ├─> 03 Content Library
  │     │     └─> 05 Content Matcher
  │     └─> 04 RC Analyzer
  │           └─> 05 Content Matcher
  │                 └─> 06 AI Generation
  │                       └─> 07 Document Generator
  │                             └─> 08 WebSocket
  │                                   └─> 09 Workflow Orchestration
  │                                         └─> 10 Testing & QA
```

## Development Approach

### Option 1: Sequential Development

Work through tasks 01-10 in order. Best for solo developer or small team.

**Timeline:** 16 weeks

### Option 2: Parallel Development

Multiple agents/developers work on independent tasks simultaneously:

**Week 1-2:**

- Task 01 (Database) - Developer A
- Plan remaining tasks - Team

**Week 3-4:**

- Task 02 (Auth) - Developer A
- Task 03 (Content Library) - Developer B (starts after Task 01)

**Week 5-6:**

- Task 04 (RC Analyzer) - Developer A
- Continue Task 03 - Developer B

**Week 7-10:**

- Task 05 (Matcher) - Developer A
- Task 06 (AI Gen) - Developer B
- Task 07 (Doc Gen) - Developer C

**Week 11-12:**

- Task 08 (WebSocket) - Developer A
- Task 09 (Workflow) - Developer B

**Week 13-16:**

- Task 10 (Testing) - All developers
- Integration and polish

**Timeline:** 10-12 weeks with 3 developers

## Current Codebase Assets

The following assets already exist and should be reused:

### Database

- `schema.sql` - Basic schema with memoires, projects, sections, document_chunks
- `migrations/` - RAG optimization migrations

### Services

- `services/supabase.py` - Supabase connection (keep)
- `services/rag.py` - RAG service with embeddings (enhance, keep)
- `services/parser.py` - Basic PDF parsing (enhance)
- `services/generator.py` - Basic generation (enhance)
- `services/exporter.py` - Basic Word export (enhance)

### Configuration

- `config.py` - Environment configuration
- `main.py` - FastAPI app (enhance with new routes)

## Quick Start for Claude Code Agents

To work on a specific task:

1. **Read the task file** (e.g., `tasks/01-database-schema-migration.md`)
2. **Check dependencies** - Ensure prerequisite tasks are complete
3. **Review deliverables** - Understand what needs to be built
4. **Check existing code** - See what can be reused
5. **Follow implementation steps** - Work through the checklist
6. **Run tests** - Verify the implementation
7. **Update documentation** - Document any changes

## Environment Variables

Create `.env` file with:

```bash
# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# AI
CLAUDE_API_KEY=your_claude_key

# Auth
JWT_SECRET_KEY=generate_random_256bit_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Storage
SUPABASE_BUCKET=memoire-files
```

## Success Metrics

### Development

- All tasks completed with >80% test coverage
- CI/CD pipeline passing
- Documentation complete

### Product

- Generate memoir in <2 hours (vs. 3-5 days)
- 90%+ generated content requires no modification
- User satisfaction >8/10
- Cost <$2.50 per memoir

## Cost Estimates

### Per Memoir Generation

- RC Analysis: $0.10
- Content Matching: $0.25
- AI Generation: $1.50
- **Total: ~$2.00**

### Infrastructure (Monthly)

- Supabase: $25 (free tier sufficient for MVP)
- Hosting: $0 (local) to $50 (cloud)
- Claude API: Pay-per-use (~$100/month for 50 memoirs)

## Support

For questions or issues:

1. Check the specific task README
2. Review the main UPDATE.md for architecture details
3. Check concept.md for business context
4. Consult existing code in services/

## Next Steps

1. **Review this README** to understand overall architecture
2. **Pick a task** based on dependencies and your expertise
3. **Read task details** in the specific task file
4. **Start coding** with confidence!

---

**Note:** Each task is designed to be completed by a separate Claude Code instance. The task files include all context needed to work independently.
