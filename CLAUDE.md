# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI backend service for generating technical memoirs (mémoires techniques) for the construction industry (BTP - Bâtiment et Travaux Publics) using RAG (Retrieval Augmented Generation). The system indexes reference memoirs, uses semantic search to find relevant content, and generates new memoir sections using Claude API.

## Core Architecture

### Three-Layer System

1. **Reference Layer** (Memoires)
   - Upload and parse reference memoirs (PDF/DOCX)
   - Chunk text into semantic units (500 chars, 50 char overlap)
   - Generate embeddings using OpenAI text-embedding-3-small (1536 dimensions)
   - Store in Supabase pgvector for semantic search

2. **RAG Layer** (Search & Retrieval)
   - Semantic search across indexed memoirs using cosine similarity
   - PostgreSQL function `match_documents()` performs database-side filtering
   - Optimized for performance with IVFFlat vector index (lists=10)

3. **Generation Layer** (Projects & Sections)
   - Create projects with RC (Règlement de Consultation) documents
   - Generate 9 section types: presentation, organisation, methodologie, moyens_humains, moyens_materiels, planning, environnement, securite, insertion
   - Each section generation: RAG search → Claude API → markdown output → database storage
   - Export to Word document with Bernadet styling (Arial, blue/green headings)

### Database Schema Flow

```
memoires (reference docs)
    ↓ (chunks & embeddings)
document_chunks (RAG vectors)
    ↓ (search)
projects (generation jobs)
    ↓ (generated content)
sections (markdown output)
```

Key relationships:
- `document_chunks.memoire_id` → `memoires.id` (ON DELETE CASCADE)
- `sections.project_id` → `projects.id` (ON DELETE CASCADE)

### Service Architecture

- **SupabaseService** (`services/supabase.py`): All database/storage operations
- **ParserService** (`services/parser.py`): PDF/DOCX parsing, text chunking
- **RAGService** (`services/rag.py`): Embeddings generation (OpenAI), vector search
- **GeneratorService** (`services/generator.py`): Section generation with Claude API
- **ExporterService** (`services/exporter.py`): Markdown to Word conversion

Services are initialized once at app startup in `main.py` (lines 60-64) and reused across requests.

## Development Commands

### Running the Server

**Local development** (with auto-reload):
```bash
source venv/bin/activate
python main.py
# OR
uvicorn main:app --reload --port 8000
```

**Docker** (recommended for consistent environment):
```bash
docker-compose up          # Start all services
docker-compose up -d       # Run in background
docker-compose logs -f backend  # View logs
docker-compose down        # Stop services
docker-compose up --build  # Rebuild after code changes
```

### Dependencies

Install/update dependencies:
```bash
pip install -r requirements.txt
```

If adding new packages, update `requirements.txt` with pinned versions.

### Database Migrations

The project uses raw SQL migrations in the `migrations/` folder. To apply:

1. Run SQL directly in Supabase SQL Editor (Dashboard → SQL Editor)
2. Or use psql with `DATABASE_URL` from `.env`

**Important**: The `schema.sql` file is the source of truth for initial setup. Do NOT edit it directly for migrations - create new files in `migrations/`.

## Configuration

All configuration is loaded from `.env` via `config.py`:

- **Required**: `CLAUDE_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`
- **Optional**: `SUPABASE_STORAGE_BUCKET` (defaults to "memoires")

Config validation runs at startup (`Config.validate()` in main.py:42).

## API Workflow

### Complete Generation Flow

1. **Upload Reference Memoirs**
   - `POST /memoires/upload` - Auto-parses and chunks on upload
   - `POST /memoires/{id}/index` - Generates embeddings for RAG

2. **Create Project**
   - `POST /projects` - Create new project
   - `POST /projects/{id}/upload-rc` - Upload RC document (extracts context)

3. **Generate Memoir**
   - `POST /projects/{id}/generate` - Generate sections using RAG + Claude
     - For each section: RAG search (10 results, 0.5 threshold) → Claude prompt → save
     - Typical time: 30-60 seconds per section

4. **Export**
   - `GET /projects/{id}/download` - Download as Word document

### RAG Search Parameters

