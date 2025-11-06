# Task 04: RC Analyzer Service (PDF Parsing & AI Extraction)

## Overview
Build the intelligent RC (Règlement de Consultation) analyzer that extracts structured requirements from French construction tender documents using Claude API.

## Current State
- No RC analysis capability
- Projects are created manually without structured requirements

## Goal
Automated RC analysis that:
- Extracts text from PDF documents
- Identifies required memoir sections
- Extracts scoring criteria and point values
- Detects special technical requirements
- Provides structured output for content matching

## Components to Implement

### 1. PDF Text Extraction Service
```python
# services/pdf_parser.py

import PyPDF2
import pdfplumber
from typing import Dict, List

class PDFParser:
    def extract_text(self, pdf_path: str) -> str:
        """Extract all text from PDF"""

    def extract_with_layout(self, pdf_path: str) -> List[Dict]:
        """Extract text preserving layout information"""

    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """Extract tables from PDF (for scoring grids)"""

    def find_scoring_section(self, text: str) -> str:
        """
        Locate scoring/requirements section.
        Common headers:
        - "Critères de jugement"
        - "Notation"
        - "Grille d'évaluation"
        - "Analyse des offres"
        """
```

### 2. RC Analyzer Service
```python
# services/rc_analyzer.py

from anthropic import Anthropic
from typing import Dict, List, Optional

class RCAnalyzer:
    def __init__(self, claude_api_key: str):
        self.client = Anthropic(api_key=claude_api_key)

    async def analyze_rc(
        self,
        rc_pdf_path: str,
        project_id: UUID
    ) -> RCAnalysis:
        """
        Main analysis workflow:
        1. Extract text from PDF
        2. Identify scoring section
        3. Use Claude to extract structured requirements
        4. Validate and structure output
        5. Save to database
        """

    def _build_analysis_prompt(
        self,
        full_text: str,
        scoring_section: str
    ) -> str:
        """
        Build detailed prompt for Claude.

        Instructs Claude to:
        - Extract project information
        - Identify required memoir sections
        - Extract point values for each section
        - Identify special technical requirements
        - Determine format constraints
        """

    async def _call_claude_api(
        self,
        prompt: str,
        context: Dict
    ) -> Dict:
        """Call Claude API with retry logic"""

    def _validate_analysis(self, raw_analysis: Dict) -> RCAnalysis:
        """Validate and structure the analysis output"""

    def _extract_keywords(self, requirements: List[str]) -> List[str]:
        """Extract keywords from requirements for matching"""
```

### 3. Claude API Integration
```python
# services/claude_client.py

class ClaudeClient:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest model

    async def analyze_document(
        self,
        prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.3
    ) -> str:
        """
        Call Claude API for document analysis.

        Uses:
        - Low temperature (0.3) for consistent output
        - Large context window (200K tokens)
        - JSON response format
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        return response.content[0].text

    async def structured_extraction(
        self,
        text: str,
        schema: Dict
    ) -> Dict:
        """Extract structured data matching a schema"""
```

## Prompt Templates

### RC Analysis Prompt
```python
RC_ANALYSIS_PROMPT = """
You are analyzing a French construction tender regulation document (Règlement de Consultation).

TASK: Extract structured information about technical memoir requirements.

SCORING SECTION (most important):
{scoring_section}

FULL DOCUMENT:
{full_text}

Extract the following information in JSON format:

1. PROJECT INFORMATION:
   - name: Project name
   - client: Client organization
   - location: Project location
   - deadline: Submission deadline (ISO 8601 format)
   - lot: Lot/trade designation

2. REQUIRED SECTIONS:
   For each required section in the memoir:
   - id: Short identifier (e.g., "presentation", "methodology")
   - title: Section title in French
   - description: What should be included
   - points: Point value if specified
   - requirements: List of specific requirements

3. SPECIAL REQUIREMENTS:
   Any special technical requirements, materials, or constraints mentioned:
   - Specific materials (e.g., "Béton bas carbone CEMEX VERTUA")
   - Specific techniques (e.g., "Façades préfabriquées type Duomurs")
   - Timeline constraints
   - Equipment requirements

4. FORMAT:
   - type: "free" or "imposed"
   - template: If imposed template, mention details
   - page_limit: Maximum pages if specified
   - language: Document language

5. SCORING CRITERIA:
   - total: Total points available
   - breakdown: Points per major category
   - emphasis: Which sections get most points

Return ONLY valid JSON. Be precise with point values and requirements.
Pay special attention to:
- Exact point values for each section
- Mandatory vs. optional elements
- Technical specifications mentioned
- Past project requirements

{format_instructions}
"""
```

## API Endpoints

