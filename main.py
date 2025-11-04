from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os

from config import Config
from services.supabase import SupabaseService
from services.parser import ParserService
from services.rag import RAGService
from models.schemas import (
    MemoireUploadResponse,
    MemoireMetadata,
    MemoireListResponse,
    ParseResponse,
    IndexResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    HealthResponse,
)
from utils.helpers import (
    validate_file_type,
    validate_file_size,
    generate_storage_path,
    format_file_size,
    extract_year_from_filename,
)

# Validate configuration on startup
Config.validate()

app = FastAPI(
    title="Memoir Generator MVP",
    description="Backend API for generating technical memoirs using RAG",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
supabase_service = SupabaseService()
parser_service = ParserService(chunk_size=500, chunk_overlap=100)
rag_service = RAGService()

# === HEALTH CHECK ===

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["System"]
)
async def health_check():
    """Health check endpoint to verify the API is running."""
    return HealthResponse(
        status="ok",
        database="connected",
        storage="connected"
    )

@app.get(
    "/",
    summary="API information",
    tags=["System"]
)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Memoir Generator API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }

# === MEMOIRE ENDPOINTS ===

@app.post(
    "/memoires/upload",
    response_model=MemoireUploadResponse,
    summary="Upload a memoire file",
    tags=["Memoires"]
)
async def upload_memoire(
    file: UploadFile = File(...),
    client: Optional[str] = None,
    year: Optional[int] = None
):
    """
    Upload a reference memoir file (PDF or DOCX).

    The file will be:
    1. Stored in Supabase Storage
    2. Automatically parsed (PDF or DOCX)
    3. Automatically chunked (500 chars with 100 overlap)
    4. Metadata saved to database

    After upload, you can index it using POST /memoires/{id}/index

    **Supported formats**: PDF, DOCX
    **Max file size**: 50 MB (Supabase free tier limit)

    Args:
        file: The memoir file to upload (PDF or DOCX)
        client: Optional client name
        year: Optional year of the memoir

    Returns:
        MemoireUploadResponse with the created memoire details
    """
    # Validate file type
    is_valid_type, error_msg = validate_file_type(file.filename)
    if not is_valid_type:
        raise HTTPException(status_code=400, detail=error_msg)

    # Read file content
    file_content = await file.read()
    file_size_mb = round(len(file_content) / (1024 * 1024), 2)

    # Log file upload attempt
    print(f"📤 Upload attempt: {file.filename} ({file_size_mb} MB)")

    # Validate file size
    is_valid_size, error_msg = validate_file_size(len(file_content))
    if not is_valid_size:
        print(f"❌ Upload rejected: {error_msg}")
        raise HTTPException(status_code=400, detail=error_msg)

    print(f"✅ File size validation passed: {file_size_mb} MB")

    # Try to extract year from filename if not provided
    if year is None:
        year = extract_year_from_filename(file.filename)

    # Generate storage path
    storage_path = generate_storage_path(file.filename, prefix="memoires")

    try:
        # Upload to Supabase Storage
        print(f"📦 Uploading to Supabase Storage: {storage_path}")
        supabase_service.upload_file(
            bucket="memoires",
            path=storage_path,
            file_data=file_content
        )
        print(f"✅ Upload to storage successful")

        # Create database record
        print(f"💾 Creating database record...")
        memoire_id = supabase_service.create_memoire(
            filename=file.filename,
            storage_path=storage_path,
            client=client,
            year=year
        )
        print(f"✅ Database record created: {memoire_id}")

        # Get the created memoire
        memoire = supabase_service.get_memoire(memoire_id)

        # Automatically parse and chunk the document
        print(f"🔄 Auto-parsing document...")
        try:
            # Download and parse
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            try:
                parse_result = parser_service.parse_file(tmp_path)
                chunks = parser_service.chunk_text(
                    text=parse_result.full_text,
                    metadata={
                        'memoire_id': memoire_id,
                        'filename': file.filename,
                        'client': client,
                        'year': year,
                    }
                )

                # Store chunks in database (without embeddings)
                chunks_stored = 0
                for chunk in chunks:
                    supabase_service.client.table('document_chunks').insert({
                        'memoire_id': memoire_id,
                        'content': chunk.content,
                        'metadata': chunk.metadata,
                        'embedding': None  # Will be filled in Step 4 (Index)
                    }).execute()
                    chunks_stored += 1

                print(f"✅ Auto-parse complete: {chunks_stored} chunks stored")

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as parse_error:
            print(f"⚠️ Auto-parse failed (non-fatal): {parse_error}")
            # Don't fail the upload if parse fails

        return MemoireUploadResponse(
            id=memoire['id'],
            filename=memoire['filename'],
            storage_path=memoire['storage_path'],
            client=memoire.get('client'),
            year=memoire.get('year'),
            indexed=memoire.get('indexed', False),
            parsed=True,  # Now parsed automatically
            created_at=memoire['created_at']
        )

    except Exception as e:
        print(f"❌ Upload failed with error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload memoire: {str(e)}")


