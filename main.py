from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import tempfile
import os

from config import Config
from services.supabase import SupabaseService
from services.parser import ParserService
from services.rag import RAGService
from services.generator import GeneratorService
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
    ProjectCreate,
    ProjectResponse,
    ProjectMetadata,
    RCUploadResponse,
    GenerateRequest,
    GenerateResponse,
    SectionResponse,
    SectionData,
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
parser_service = ParserService(chunk_size=500, chunk_overlap=50)
rag_service = RAGService()
generator_service = GeneratorService()

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


# === PROJECT ENDPOINTS ===

@app.post(
    "/projects",
    response_model=ProjectResponse,
    summary="Create a new project",
    tags=["Projects"],
    responses={
        200: {"description": "Project created successfully"},
        500: {"description": "Failed to create project"}
    }
)
async def create_project(project: ProjectCreate):
    """
    Create a new memoir generation project.

    A project represents a single memoir to be generated. After creating a project:
    1. Upload the RC (Règlement de Consultation) document
    2. Generate memoir sections using reference memoires
    3. Download the final Word document

    Args:
        project: Project creation request with name

    Returns:
        ProjectResponse with project details
    """
    print(f"🚀 Create project request: {project.name}")

    try:
        # Create project in database
        project_id = supabase_service.create_project(project.name)

        # Get the created project
        created_project = supabase_service.get_project(project_id)

        print(f"✅ Project created: {project_id}")

        return ProjectResponse(
            id=created_project['id'],
            name=created_project['name'],
            status=created_project['status'],
            created_at=created_project['created_at']
        )

    except Exception as e:
        print(f"❌ Project creation failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@app.get(
    "/projects",
    summary="List all projects",
    tags=["Projects"]
)
async def list_projects():
    """
    List all memoir generation projects.

    Returns:
        List of projects with their metadata
    """
    try:
        projects = supabase_service.list_projects()

        return {
            "projects": projects,
            "count": len(projects)
        }

    except Exception as e:
        print(f"❌ Failed to list projects: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@app.get(
    "/projects/{project_id}",
    response_model=ProjectMetadata,
    summary="Get project details",
    tags=["Projects"],
    responses={
        200: {"description": "Project details"},
        404: {"description": "Project not found"}
    }
)
async def get_project(project_id: str):
    """
    Get details of a specific project.

    Args:
        project_id: UUID of the project

    Returns:
        ProjectMetadata with project details
    """
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectMetadata(
        id=project['id'],
        name=project['name'],
        rc_storage_path=project.get('rc_storage_path'),
        rc_context=project.get('rc_context'),
        status=project['status'],
        created_at=project['created_at']
    )


