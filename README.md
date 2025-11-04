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
│   └── supabase.py           # Supabase client & DB operations
├── models/                    # Pydantic schemas (future)
├── utils/                     # Helper functions (future)
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

### Current (Step 1)

- `GET /` - API information
- `GET /health` - Health check

### Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Planned (Future Steps)

- `POST /memoires/upload` - Upload reference memoir (PDF/DOCX)
- `POST /memoires/{id}/index` - Index memoir for RAG
- `GET /memoires` - List all memoirs
- `POST /projects` - Create new project
- `POST /projects/{id}/upload-rc` - Upload RC document
- `POST /projects/{id}/generate` - Generate memoir sections
- `GET /projects/{id}/download` - Download generated Word document
- `GET /projects` - List all projects

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

### What's Working

- ✅ FastAPI server with health check
- ✅ Supabase client initialization
- ✅ Configuration management
- ✅ All dependencies installed and up-to-date
- ✅ Database schema with vector search capability
- ✅ PostgreSQL functions for RAG operations
- ✅ Docker & Docker Compose setup
- ✅ Redis for caching on port 6380 (optional)

### Next Steps

1. **Step 3**: Parser Service
   - PDF parsing (pypdf)
   - DOCX parsing (python-docx)
   - Text chunking for RAG

3. **Step 4**: RAG Service
   - OpenAI embeddings generation
   - Vector storage in pgvector
   - Semantic search

4. **Step 5**: Generator Service
   - Claude API integration
   - Section generation with context
   - Prompt engineering

5. **Step 6**: Exporter Service
   - Word document generation
   - Template management
   - Styling

6. **Step 7**: API Endpoints
   - Implement all CRUD operations
   - File upload handling
   - Error handling

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
