# Task 03: Content Library API & File Management

## Overview
Build the content library system that allows companies to store, organize, and retrieve reusable content blocks (company profiles, CVs, equipment, procedures, etc.).

## Current State
- No content library system
- Basic file storage exists (memoires uploaded to Supabase)

## Goal
Full-featured content library with:
- CRUD operations for content blocks
- File upload to S3/Supabase Storage
- Search and filtering
- Tagging system
- Version control
- Multi-type content support

## Content Block Types

```python
class ContentBlockType(str, Enum):
    COMPANY_PROFILE = "company-profile"        # Company description, certifications
    PERSON_CV = "person-cv"                    # Employee CVs with photos
    EQUIPMENT = "equipment"                     # Equipment specs and photos
    PROCEDURE = "procedure"                     # Standard procedures (safety, quality)
    CERTIFICATION = "certification"             # Company certifications
    METHODOLOGY_TEMPLATE = "methodology-template"  # Reusable methodology sections
    PAST_PROJECT = "past-project-reference"    # Past project for references
```

## API Endpoints to Implement

### 1. Content Block CRUD
```python
# routers/content_library.py

@router.post("/api/content-blocks")
async def create_content_block(
    block: ContentBlockCreate,
    files: Optional[List[UploadFile]] = File(None),
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.CONTENT_WRITE))
) -> ContentBlock:
    """
    Create new content block with optional file attachments.

    Supports multiple content types:
    - company-profile: Company description, history, certifications
    - person-cv: CV with metadata (name, role, experience, expertise)
    - equipment: Equipment specs, photos, datasheets
    - procedure: Safety/quality procedures
    - etc.
    """
    # Upload files to S3 if provided
    # Create content block in database
    # Link files to block
    # Return created block

@router.get("/api/content-blocks")
async def list_content_blocks(
    type: Optional[ContentBlockType] = None,
    tags: Optional[str] = None,  # Comma-separated
    search: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 50,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> ContentBlockListResponse:
    """
    List content blocks with filtering and search.

    Filters:
    - type: Filter by content block type
    - tags: Filter by tags (OR logic)
    - search: Full-text search on title and content
    - is_active: Show only active blocks
    """

@router.get("/api/content-blocks/{block_id}")
async def get_content_block(
    block_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> ContentBlockDetail:
    """Get content block with all files and metadata"""

@router.patch("/api/content-blocks/{block_id}")
async def update_content_block(
    block_id: UUID,
    updates: ContentBlockUpdate,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.CONTENT_WRITE))
) -> ContentBlock:
    """
    Update content block.
    Increments version number for audit trail.
    """

@router.delete("/api/content-blocks/{block_id}")
async def delete_content_block(
    block_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.CONTENT_DELETE))
):
    """Soft delete: sets is_active = false"""
```

### 2. File Upload & Management
```python
# routers/files.py

@router.post("/api/files/upload")
async def upload_file(
    file: UploadFile,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> FileUploadResponse:
    """
    Upload file to S3/Supabase Storage.

    Returns:
    - file_id: UUID
    - storage_url: S3 URL
    - filename: Original filename
    - size_bytes: File size
    """

@router.get("/api/files/{file_id}")
async def get_file_metadata(
    file_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> FileMetadata:
    """Get file metadata"""

@router.get("/api/files/{file_id}/download")
async def download_file(
    file_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> StreamingResponse:
    """Download file from storage"""

@router.delete("/api/files/{file_id}")
async def delete_file(
    file_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.CONTENT_DELETE))
):
    """Delete file from storage and database"""
```

### 3. Past Projects Management
```python
# routers/past_projects.py

@router.post("/api/past-projects")
async def create_past_project(
    project: PastProjectCreate,
    photos: Optional[List[UploadFile]] = File(None),
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.CONTENT_WRITE))
) -> PastProject:
    """Create past project reference"""

@router.get("/api/past-projects")
async def list_past_projects(
    project_type: Optional[str] = None,
    year: Optional[int] = None,
    is_referenceable: bool = True,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> List[PastProject]:
    """List past projects with filtering"""

@router.get("/api/past-projects/similar")
async def find_similar_projects(
    project_type: str,
    techniques: List[str],
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> List[PastProject]:
    """
    Find past projects similar to requirements.

    Matches on:
    - project_type (exact match)
    - techniques_used (array overlap)

    Returns top 5 most similar projects.
    """
```

### 4. Search Functionality
```python
# services/content_search.py

class ContentSearchService:
    def __init__(self, db):
        self.db = db

    async def search_blocks(
        self,
        query: str,
        company_id: UUID,
        filters: Optional[dict] = None
    ) -> List[ContentBlock]:
        """
        Full-text search across content blocks.

        Uses PostgreSQL full-text search:
        - Searches title and content
        - Ranks results by relevance
        - Applies filters (type, tags, is_active)
        """
        # Build search query with ts_vector
        # Apply filters
        # Order by rank
        # Return results
```

## Services to Implement

### 1. File Storage Service
```python
# services/storage.py

class StorageService:
    def __init__(self, supabase_client):
        self.client = supabase_client
        self.bucket_name = "memoire-files"

    async def upload_file(
        self,
        file: UploadFile,
        company_id: UUID,
        folder: str = "general"
    ) -> FileUploadResult:
        """
        Upload file to Supabase Storage.

        Path structure: {company_id}/{folder}/{uuid}_{filename}
        """
        # Generate unique filename
        # Upload to Supabase Storage
        # Return storage URL and metadata

    async def download_file(self, storage_path: str) -> bytes:
        """Download file from storage"""

    async def delete_file(self, storage_path: str):
        """Delete file from storage"""

    async def get_signed_url(
        self,
        storage_path: str,
        expires_in: int = 3600
    ) -> str:
        """Get temporary signed URL for file access"""
```

