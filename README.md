# Memoir Generator Backend - MVP

Backend API for generating technical memoirs using RAG (Retrieval Augmented Generation).

## Tech Stack

- **Framework**: FastAPI 0.115.6
- **Database**: Supabase (PostgreSQL + pgvector)
- **Storage**: Supabase Storage
- **LLM**: Claude API (Anthropic) - Sonnet 4.5
- **Embeddings**: OpenAI text-embedding-3-small
- **Document Processing**: pypdf, python-docx

## Project Structure

```
backend/
├── venv/                      # Python virtual environment
├── services/
│   ├── __init__.py
│   ├── supabase.py           # Supabase client & DB operations
│   └── parser.py             # PDF/DOCX parsing & text chunking
├── models/
│   ├── __init__.py
│   └── schemas.py            # Pydantic models for API validation
├── utils/
│   ├── __init__.py
│   └── helpers.py            # File validation utilities
├── templates/                 # Word templates (future)
├── data/                      # Generated output files
├── main.py                   # FastAPI application
├── config.py                 # Configuration from .env
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not in git)
└── README.md                 # This file
```

## Setup

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Make sure your `.env` file contains:

```env
# Supabase
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_ANON_KEY="eyJ..."
SUPABASE_SERVICE_ROLE_KEY="eyJ..."
SUPABASE_STORAGE_BUCKET="memoires"
DATABASE_URL="postgresql://..."

# AI Services
CLAUDE_API_KEY="sk-ant-..."
OPENAI_API_KEY="sk-..."
```

## Running the Server

### Option 1: Docker (Recommended)

**Start all services:**

```bash
docker-compose up
```

**Start in background:**

```bash
docker-compose up -d
```

**View logs:**

```bash
docker-compose logs -f backend
```

**Stop services:**

```bash
docker-compose down
```

**Rebuild after code changes:**

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

### Option 2: Local Development (without Docker)

**Development Mode (with auto-reload):**

```bash
source venv/bin/activate
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --port 8000
```

**Production Mode:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### System

- `GET /` - API information
- `GET /health` - Health check (database + storage)

### Memoires

- `POST /memoires/upload` - Upload PDF/DOCX (auto-parses and chunks)
- `GET /memoires` - List all uploaded memoires
- `GET /memoires/{id}` - Get memoire details
- `GET /memoires/{id}/chunks` - Get all chunks for a memoire
- `POST /memoires/{id}/parse` - Re-parse and chunk document
- `POST /memoires/{id}/index` - Generate embeddings and index for RAG
- `DELETE /memoires/{id}` - Delete memoire and all associated data

### RAG (Search)

- `POST /search` - Semantic search across indexed memoires

### Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Generation (Step 5 Complete)

- `POST /projects` - Create new project
- `GET /projects` - List all projects
- `GET /projects/{id}` - Get project details
- `POST /projects/{id}/upload-rc` - Upload RC document
- `POST /projects/{id}/generate` - Generate memoir sections
- `GET /projects/{id}/sections` - Get generated sections

### Planned (Future Steps)

- `GET /projects/{id}/download` - Download generated Word document

## Current Status

✅ **Step 1 Complete**: Initial Setup

- FastAPI server running
- Supabase connection working
- All API keys validated
- Latest packages installed

✅ **Step 2 Complete**: Database Schema Setup

- All tables created (memoires, projects, sections, document_chunks)
- pgvector extension enabled
- Vector similarity index created (IVFFlat)
- match_documents() PostgreSQL function created

✅ **Step 3 Complete**: Parser Service

- PDF parsing with pypdf
- DOCX parsing with python-docx
- Text chunking with sliding window (500 chars, 100 overlap)
- File upload with validation (50MB limit - Supabase free tier)
- Automatic parsing and chunking on upload
- Manual re-parse functionality
- Chunks stored in database (without embeddings)

✅ **Step 4 Complete**: RAG Service (Indexing & Search)

- OpenAI embeddings generation (text-embedding-3-small)
- Batch embedding processing for efficiency
- Embedding storage in pgvector
- Semantic search with similarity scoring
- Filter search by specific memoires
- Configurable result count and similarity threshold
- **Optimized for performance**:
  - Text cleaning (removes whitespace, headers, footers)
  - Reduced chunk overlap (50 chars, 40% fewer chunks)
  - Database-side similarity filtering (30-50% faster)
  - Optimized vector index for free tier (lists=10)