@app.post(
    "/projects/{project_id}/upload-rc",
    response_model=RCUploadResponse,
    summary="Upload RC document for a project",
    tags=["Projects"],
    responses={
        200: {"description": "RC uploaded successfully"},
        404: {"description": "Project not found"},
        400: {"description": "Invalid file type"},
        500: {"description": "Upload failed"}
    }
)
async def upload_rc(
    project_id: str,
    file: UploadFile = File(...)
):
    """
    Upload the RC (Règlement de Consultation) document for a project.

    The RC will be:
    1. Stored in Supabase Storage
    2. Parsed to extract context (first 2000 characters)
    3. Saved to the project for use in generation

    **Supported formats**: PDF only
    **Max file size**: 50 MB

    Args:
        project_id: UUID of the project
        file: RC document file (PDF)

    Returns:
        RCUploadResponse with upload confirmation
    """
    print(f"📤 Upload RC for project: {project_id}")

    # Check if project exists
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file type (PDF only for RC)
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="RC must be a PDF file")

    # Read file content
    file_content = await file.read()
    file_size_mb = round(len(file_content) / (1024 * 1024), 2)

    print(f"   File: {file.filename} ({file_size_mb} MB)")

    # Validate file size
    is_valid_size, error_msg = validate_file_size(len(file_content))
    if not is_valid_size:
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        # Generate storage path
        storage_path = f"projects/{project_id}/rc.pdf"

        # Upload to Supabase Storage
        print(f"📦 Uploading to storage: {storage_path}")
        supabase_service.upload_file(
            bucket="memoires",
            path=storage_path,
            file_data=file_content
        )
        print(f"✅ Upload to storage successful")

        # Parse RC to extract context
        print(f"🔄 Parsing RC to extract context...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        try:
            parse_result = parser_service.parse_file(tmp_path)
            # Take first 2000 characters as context
            rc_context = parse_result.full_text[:2000]
            print(f"✅ RC parsed: {len(parse_result.full_text)} chars, context: {len(rc_context)} chars")

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # Update project with RC info
        supabase_service.update_project_rc(
            project_id=project_id,
            rc_storage_path=storage_path,
            rc_context=rc_context
        )

        print(f"✅ Project updated with RC info")

        return RCUploadResponse(
            project_id=project_id,
            rc_uploaded=True,
            rc_storage_path=storage_path
        )

    except Exception as e:
        print(f"❌ RC upload failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to upload RC: {str(e)}")


@app.post(
    "/projects/{project_id}/generate",
    response_model=GenerateResponse,
    summary="Generate memoir sections",
    tags=["Projects"],
    responses={
        200: {"description": "Memoir generated successfully"},
        404: {"description": "Project not found"},
        400: {"description": "RC not uploaded or invalid section types"},
        500: {"description": "Generation failed"}
    }
)
async def generate_memoire(
    project_id: str,
    request: GenerateRequest
):
    """
    Generate memoir sections using Claude API and RAG.

    This is the main generation endpoint. It will:
    1. Validate the project and RC exist
    2. For each requested section:
       - Search for relevant content using RAG
       - Generate section content using Claude API
       - Save the section to database
    3. Update project status to 'ready'

    ## Section Types

    Valid section types:
    - `presentation`: Company presentation (history, certifications, key figures)
    - `organisation`: Site organization (PIC, logistics, planning)
    - `methodologie`: Implementation methodology (phasing, techniques)
    - `moyens_humains`: Human resources (org chart, staffing)
    - `moyens_materiels`: Material resources (equipment list, capacities)
    - `planning`: Schedule (Gantt, deadlines)
    - `environnement`: Environmental approach (CSR, waste management)
    - `securite`: Safety and health (PPSPS, prevention measures)
    - `insertion`: Social integration (planned integration hours)

    ## Generation Time

    - Typical generation time: 30-60 seconds per section
    - 5 sections: ~3-5 minutes total

    ## Requirements

    - Project must exist
    - RC must be uploaded (provides context)
    - Specified memoires must be indexed (for RAG search)

    Args:
        project_id: UUID of the project
        request: Generation request with memoire_ids and section types

    Returns:
        GenerateResponse with list of generated sections
    """
    print(f"🚀 Generate request for project: {project_id}")
    print(f"   Memoire IDs: {request.memoire_ids}")
    print(f"   Sections: {request.sections}")

    # Validate project exists
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if RC is uploaded
    if not project.get('rc_storage_path'):
        raise HTTPException(
            status_code=400,
            detail="RC not uploaded. Please upload RC document first using POST /projects/{id}/upload-rc"
        )

    # Validate section types
    valid_section_types = generator_service.get_valid_section_types()
    invalid_sections = [s for s in request.sections if s not in valid_section_types]
    if invalid_sections:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid section types: {invalid_sections}. Valid types: {valid_section_types}"
        )

    # Validate memoires exist and are indexed
    for memoire_id in request.memoire_ids:
        memoire = supabase_service.get_memoire(memoire_id)
        if not memoire:
            raise HTTPException(status_code=404, detail=f"Memoire not found: {memoire_id}")
        if not memoire.get('indexed', False):
            raise HTTPException(
                status_code=400,
                detail=f"Memoire not indexed: {memoire_id}. Please index it first using POST /memoires/{memoire_id}/index"
            )

    try:
        # Update status to generating
        print(f"\n{'='*80}")
        print(f"🚀 STARTING MEMOIR GENERATION")
        print(f"{'='*80}")
        print(f"📋 Project: {project['name']} (ID: {project_id})")
        print(f"📚 Reference memoires: {len(request.memoire_ids)}")
        print(f"📄 Sections to generate: {len(request.sections)}")
        print(f"   Sections: {', '.join(request.sections)}")
        print(f"{'='*80}\n")

        supabase_service.update_project_status(project_id, 'generating')
        print(f"✅ Project status updated to 'generating'\n")

        # Get RC context
        rc_context = project.get('rc_context', '')
        print(f"📄 RC context loaded: {len(rc_context)} characters\n")

        # Generate each section
        generated_sections = []

        for i, section_type in enumerate(request.sections, 1):
            print(f"\n{'='*80}")
            print(f"📄 SECTION {i}/{len(request.sections)}: {section_type.upper()}")
            print(f"{'='*80}")

            try:
                # Build RAG search query
                search_query = f"{section_type} {generator_service.SECTION_DESCRIPTIONS.get(section_type, '')}"

                print(f"🔍 Step 1/3: Searching for relevant content...")
                print(f"   Query: '{search_query[:80]}...'")

                # Search for relevant chunks
                chunks = rag_service.search(
                    query=search_query,
                    memoire_ids=request.memoire_ids,
                    n_results=10,
                    similarity_threshold=0.5  # Only get relevant chunks
                )

                print(f"✅ Found {len(chunks)} relevant chunks from reference memoires")
                if chunks:
                    avg_similarity = sum(c.get('similarity', 0) for c in chunks) / len(chunks)
                    print(f"   Average similarity: {avg_similarity:.2f}")
                print(f"\n🤖 Step 2/3: Generating content with Claude AI...")

                # Generate section with Claude
                content = generator_service.generate_section(
                    section_type=section_type,
                    rc_context=rc_context,
                    reference_chunks=chunks
                )

                # Save section to database
                print(f"\n💾 Step 3/3: Saving section to database...")
                section_title = section_type.replace('_', ' ').title()
                section_id = supabase_service.create_section(
                    project_id=project_id,
                    section_type=section_type,
                    title=section_title,
                    content=content,
                    order_num=i
                )

                print(f"✅ Section '{section_type}' saved successfully!")
                print(f"   Section ID: {section_id}")
                print(f"   Title: {section_title}")
                print(f"   Content length: {len(content)} characters")

                generated_sections.append(
                    SectionResponse(
                        id=section_id,
                        section_type=section_type,
                        title=section_title
                    )
                )

            except Exception as section_error:
                print(f"\n❌ FAILED to generate section '{section_type}'")
                print(f"   Error: {str(section_error)}")
                import traceback
                traceback.print_exc()
                # Continue with other sections instead of failing completely
                # In production, you might want to fail fast instead

        # Update project status to ready
        print(f"\n{'='*80}")
        print(f"📊 GENERATION SUMMARY")
        print(f"{'='*80}")

        if len(generated_sections) == len(request.sections):
            supabase_service.update_project_status(project_id, 'ready')
            status_msg = "ready"
            message = f"Successfully generated all {len(generated_sections)} sections"
            print(f"✅ SUCCESS: All {len(generated_sections)} sections generated!")
        else:
            supabase_service.update_project_status(project_id, 'partial')
            status_msg = "partial"
            message = f"Generated {len(generated_sections)}/{len(request.sections)} sections (some failed)"
            print(f"⚠️  PARTIAL SUCCESS: Generated {len(generated_sections)}/{len(request.sections)} sections")
            failed_count = len(request.sections) - len(generated_sections)
            print(f"   {failed_count} section(s) failed to generate")

        print(f"\n📋 Generated sections:")
        for idx, section in enumerate(generated_sections, 1):
            print(f"   {idx}. {section.title} ({section.section_type})")

        print(f"\n✅ Project status updated to '{status_msg}'")
        print(f"{'='*80}\n")

        return GenerateResponse(
            project_id=project_id,
            status=status_msg,
            sections=generated_sections,
            message=message
        )

    except Exception as e:
        # Update status to failed
        supabase_service.update_project_status(project_id, 'failed')

        print(f"❌ Generation failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate memoir: {str(e)}")


