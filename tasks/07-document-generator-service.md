# Task 07: Word Document Generator Service

## Overview
Build the document assembly system that creates professional Word documents (.docx) from generated sections and content blocks, with proper formatting, images, and company branding.

## Current State
- Sections generated as plain text
- No document assembly capability
- Basic Word export exists (download endpoint in main.py)

## Goal
Professional document generation with:
- Word document assembly with python-docx
- Company branding and styling
- Cover page, table of contents, headers/footers
- Image embedding and optimization
- Table generation
- Quality assurance checks
- Export to S3 storage

## Components to Implement

### 1. Word Document Builder
```python
# services/word_generator.py

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from typing import List, Dict, Optional
import io

class WordDocumentGenerator:
    def __init__(self, storage_service, template_service):
        self.storage = storage_service
        self.templates = template_service

    async def generate_memoir(
        self,
        project_id: UUID,
        company_id: UUID,
        style_config: Optional[StyleConfig] = None
    ) -> io.BytesIO:
        """
        Main document generation workflow:
        1. Load sections from database
        2. Load company info and branding
        3. Create Word document from template
        4. Add cover page
        5. Add table of contents
        6. Add each section with formatting
        7. Add annexes
        8. Add headers/footers, page numbers
        9. Quality check
        10. Save to buffer
        11. Upload to S3
        """

    def _create_document(
        self,
        template_name: Optional[str] = None
    ) -> Document:
        """Create document from template or default"""

    def _setup_styles(self, doc: Document, company: Company):
        """Configure document styles (headings, body, captions)"""

    def _add_cover_page(
        self,
        doc: Document,
        project: Project,
        company: Company
    ):
        """Create professional cover page"""

    def _add_table_of_contents(
        self,
        doc: Document,
        sections: List[Section]
    ):
        """Generate table of contents"""

    def _add_section(
        self,
        doc: Document,
        section: Section,
        style: StyleConfig
    ):
        """Add section with proper formatting"""

    def _parse_content(self, content: str) -> List[ContentPart]:
        """
        Parse content text into structured parts:
        - Paragraphs
        - Subsection headers
        - Bullet points
        - Image placeholders
        - Tables
        """

    async def _add_image(
        self,
        doc: Document,
        image_data: Dict,
        caption: Optional[str],
        style: StyleConfig
    ):
        """Add image with sizing and caption"""

    def _add_table(
        self,
        doc: Document,
        table_data: Dict,
        style: StyleConfig
    ):
        """Add formatted table"""

    def _add_headers_footers(
        self,
        doc: Document,
        project: Project,
        company: Company
    ):
        """Add headers and footers with page numbers"""

    def _finalize_formatting(self, doc: Document):
        """Final formatting: widow control, keep-with-next, etc."""
```

### 2. Image Processing Service
```python
# services/image_processor.py

from PIL import Image
import io

class ImageProcessor:
    def __init__(self, storage_service):
        self.storage = storage_service

    async def download_and_optimize(
        self,
        image_url: str,
        max_width: int = 1200,
        max_height: int = 900
    ) -> io.BytesIO:
        """
        Download image and optimize for document:
        - Resize if too large
        - Compress if needed
        - Convert to RGB if necessary
        """

    def resize_image(
        self,
        image: Image.Image,
        max_width: int,
        max_height: int
    ) -> Image.Image:
        """Resize maintaining aspect ratio"""

    def calculate_display_size(
        self,
        image: Image.Image,
        max_width_inches: float = 6.5
    ) -> Inches:
        """Calculate appropriate display size in Word"""
```