### What's Working

- ✅ FastAPI server with health check
- ✅ Supabase client initialization and storage
- ✅ Configuration management
- ✅ Database schema with vector search capability
- ✅ PostgreSQL functions for RAG operations
- ✅ Docker & Docker Compose setup
- ✅ **PDF/DOCX upload and parsing**
- ✅ **Automatic text chunking on upload**
- ✅ **Chunk storage and retrieval**
- ✅ **Delete memoires with CASCADE cleanup**
- ✅ **Basic frontend test interface**
- ✅ **OpenAI embeddings generation**
- ✅ **Vector indexing in pgvector**
- ✅ **Semantic search with similarity scoring**
- ✅ **Performance optimizations** (see [OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md))
- ✅ **Claude API integration for memoir generation**
- ✅ **Project management system (create, upload RC, generate)**
- ✅ **Intelligent section generation with RAG context**
- ✅ **9 section types with specialized prompts**
- ✅ **Real-time generation with progress tracking**

✅ **Step 5 Complete**: Generator Service

- Claude API integration (Sonnet 4.5) for memoir generation
- Section generation with RAG context
- Intelligent prompt engineering for technical memoirs
- 9 section types supported (presentation, organisation, methodologie, etc.)
- Project workflow: create → upload RC → generate sections
- Real-time generation with progress tracking
- Error handling with partial generation support

### Next Steps

1. **Step 6**: Exporter Service

   - Word document generation from sections
   - Template management for Bernadet style
   - Markdown to Word conversion
   - Styling and formatting
   - Download endpoint for generated memoirs

2. **Step 7**: Advanced Features (Optional)
   - Section regeneration capability
   - Multiple memoir templates
   - RC criteria extraction enhancement
   - Image and annexe support

## Usage Examples

### Complete RAG Workflow

Here's a complete example of uploading, indexing, and searching memoires:

#### 1. Upload a Memoire

```bash
curl -X POST "http://localhost:8000/memoires/upload" \
  -F "file=@memoire_toulouse.pdf" \
  -F "client=Toulouse Metropole" \
  -F "year=2024"
```

Response:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "memoire_toulouse.pdf",
  "storage_path": "memoires/1699564800_memoire_toulouse.pdf",
  "client": "Toulouse Metropole",
  "year": 2024,
  "indexed": false,
  "parsed": true,
  "created_at": "2024-11-04T10:00:00Z"
}
```

Note: The document is automatically parsed and chunked on upload!

#### 2. Index the Memoire (Generate Embeddings)

```bash
curl -X POST "http://localhost:8000/memoires/550e8400-e29b-41d4-a716-446655440000/index"
```

Response:

```json
{
  "memoire_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "indexed",
  "chunks_indexed": 45,
  "embeddings_generated": 45,
  "message": "Successfully indexed 45 chunks"
}
```

This process:

- Generates embeddings using OpenAI's `text-embedding-3-small` (1536 dimensions)
- Stores embeddings in pgvector
- Marks the memoire as indexed

#### 3. Search Across Memoires

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "organisation du chantier et moyens humains",
    "n_results": 5,
    "similarity_threshold": 0.7
  }'
```

Response:

```json
{
  "query": "organisation du chantier et moyens humains",
  "results": [
    {
      "id": "chunk-123",
      "content": "L'organisation du chantier sera assurée par...",
      "metadata": {
        "filename": "memoire_toulouse.pdf",
        "client": "Toulouse Metropole",
        "chunk_index": 12
      },
      "similarity": 0.89,
      "memoire_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ],
  "count": 5
}
```

#### 4. Search Within Specific Memoires

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "sécurité et santé",
    "memoire_ids": ["550e8400-e29b-41d4-a716-446655440000", "660e8400-e29b-41d4-a716-446655440001"],
    "n_results": 10
  }'