### 2. Content Block Service
```python
# services/content_blocks.py

class ContentBlockService:
    def __init__(self, db, storage_service):
        self.db = db
        self.storage = storage_service

    async def create_block(
        self,
        block_data: ContentBlockCreate,
        files: Optional[List[UploadFile]],
        company_id: UUID,
        user_id: UUID
    ) -> ContentBlock:
        """Create content block with file uploads"""
        # Validate block type
        # Upload files if provided
        # Create block in database
        # Link files to block
        # Return created block

    async def update_block(
        self,
        block_id: UUID,
        updates: ContentBlockUpdate,
        company_id: UUID
    ) -> ContentBlock:
        """Update block with version increment"""
        # Verify ownership (company_id)
        # Update fields
        # Increment version
        # Return updated block

    async def search_blocks(
        self,
        query: str,
        company_id: UUID,
        filters: dict
    ) -> List[ContentBlock]:
        """Search blocks with full-text search"""

    async def get_blocks_by_tags(
        self,
        tags: List[str],
        company_id: UUID
    ) -> List[ContentBlock]:
        """Get blocks matching any of the tags"""
```

## Pydantic Models

```python
# models/content_library.py

class ContentBlockCreate(BaseModel):
    type: ContentBlockType
    title: str = Field(min_length=1, max_length=255)
    content: Optional[str] = None
    metadata: Optional[dict] = {}
    tags: List[str] = []

class ContentBlockUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[dict] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None

class ContentBlock(BaseModel):
    id: UUID
    company_id: UUID
    type: ContentBlockType
    title: str
    content: Optional[str]
    metadata: dict
    tags: List[str]
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: UUID
    files: List[FileMetadata] = []

class FileMetadata(BaseModel):
    id: UUID
    filename: str
    file_type: str
    storage_url: str
    size_bytes: int
    uploaded_at: datetime

class PastProjectCreate(BaseModel):
    name: str
    client: str
    year: int
    project_type: str
    description: str
    techniques_used: List[str] = []
    success_factors: List[str] = []
    is_referenceable: bool = True
    metadata: Optional[dict] = {}

class PastProject(BaseModel):
    id: UUID
    company_id: UUID
    name: str
    client: str
    year: int
    project_type: str
    description: str
    techniques_used: List[str]
    success_factors: List[str]
    photos: List[str]
    is_referenceable: bool
    metadata: dict
    created_at: datetime
```

## Database Queries

```python
# Example queries for content_blocks table

# Full-text search
"""
SELECT *
FROM content_blocks
WHERE company_id = $1
  AND is_active = true
  AND (
    to_tsvector('french', title || ' ' || COALESCE(content, ''))
    @@ plainto_tsquery('french', $2)
  )
ORDER BY ts_rank(
  to_tsvector('french', title || ' ' || COALESCE(content, '')),
  plainto_tsquery('french', $2)
) DESC
LIMIT $3;
"""

# Tag filtering with array contains
"""
SELECT *
FROM content_blocks
WHERE company_id = $1
  AND tags && $2  -- Array overlap operator
  AND is_active = true
ORDER BY created_at DESC;
"""

# Get blocks by type
"""
SELECT *
FROM content_blocks
WHERE company_id = $1
  AND type = $2
  AND is_active = true;
"""
```

## Implementation Steps

1. Create `services/storage.py` for Supabase Storage integration
2. Create `services/content_blocks.py` for business logic
3. Create `routers/content_library.py` with CRUD endpoints
4. Create `routers/files.py` for file management
5. Create `routers/past_projects.py` for project references
6. Create Pydantic models in `models/content_library.py`
7. Add full-text search indexes to database
8. Test file upload/download flow
9. Test multi-tenant isolation
10. Add API documentation with examples

## Testing Checklist

- [ ] Can create content block without files
- [ ] Can create content block with multiple files
- [ ] File upload to Supabase Storage works
- [ ] Can list content blocks with filters (type, tags)
- [ ] Full-text search returns relevant results
- [ ] Can update content block (version increments)
- [ ] Can soft-delete content block (is_active = false)
- [ ] Multi-tenant isolation: users only see their company's blocks
- [ ] File download generates signed URLs correctly
- [ ] Can delete files from storage
- [ ] Past projects can be searched by type and techniques
- [ ] Similar project matching returns relevant results
- [ ] Tag filtering works with array operations

## Dependencies
- Task 01 (Database Schema)
- Task 02 (Authentication)
- Supabase Storage configured
- `python-multipart` for file uploads

## Estimated Effort
**4-5 days**

## Success Criteria
- Full CRUD operations for content blocks
- File upload/download working with Supabase Storage
- Search and filtering functional
- Multi-tenant data isolation enforced
- Version control for content blocks
- Comprehensive API documentation
- Test coverage >80%

## Notes
- Use Supabase Storage (already configured) instead of AWS S3
- Implement file size limits (e.g., 10MB per file)
- Support common file types: PDF, DOCX, JPG, PNG
- Consider image optimization for photos
- Add file virus scanning in future (ClamAV)