### 3. Content Parser
```python
# services/content_parser.py

import re
from typing import List, Dict

class ContentParser:
    def parse(self, content: str) -> List[ContentPart]:
        """
        Parse generated content text into structured parts.

        Recognizes:
        - Subsection headers: "2.1", "2.2.1", etc.
        - Paragraphs: Regular text blocks
        - Bullet points: Lines starting with • or -
        - Image placeholders: {{IMAGE: description}}
        - Table markers: {{TABLE: ...}}
        """

    def _extract_subsections(self, text: str) -> List[str]:
        """Extract subsection headers"""

    def _extract_image_placeholders(self, text: str) -> List[Dict]:
        """Find image placeholders and extract metadata"""

    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs"""

    def _identify_bullets(self, text: str) -> List[str]:
        """Identify bullet point lists"""
```

### 4. Document Template Service
```python
# services/document_templates.py

class DocumentTemplateService:
    def __init__(self, storage_service):
        self.storage = storage_service

    def get_template(
        self,
        company_id: UUID,
        template_name: str = "default"
    ) -> Optional[str]:
        """
        Load Word template file.

        Templates define:
        - Page layout (margins, orientation)
        - Style definitions
        - Company branding elements
        """

    def create_default_template(self) -> Document:
        """Create default template with standard styles"""

    async def upload_custom_template(
        self,
        company_id: UUID,
        template_file: UploadFile
    ):
        """Allow company to upload custom template"""
```

### 5. Document QA Service
```python
# services/document_qa.py

from docx import Document
import io

class DocumentQA:
    async def validate_document(
        self,
        doc_bytes: bytes
    ) -> QAReport:
        """
        Quality assurance checks:
        1. All required sections present
        2. Images loaded correctly
        3. Table of contents exists
        4. Page count reasonable (20-80 pages)
        5. No excessive empty paragraphs
        6. Headers/footers present
        """

    def _check_sections(self, doc: Document) -> List[str]:
        """Verify all required sections included"""

    def _check_images(self, doc: Document) -> int:
        """Count and verify images"""

    def _estimate_page_count(self, doc: Document) -> int:
        """Estimate page count"""
```

## API Endpoints

```python
# routers/document_generation.py

@router.post("/api/projects/{project_id}/document/generate")
async def generate_document(
    project_id: UUID,
    config: DocumentConfig,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> DocumentGenerationResponse:
    """
    Start document generation (async).

    Config:
    - include_annexes: bool
    - style_template: str
    - image_quality: "low" | "medium" | "high"

    Returns task ID and starts background job
    """

@router.get("/api/projects/{project_id}/document/status")
async def get_document_status(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> DocumentStatusResponse:
    """
    Get document generation status.

    Status:
    - pending: Queued
    - preparing: Loading sections
    - building: Creating Word doc
    - processing_images: Downloading/optimizing images
    - finalizing: QA and formatting
    - completed: Ready for download
    - failed: Error
    """

@router.get("/api/projects/{project_id}/document/download")
async def download_document(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> StreamingResponse:
    """
    Download generated Word document.

    Returns .docx file with proper headers
    """

@router.get("/api/projects/{project_id}/document/preview")
async def get_document_preview(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> DocumentPreview:
    """
    Get document preview/metadata.

    Returns:
    - Page count estimate
    - Section list
    - Image count
    - Word count
    - File size estimate
    """

@router.post("/api/templates/upload")
async def upload_template(
    template: UploadFile,
    template_name: str,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.COMPANY_SETTINGS))
):
    """Upload custom Word template"""

@router.get("/api/templates")
async def list_templates(
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> List[TemplateInfo]:
    """List available templates"""
```

## Pydantic Models

```python
# models/document_generation.py

class DocumentConfig(BaseModel):
    include_annexes: bool = True
    style_template: str = "default"
    image_quality: str = "medium"  # low, medium, high
    add_placeholder_images: bool = True

class DocumentStatusResponse(BaseModel):
    status: str
    progress: int  # 0-100
    message: str
    current_step: Optional[str]
    document_url: Optional[str]
    error: Optional[str]

class DocumentPreview(BaseModel):
    estimated_pages: int
    sections: List[str]
    image_count: int
    word_count: int
    estimated_size_mb: float

class QAReport(BaseModel):
    passed: bool
    issues: List[str]
    warnings: List[str]
    stats: Dict[str, Any]

class StyleConfig(BaseModel):
    template_name: str = "default"
    heading_color: str = "#003366"  # RGB hex
    font_family: str = "Arial"
    body_font_size: int = 11
    heading1_size: int = 16
    heading2_size: int = 14

class ContentPart(BaseModel):
    type: str  # paragraph, subsection, bullet, image, table
    text: Optional[str]
    data: Optional[Dict]
    metadata: Optional[Dict]
```