@app.get(
    "/projects/{project_id}/sections",
    summary="Get project sections",
    tags=["Projects"],
    responses={
        200: {"description": "List of sections"},
        404: {"description": "Project not found"}
    }
)
async def get_project_sections(project_id: str):
    """
    Get all generated sections for a project.

    Args:
        project_id: UUID of the project

    Returns:
        List of sections with content
    """
    # Check if project exists
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        sections = supabase_service.get_sections(project_id)

        return {
            "project_id": project_id,
            "project_name": project['name'],
            "sections": sections,
            "count": len(sections)
        }

    except Exception as e:
        print(f"❌ Failed to get sections: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sections: {str(e)}")


@app.delete(
    "/projects/{project_id}",
    summary="Delete a project",
    tags=["Projects"],
    responses={
        200: {"description": "Project deleted successfully"},
        404: {"description": "Project not found"},
        500: {"description": "Deletion failed"}
    }
)
async def delete_project(project_id: str):
    """
    Delete a project and all its associated data.

    This will delete:
    - The project record from database
    - All generated sections (via CASCADE)
    - RC document from storage
    - Any generated Word documents from storage
    - All files in the project folder

    **Warning**: This operation cannot be undone!

    Args:
        project_id: UUID of the project to delete

    Returns:
        Success message with deletion details
    """
    print(f"🗑️ Delete request for project: {project_id}")

    # Check if project exists
    project = supabase_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get sections count before deletion
    sections = supabase_service.get_sections(project_id)
    sections_count = len(sections)

    print(f"📋 Project: {project['name']}")
    print(f"📄 Sections to delete: {sections_count}")
    print(f"📁 RC path: {project.get('rc_storage_path', 'None')}")

    try:
        # Delete project and all associated data
        success = supabase_service.delete_project(project_id)

        if success:
            print(f"✅ Successfully deleted project: {project_id}")
            return {
                "success": True,
                "message": f"Project '{project['name']}' and all associated data deleted successfully",
                "deleted_id": project_id,
                "deleted_sections": sections_count,
                "details": {
                    "project_name": project['name'],
                    "sections_deleted": sections_count,
                    "rc_deleted": bool(project.get('rc_storage_path')),
                    "storage_cleaned": True
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete project")

    except Exception as e:
        print(f"❌ Delete failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")


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