@app.post(
    "/memoires/{memoire_id}/parse",
    response_model=ParseResponse,
    summary="Re-parse and chunk a memoire",
    tags=["Memoires"]
)
async def parse_memoire(memoire_id: str):
    """
    Re-parse and chunk a memoire file.

    Downloads the file from storage, parses it (PDF or DOCX),
    and creates text chunks for RAG. Does NOT create embeddings yet.

    **Note**: Files are automatically parsed on upload. Use this only if you need to re-parse.

    Args:
        memoire_id: UUID of the memoire to parse

    Returns:
        ParseResponse with parsing results and chunk count
    """
    # Get memoire from database
    memoire = supabase_service.get_memoire(memoire_id)
    if not memoire:
        raise HTTPException(status_code=404, detail="Memoire not found")

    try:
        # Download file from Supabase Storage
        file_data = supabase_service.download_file(
            bucket="memoires",
            path=memoire['storage_path']
        )

        # Save to temporary file
        file_ext = os.path.splitext(memoire['filename'])[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
            tmp_file.write(file_data)
            tmp_path = tmp_file.name

        try:
            # Parse the file
            parse_result = parser_service.parse_file(tmp_path)

            # Chunk the text
            chunks = parser_service.chunk_text(
                text=parse_result.full_text,
                metadata={
                    'memoire_id': memoire_id,
                    'filename': memoire['filename'],
                    'client': memoire.get('client'),
                    'year': memoire.get('year'),
                }
            )

            # Delete existing chunks for this memoire (re-parse = replace)
            print(f"🗑️ Deleting existing chunks for memoire: {memoire_id}")
            supabase_service.client.table('document_chunks').delete().eq('memoire_id', memoire_id).execute()

            # Store chunks in database (without embeddings)
            chunks_stored = 0
            for chunk in chunks:
                supabase_service.client.table('document_chunks').insert({
                    'memoire_id': memoire_id,
                    'content': chunk.content,
                    'metadata': chunk.metadata,
                    'embedding': None  # Will be filled in Step 4 (Index)
                }).execute()
                chunks_stored += 1

            print(f"✅ Re-parse complete: {chunks_stored} chunks stored")

            return ParseResponse(
                memoire_id=memoire_id,
                status="parsed",
                chunks_created=chunks_stored,
                char_count=parse_result.char_count,
                parse_result=parse_result
            )

        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse memoire: {str(e)}")


@app.get(
    "/memoires",
    response_model=MemoireListResponse,
    summary="List all memoires",
    tags=["Memoires"]
)
async def list_memoires():
    """
    List all uploaded memoires.

    Returns:
        MemoireListResponse with list of all memoires
    """
    try:
        memoires = supabase_service.list_memoires()

        memoires_list = [
            MemoireMetadata(
                id=m['id'],
                filename=m['filename'],
                storage_path=m['storage_path'],
                client=m.get('client'),
                year=m.get('year'),
                indexed=m.get('indexed', False),
                created_at=m['created_at']
            )
            for m in memoires
        ]

        return MemoireListResponse(
            memoires=memoires_list,
            count=len(memoires_list)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list memoires: {str(e)}")


@app.get(
    "/memoires/{memoire_id}",
    response_model=MemoireMetadata,
    summary="Get memoire details",
    tags=["Memoires"]
)
async def get_memoire(memoire_id: str):
    """
    Get details of a specific memoire.

    Args:
        memoire_id: UUID of the memoire

    Returns:
        MemoireMetadata with memoire details
    """
    memoire = supabase_service.get_memoire(memoire_id)
    if not memoire:
        raise HTTPException(status_code=404, detail="Memoire not found")

    return MemoireMetadata(
        id=memoire['id'],
        filename=memoire['filename'],
        storage_path=memoire['storage_path'],
        client=memoire.get('client'),
        year=memoire.get('year'),
        indexed=memoire.get('indexed', False),
        created_at=memoire['created_at']
    )


@app.get(
    "/memoires/{memoire_id}/chunks",
    summary="Get memoire chunks",
    tags=["Memoires"]
)
async def get_memoire_chunks(memoire_id: str):
    """
    Get all text chunks for a specific memoire.

    Chunks are created during the parsing process (automatically on upload).

    Args:
        memoire_id: UUID of the memoire

    Returns:
        List of chunks with content and metadata
    """
    # Check if memoire exists
    memoire = supabase_service.get_memoire(memoire_id)
    if not memoire:
        raise HTTPException(status_code=404, detail="Memoire not found")

    try:
        chunks = supabase_service.get_chunks(memoire_id)
        chunk_count = len(chunks)

        return {
            "memoire_id": memoire_id,
            "filename": memoire['filename'],
            "chunk_count": chunk_count,
            "chunks": chunks
        }

    except Exception as e:
        print(f"❌ Failed to get chunks: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {str(e)}")


@app.delete(
    "/memoires/{memoire_id}",
    summary="Delete a memoire",
    tags=["Memoires"]
)
async def delete_memoire(memoire_id: str):
    """
    Delete a memoire and all its associated data.

    This will delete:
    - The file from Supabase Storage
    - The memoire record from database
    - All associated chunks (via CASCADE)
    - All associated embeddings/vectors (via CASCADE)

    **Warning**: This operation cannot be undone!

    Args:
        memoire_id: UUID of the memoire to delete

    Returns:
        Success message
    """
    print(f"🗑️ Delete request for memoire: {memoire_id}")

    # Check if memoire exists
    memoire = supabase_service.get_memoire(memoire_id)
    if not memoire:
        raise HTTPException(status_code=404, detail="Memoire not found")

    try:
        # Delete memoire and all associated data
        success = supabase_service.delete_memoire(memoire_id)

        if success:
            print(f"✅ Successfully deleted memoire: {memoire_id}")
            return {
                "success": True,
                "message": f"Memoire '{memoire['filename']}' and all associated data deleted successfully",
                "deleted_id": memoire_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete memoire")

    except Exception as e:
        print(f"❌ Delete failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete memoire: {str(e)}")


# === RAG ENDPOINTS ===

@app.post(
    "/memoires/{memoire_id}/index",
    response_model=IndexResponse,
    summary="Index a memoire for RAG",
    tags=["RAG"],
    responses={
        200: {
            "description": "Memoire successfully indexed",
            "content": {
                "application/json": {
                    "example": {
                        "memoire_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "indexed",
                        "chunks_indexed": 45,
                        "embeddings_generated": 45,
                        "message": "Successfully indexed 45 chunks"
                    }
                }
            }
        },
        404: {"description": "Memoire not found"},
        400: {"description": "No chunks found - parse the memoire first"},
        500: {"description": "Indexing failed"}
    }
)
async def index_memoire(memoire_id: str):
    """
    Generate embeddings for all chunks of a memoire and store them in pgvector.

    This enables semantic search across the memoire content using RAG (Retrieval Augmented Generation).

    ## Process

    1. **Fetch chunks**: Retrieves all text chunks for the memoire
    2. **Generate embeddings**: Uses OpenAI's text-embedding-3-small model (1536 dimensions)
    3. **Store vectors**: Saves embeddings in Supabase pgvector for similarity search
    4. **Mark indexed**: Updates memoire status to indexed=true

    ## Performance

    - Processes chunks in batches of 100
    - Typical speed: ~1-2 seconds per batch
    - A 50-page PDF (~100 chunks) takes about 2-3 minutes

    ## Cost

    - Uses OpenAI text-embedding-3-small
    - Cost: ~$0.00002 per 1K tokens
    - Typical document (50 pages): ~$0.05

    ## After Indexing

    Once indexed, you can:
    - Perform semantic searches using POST /search
    - Find similar content across multiple memoires
    - Use for RAG-based memoir generation
    """
    print(f"🚀 Index request for memoire: {memoire_id}")

    # Check if memoire exists
    memoire = supabase_service.get_memoire(memoire_id)
    if not memoire:
        raise HTTPException(status_code=404, detail="Memoire not found")

    # Check if there are chunks to index
    chunk_count = supabase_service.get_chunk_count(memoire_id)
    if chunk_count == 0:
        raise HTTPException(
            status_code=400,
            detail="No chunks found. Please parse the memoire first using POST /memoires/{id}/parse"
        )

    try:
        # Perform indexing
        result = rag_service.index_memoire(memoire_id)

        return IndexResponse(
            memoire_id=memoire_id,
            status="indexed",
            chunks_indexed=result['chunks_indexed'],
            embeddings_generated=result['embeddings_generated'],
            message=result['message']
        )

    except Exception as e:
        print(f"❌ Indexing failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to index memoire: {str(e)}")


@app.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search across memoires",
    tags=["RAG"],
    responses={
        200: {
            "description": "Search results",
            "content": {
                "application/json": {
                    "example": {
                        "query": "organisation du chantier",
                        "results": [
                            {
                                "id": "chunk-123",
                                "content": "L'organisation du chantier sera assurée par une équipe dédiée...",
                                "metadata": {
                                    "filename": "memoire_toulouse.pdf",
                                    "client": "Toulouse Metropole",
                                    "chunk_index": 12,
                                    "total_chunks": 45
                                },
                                "similarity": 0.89,
                                "memoire_id": "550e8400-e29b-41d4-a716-446655440000"
                            }
                        ],
                        "count": 5
                    }
                }
            }
        },
        500: {"description": "Search failed"}
    }
)
async def search_memoires(search_request: SearchRequest):
    """
    Search for similar content across indexed memoires using semantic search.

    This endpoint uses **RAG (Retrieval Augmented Generation)** to find the most semantically
    similar content across all indexed memoires. Unlike keyword search, semantic search
    understands context and meaning.

    ## How it Works

    1. **Convert query to vector**: Your query is converted to a 1536-dimension embedding
    2. **Vector similarity**: Uses cosine similarity to find closest matches in pgvector
    3. **Rank results**: Returns chunks sorted by similarity score (0.0 to 1.0)

    ## Request Parameters

    - **query** (required): Your search query (e.g., "organisation du chantier")
    - **memoire_ids** (optional): Filter search to specific memoires
    - **n_results** (optional): Maximum results to return (1-100, default: 10)
    - **similarity_threshold** (optional): Minimum similarity score (0.0-1.0, default: 0.0)

    ## Similarity Scores

    - **0.9-1.0**: Extremely similar (almost identical meaning)
    - **0.8-0.9**: Very similar (same topic, similar context)
    - **0.7-0.8**: Similar (related topics)
    - **0.6-0.7**: Somewhat similar
    - **< 0.6**: Weakly related

    ## Example Queries

    ```json
    {
      "query": "organisation du chantier et moyens humains",
      "n_results": 10,
      "similarity_threshold": 0.7
    }
    ```

    Search within specific memoires:
    ```json
    {
      "query": "sécurité et santé",
      "memoire_ids": ["550e8400-e29b-41d4-a716-446655440000"],
      "n_results": 5
    }
    ```

    ## Use Cases

    - Find relevant sections for memoir generation
    - Identify similar past projects
    - Extract reusable content for new proposals
    - Compare approaches across different memoires
    """
    print(f"🔍 Search request: '{search_request.query[:100]}...'")

    try:
        # Perform semantic search
        results = rag_service.search(
            query=search_request.query,
            memoire_ids=search_request.memoire_ids,
            n_results=search_request.n_results,
            similarity_threshold=search_request.similarity_threshold
        )

        # Convert to SearchResult schema
        search_results = [
            SearchResult(
                id=result['id'],
                content=result['content'],
                metadata=result['metadata'],
                similarity=result['similarity'],
                memoire_id=result.get('memoire_id', '')
            )
            for result in results
        ]

        return SearchResponse(
            query=search_request.query,
            results=search_results,
            count=len(search_results)
        )

    except Exception as e:
        print(f"❌ Search failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# === STARTUP EVENT ===

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    print("🚀 Memoir Generator API starting...")
    print(f"📍 Supabase URL: {Config.SUPABASE_URL}")
    print(f"🔑 Claude API Key configured: {'Yes' if Config.CLAUDE_API_KEY else 'No'}")
    print(f"🔑 OpenAI API Key configured: {'Yes' if Config.OPENAI_API_KEY else 'No'}")
    print("✅ Configuration validated successfully")

    # Test Supabase connection
    try:
        from services.supabase import get_supabase
        supabase = get_supabase()
        print("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Supabase client: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