```

### List All Memoires

```bash
curl -X GET "http://localhost:8000/memoires"
```

### Get Memoire Details

```bash
curl -X GET "http://localhost:8000/memoires/550e8400-e29b-41d4-a716-446655440000"
```

### View Chunks

```bash
curl -X GET "http://localhost:8000/memoires/550e8400-e29b-41d4-a716-446655440000/chunks"
```

### Delete a Memoire

```bash
curl -X DELETE "http://localhost:8000/memoires/550e8400-e29b-41d4-a716-446655440000"
```

This deletes:

- The file from Supabase Storage
- The database record
- All chunks (via CASCADE)
- All embeddings (via CASCADE)

### Complete Generation Workflow (Step 5)

Here's a complete example of creating a project and generating memoir sections:

#### 1. Create a Project

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Résidence Personnes Âgées - Toulouse"}'
```

Response:

```json
{
  "id": "4cf0ac0e-dbc9-46e7-bfb9-f8ad64c889e1",
  "name": "Résidence Personnes Âgées - Toulouse",
  "status": "draft",
  "created_at": "2025-11-04T17:45:20Z"
}
```

#### 2. Upload RC Document

```bash
curl -X POST "http://localhost:8000/projects/4cf0ac0e-dbc9-46e7-bfb9-f8ad64c889e1/upload-rc" \
  -F "file=@rc_toulouse.pdf"
```

Response:

```json
{
  "project_id": "4cf0ac0e-dbc9-46e7-bfb9-f8ad64c889e1",
  "rc_uploaded": true,
  "rc_storage_path": "projects/4cf0ac0e-dbc9-46e7-bfb9-f8ad64c889e1/rc.pdf"
}
```

#### 3. Generate Memoir Sections

```bash
curl -X POST "http://localhost:8000/projects/4cf0ac0e-dbc9-46e7-bfb9-f8ad64c889e1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "memoire_ids": ["550e8400-e29b-41d4-a716-446655440000", "660e8400-e29b-41d4-a716-446655440001"],
    "sections": ["presentation", "organisation", "methodologie", "moyens_humains", "moyens_materiels"]
  }'
```

Response:

```json
{
  "project_id": "4cf0ac0e-dbc9-46e7-bfb9-f8ad64c889e1",
  "status": "ready",
  "sections": [
    {
      "id": "eb22718d-372e-4eb1-91d9-569e2ca87efd",
      "section_type": "presentation",
      "title": "Presentation"
    },
    {
      "id": "19176c26-0847-4e28-8e84-59f55f369d74",
      "section_type": "organisation",
      "title": "Organisation"
    }
  ],
  "message": "Successfully generated all 5 sections"
}
```

**Generation Time:** Typically 30-60 seconds per section (~3-5 minutes for 5 sections)

#### 4. View Generated Sections

```bash
curl -X GET "http://localhost:8000/projects/4cf0ac0e-dbc9-46e7-bfb9-f8ad64c889e1/sections"
```

This returns all generated sections with their full markdown content.

#### Valid Section Types

- `presentation` - Company presentation (history, certifications, key figures)
- `organisation` - Site organization (PIC, logistics, planning)
- `methodologie` - Implementation methodology (phasing, techniques)
- `moyens_humains` - Human resources (org chart, staffing)
- `moyens_materiels` - Material resources (equipment list, capacities)
- `planning` - Schedule (Gantt, deadlines)
- `environnement` - Environmental approach (CSR, waste management)
- `securite` - Safety and health (PPSPS, prevention measures)
- `insertion` - Social integration (planned integration hours)

## Development Notes

### API Keys

- **Supabase**: Uses JWT-based `service_role` key for backend operations (bypasses RLS)
- **Claude**: Sonnet 4.5 for content generation
- **OpenAI**: text-embedding-3-small for vector embeddings

### Database

The app uses Supabase which provides:

- PostgreSQL database
- pgvector extension for vector similarity search
- Storage (S3-compatible) for file uploads
- Auto-generated REST API

## Troubleshooting

### Docker Issues

**Port Already in Use:**

```bash
# Stop all containers
docker-compose down

# Or kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Container Won't Start:**

```bash
# Check logs
docker-compose logs backend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

**Database Connection Issues:**

```bash
# Check .env file has correct DATABASE_URL
# Ensure Supabase project is active
# Test connection:
docker-compose exec backend python -c "from config import Config; Config.validate(); print('Config OK')"
```

### Local Development Issues

**Port Already in Use:**

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

**Module Not Found:**

```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Supabase Connection Issues

- Check `.env` file has correct `SUPABASE_SERVICE_ROLE_KEY`
- Verify Supabase project is active at https://app.supabase.com
- Check database URL is correct

## License

Private project for Enpyco.