```python
# routers/rc_analysis.py

@router.post("/api/projects/{project_id}/analyze-rc")
async def analyze_rc(
    project_id: UUID,
    rc_file: UploadFile,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> AnalysisStartedResponse:
    """
    Start RC analysis (async operation).

    Steps:
    1. Upload RC PDF to storage
    2. Start async analysis task
    3. Return task ID for status polling
    4. Send WebSocket updates during analysis
    """

@router.get("/api/projects/{project_id}/analysis")
async def get_analysis_results(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> RCAnalysisResponse:
    """Get RC analysis results once completed"""

@router.get("/api/projects/{project_id}/analysis/status")
async def get_analysis_status(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> AnalysisStatusResponse:
    """
    Get analysis progress status.

    Status values:
    - pending: Queued
    - extracting_text: Extracting from PDF
    - analyzing: Claude API processing
    - completed: Analysis done
    - failed: Error occurred
    """

@router.post("/api/projects/{project_id}/analysis/retry")
async def retry_analysis(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> AnalysisStartedResponse:
    """Retry failed analysis"""
```

## Pydantic Models

```python
# models/rc_analysis.py

class ProjectInfo(BaseModel):
    name: str
    client: str
    location: str
    deadline: Optional[datetime]
    lot: Optional[str]

class RequiredSection(BaseModel):
    id: str
    title: str
    description: str
    points: Optional[int]
    requirements: List[str]
    keywords: List[str]

class FormatInfo(BaseModel):
    type: str  # "free" or "imposed"
    template_details: Optional[str]
    page_limit: Optional[int]
    language: str = "fr"

class ScoringCriteria(BaseModel):
    total: int
    breakdown: Dict[str, int]
    emphasis: List[str]

class RCAnalysis(BaseModel):
    id: UUID
    project_id: UUID
    rc_file_url: str
    project_info: ProjectInfo
    required_sections: List[RequiredSection]
    special_requirements: List[str]
    format: FormatInfo
    scoring_criteria: ScoringCriteria
    confidence_score: float
    analyzed_at: datetime
    raw_text_preview: Optional[str]

class AnalysisStatusResponse(BaseModel):
    status: str  # pending, extracting_text, analyzing, completed, failed
    progress: int  # 0-100
    message: str
    error: Optional[str] = None
```

## WebSocket Updates

```python
# websocket/analysis.py

class AnalysisWebSocket:
    async def send_progress(
        self,
        project_id: UUID,
        status: str,
        progress: int,
        message: str
    ):
        """Send progress update via WebSocket"""
        await self.send_json({
            "type": "analysis_progress",
            "project_id": str(project_id),
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })
```

## Error Handling

```python
# exceptions.py

class RCAnalysisError(Exception):
    """Base exception for RC analysis"""

class PDFExtractionError(RCAnalysisError):
    """Failed to extract text from PDF"""

class ScoringNotFoundError(RCAnalysisError):
    """Could not locate scoring criteria"""

class ClaudeAPIError(RCAnalysisError):
    """Claude API call failed"""

class InvalidAnalysisOutput(RCAnalysisError):
    """AI returned invalid/incomplete analysis"""
```

## Implementation Steps

1. Install dependencies: `PyPDF2`, `pdfplumber`, `anthropic`
2. Create `services/pdf_parser.py` for PDF extraction
3. Create `services/claude_client.py` for API wrapper
4. Create `services/rc_analyzer.py` for analysis logic
5. Create `routers/rc_analysis.py` with endpoints
6. Create Pydantic models in `models/rc_analysis.py`
7. Set up WebSocket for progress updates
8. Add error handling and retry logic
9. Test with real RC documents (5+ examples)
10. Optimize prompt for better extraction accuracy

## Testing Checklist

- [ ] Can extract text from various PDF formats
- [ ] Can locate scoring sections in RCs
- [ ] Claude API integration works
- [ ] Analysis returns valid JSON structure
- [ ] Required sections are extracted correctly
- [ ] Point values are extracted accurately
- [ ] Special requirements are identified
- [ ] WebSocket progress updates work
- [ ] Error handling for malformed PDFs
- [ ] Error handling for Claude API failures
- [ ] Retry logic works for failed analyses
- [ ] Multi-tenant isolation (company_id)
- [ ] Analysis results saved to database

## Test Data

Collect 5-10 real RC documents from:
- Different clients (CDC Habitat, SNCF, Toulouse Métropole, etc.)
- Different project types (logements, infrastructure, renovation)
- Different formats (free vs. imposed template)

## Performance Considerations

- PDF extraction: 5-10 seconds for 50-page doc
- Claude API call: 10-30 seconds for full analysis
- Total time: 15-40 seconds per RC

## Cost Estimation

Claude API costs:
- Input: ~20,000 tokens per RC (at $3/M tokens = $0.06)
- Output: ~2,000 tokens (at $15/M tokens = $0.03)
- **Total: ~$0.10 per RC analysis**

## Dependencies
- Task 01 (Database Schema)
- Task 02 (Authentication)
- Claude API key
- `PyPDF2` and `pdfplumber`
- `anthropic` SDK

## Estimated Effort
**5-6 days**

## Success Criteria
- Accurate extraction of required sections (>90%)
- Accurate extraction of point values (>95%)
- Handles variety of RC formats
- Robust error handling
- Real-time progress updates
- <1 minute total analysis time
- Structured output ready for content matching

## Notes
- Claude 3.5 Sonnet has 200K context window (can handle full RCs)
- Use low temperature (0.3) for consistent output
- Implement caching for repeated analyses (same RC)
- Consider OCR for scanned PDFs (pytesseract)
- Log all Claude API calls for cost tracking