## Styling Configuration

```python
# Default style configuration

DEFAULT_STYLES = {
    "heading1": {
        "font": "Arial",
        "size": 16,
        "bold": True,
        "color": "#003366",
        "space_before": 24,
        "space_after": 12
    },
    "heading2": {
        "font": "Arial",
        "size": 14,
        "bold": True,
        "color": "#003366",
        "space_before": 18,
        "space_after": 6
    },
    "body": {
        "font": "Arial",
        "size": 11,
        "line_spacing": 1.15,
        "alignment": "justify",
        "space_after": 6
    },
    "caption": {
        "font": "Arial",
        "size": 9,
        "italic": True,
        "color": "#595959",
        "alignment": "center"
    }
}
```

## Implementation Steps

1. Install `python-docx` and `Pillow`
2. Create `services/content_parser.py` for text parsing
3. Create `services/image_processor.py` for image handling
4. Create `services/document_templates.py` for template management
5. Create `services/word_generator.py` with main generation logic
6. Create `services/document_qa.py` for quality checks
7. Create `routers/document_generation.py` with endpoints
8. Create Pydantic models in `models/document_generation.py`
9. Test with various content structures
10. Optimize image processing performance

## Testing Checklist

- [ ] Can create basic Word document
- [ ] Cover page has company logo and project info
- [ ] Table of contents generated correctly
- [ ] Sections formatted with proper styles
- [ ] Subsection headers recognized and styled
- [ ] Paragraphs have correct formatting
- [ ] Bullet points rendered correctly
- [ ] Images downloaded and embedded
- [ ] Images have appropriate size
- [ ] Image captions displayed
- [ ] Tables formatted correctly
- [ ] Headers and footers added
- [ ] Page numbers work
- [ ] QA report catches issues
- [ ] Document downloads successfully
- [ ] File is valid .docx format
- [ ] Multi-tenant isolation (company_id)

## Document Structure

```
1. Cover Page
   - Company logo
   - "MÉMOIRE TECHNIQUE" title
   - Project name
   - Client, location, lot, date

2. Table of Contents
   - Section titles with page numbers

3. Sections (numbered)
   1. Présentation de l'entreprise
   2. Méthodologie des travaux
   3. Moyens humains
   4. Moyens matériels
   5. Planning prévisionnel
   6. Démarche environnementale
   7. Sécurité et santé
   8. Insertion sociale

4. Annexes (if applicable)
   - CVs
   - Certifications
   - Equipment datasheets
   - Planning Gantt

Headers: Company name - Project name
Footers: Page numbers centered
```

## Performance Considerations

- Content parsing: <1 second
- Image processing: 2-5 seconds per image
- Document assembly: 5-10 seconds
- Total time for 40-page memoir: 30-60 seconds

## Dependencies
- Task 01 (Database Schema)
- Task 02 (Authentication)
- Task 03 (Content Library for images)
- Task 06 (AI Generation for content)
- `python-docx`
- `Pillow` (PIL)

## Estimated Effort
**5-6 days**

## Success Criteria
- Generates professional Word documents
- All sections formatted correctly
- Images embedded and sized properly
- Company branding applied
- QA checks catch formatting issues
- <1 minute generation time
- Document opens in Microsoft Word without errors

## Future Enhancements
- PDF export with preserved formatting
- Automatic diagram generation (org charts, planning)
- Multi-language support (bilingual memoirs)
- Version comparison for regenerated sections
- Collaborative commenting
- Custom styling per section