When using RAG search (in `services/rag.py:search()`):
- `n_results`: 10 (optimal for context without overwhelming Claude)
- `similarity_threshold`: 0.5 (filters weak matches, improves quality)
- Chunks are ordered by similarity (best matches first)

## Code Style & Patterns

### Error Handling

The codebase uses verbose logging with emoji prefixes for debugging:
- 🚀 Starting operation
- ✅ Success
- ❌ Error
- 🔍 Search/lookup
- 📦 Upload/storage
- 💾 Database operation
- 🤖 AI/LLM operation

Always include detailed error logging:
```python
except Exception as e:
    print(f"❌ Operation failed: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    raise HTTPException(status_code=500, detail=f"Failed: {str(e)}")
```

### Database Operations

All database operations go through `SupabaseService`. Use the service methods rather than direct Supabase client calls:
- `create_memoire()`, `get_memoire()`, `delete_memoire()`
- `create_project()`, `update_project_status()`, `delete_project()`
- `create_section()`, `get_sections()`

Foreign key cascades handle cleanup automatically (e.g., deleting a memoire deletes all chunks).

### Claude API Integration

Model: `claude-sonnet-4-20250514` (Sonnet 4.5)
- Max tokens: 4096 (default for sections)
- Temperature: 0.7 (balanced creativity/consistency)
- Always uses structured prompts with RC context + reference chunks

Prompt structure in `GeneratorService._build_prompt()`:
1. System context (expert role)
2. RC context (project requirements)
3. Section type description
4. Top 5 reference chunks by similarity
5. Instructions (format, length, constraints)

### Vector Operations

OpenAI embeddings format for pgvector:
```python
embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'
```

Supabase Python client requires string format for vector types, not JSON arrays.

## Performance Considerations

### RAG Optimizations

The system has been optimized for Supabase free tier:
- Reduced chunk overlap (50 chars vs 100, reduces chunks by ~40%)
- Database-side similarity filtering (PostgreSQL function filters before returning)
- IVFFlat index with lists=10 (optimal for small-medium datasets)
- Text cleaning removes whitespace/headers/footers before chunking

See `OPTIMIZATION_SUMMARY.md` (referenced in README but deleted from repo) for historical context.

### Batch Processing

RAG indexing processes chunks in batches of 100:
```python
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    embeddings = generate_embeddings_batch(texts)
```

OpenAI allows up to 2048 inputs per batch request.

## Testing

The codebase does not currently have automated tests. When adding features:
1. Test via Swagger UI at `http://localhost:8000/docs`
2. Use curl commands from README examples
3. Check logs for verbose operation details

## File Storage

Supabase Storage bucket structure:
```
memoires/
  ├── {timestamp}_{filename}.pdf  (uploaded memoirs)
projects/
  ├── {project_id}/
      ├── rc.pdf  (RC document)
      └── (generated outputs stored in data/ folder locally)
```

Storage operations use `SupabaseService.upload_file()` and `download_file()`.

Generated Word documents are stored locally in `data/` and returned via FileResponse (not stored in Supabase).

## Common Gotchas

1. **Embedding dimension mismatch**: Always use 1536 dimensions for text-embedding-3-small
2. **Chunk parsing on upload**: Documents are automatically parsed when uploaded (don't need manual parse unless re-parsing)
3. **Project status transitions**: draft → generating → ready/partial/failed
4. **Memoire indexing**: Must index memoirs before using them for generation (check `indexed` flag)
5. **Vector format**: Supabase Python client requires string format `'[1,2,3]'` not list `[1,2,3]`

## Section Types

9 valid section types (in French):
- `presentation` - Company presentation
- `organisation` - Site organization
- `methodologie` - Implementation methodology
- `moyens_humains` - Human resources
- `moyens_materiels` - Material resources
- `planning` - Schedule
- `environnement` - Environmental approach
- `securite` - Safety and health
- `insertion` - Social integration

Each has specialized prompts in `GeneratorService.SECTION_DESCRIPTIONS`.

## Supabase Connection

The app uses `service_role` key which bypasses Row Level Security (RLS). This is intentional for backend operations. Do not use `anon` key for API endpoints.

SSL certificate at `supabase_ssl_cert.crt` is loaded for secure PostgreSQL connections.
