# Database Schema Documentation

## Overview

The Memoir Generator uses Supabase (PostgreSQL) with pgvector extension for vector similarity search.

## Tables

### 1. `memoires`
Stores metadata about reference memoir documents.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `filename` | VARCHAR(255) | Original filename |
| `storage_path` | VARCHAR(500) | Path in Supabase Storage |
| `client` | VARCHAR(255) | Client name (optional) |
| `year` | INTEGER | Year of the project (optional) |
| `indexed` | BOOLEAN | Whether the document has been indexed for RAG |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

### 2. `projects`
Stores memoir generation projects.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `name` | VARCHAR(255) | Project name |
| `rc_storage_path` | VARCHAR(500) | Path to RC document in storage |
| `rc_context` | TEXT | Extracted context from RC |
| `status` | VARCHAR(50) | Project status (draft, generating, ready) |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

### 3. `sections`
Stores generated content sections for each project.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `project_id` | UUID | Foreign key to projects |
| `section_type` | VARCHAR(100) | Type of section (presentation, methodologie, etc.) |
| `title` | VARCHAR(255) | Section title |
| `content` | TEXT | Generated markdown content |
| `order_num` | INTEGER | Display order |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

**Foreign Keys:**
- `project_id` → `projects(id)` ON DELETE CASCADE

### 4. `document_chunks`
Stores text chunks with vector embeddings for RAG.

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key (auto-generated) |
| `memoire_id` | UUID | Foreign key to memoires |
| `content` | TEXT | Text chunk content |
| `embedding` | vector(1536) | OpenAI embedding vector |
| `metadata` | JSONB | Additional metadata (chunk_index, filename, etc.) |
| `created_at` | TIMESTAMPTZ | Creation timestamp |

**Foreign Keys:**
- `memoire_id` → `memoires(id)` ON DELETE CASCADE

## Indexes

### Performance Indexes
- `idx_chunks_memoire` - Index on `document_chunks(memoire_id)`
- `idx_sections_project` - Index on `sections(project_id, order_num)`

### Vector Index
- IVFFlat index on `document_chunks(embedding)` using `vector_cosine_ops`
  - Lists: 100 (suitable for up to ~1M vectors)
  - Operator: `<=>` (cosine distance)

## Functions

### `match_documents()`
Semantic search function for RAG.

**Signature:**
```sql
match_documents(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    memoire_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
)
```

**Parameters:**
- `query_embedding`: The embedding vector to search for
- `match_count`: Number of results to return (default: 10)
- `memoire_ids`: Optional filter by specific memoir IDs

**Returns:**
- `id`: Chunk ID
- `content`: Text content
- `metadata`: JSONB metadata
- `similarity`: Similarity score (0-1, higher is better)

**Example:**
```python
result = supabase.rpc('match_documents', {
    'query_embedding': embedding_vector,
    'match_count': 10,
    'memoire_ids': ['uuid1', 'uuid2']
}).execute()
```

## Setup Instructions

### Option 1: Using Python Script
```bash
source venv/bin/activate
python -c "
import psycopg2
from config import Config
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DIRECT_URL')
conn = psycopg2.connect(db_url)
conn.autocommit = True
cursor = conn.cursor()

with open('schema.sql', 'r') as f:
    sql = f.read()

cursor.execute(sql)
cursor.close()
conn.close()
print('✅ Database schema created!')
"
```

### Option 2: Using Supabase SQL Editor
1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Navigate to **SQL Editor**
4. Create a new query
5. Copy and paste the contents of `schema.sql`
6. Click **Run**

## Verification

Test the setup:
```python
from supabase import create_client
from config import Config

client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Test tables
tables = ['memoires', 'projects', 'sections', 'document_chunks']
for table in tables:
    result = client.table(table).select('*').limit(1).execute()
    print(f'✅ {table} - OK')

# Test function
test_embedding = [0.0] * 1536
result = client.rpc('match_documents', {
    'query_embedding': test_embedding,
    'match_count': 5
}).execute()
print(f'✅ match_documents() - OK')
```

## Migrations

For schema changes:
1. Modify `schema.sql`
2. Drop and recreate (for development only!)
3. For production, create migration scripts that preserve data

## Storage Setup

The storage bucket is automatically created by the setup script.

### Automated Setup (Recommended)
```bash
source venv/bin/activate
python -c "
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DIRECT_URL')
conn = psycopg2.connect(db_url)
conn.autocommit = True
cursor = conn.cursor()

with open('setup_storage.sql', 'r') as f:
    cursor.execute(f.read())

cursor.close()
conn.close()
print('✅ Storage bucket created!')
"
```

### Manual Setup (Alternative)
1. Go to **Storage** in Supabase Dashboard
2. Create bucket named `memoires` (or value from `.env`)
3. Set as **Private** (not public)
4. Policies are configured via SQL for:
   - Service role: Full access
   - Authenticated users: Read/Write access

## pgvector Extension

The `vector` extension is automatically enabled by `schema.sql`.

**Vector Operations:**
- `<->` - L2 distance
- `<#>` - Inner product
- `<=>` - Cosine distance (used in this project)

**Index Types:**
- `ivfflat` - Approximate nearest neighbor (faster, less accurate)
- `hnsw` - Hierarchical Navigable Small World (more accurate, slower build)

Current configuration uses IVFFlat with 100 lists, suitable for up to 1M vectors.
