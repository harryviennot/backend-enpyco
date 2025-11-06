# Task 06: AI Content Generation Service

## Overview
Build the AI-powered content generation system that creates project-specific memoir sections using Claude API, with quality assessment and retry logic.

## Current State
- Content matching identifies gaps
- No AI generation capability
- Existing RAG service can retrieve context

## Goal
Intelligent content generation that:
- Generates project-specific sections (methodology, hypotheses, etc.)
- Uses company knowledge and past projects for context
- Produces high-quality, professional French text
- Assesses quality automatically
- Retries on low quality
- Tracks costs and performance

## Section Types to Generate

```python
class GenerationSectionType(str, Enum):
    METHODOLOGY = "methodology"                    # Main technical section (3000-4000 words)
    HYPOTHESES = "hypotheses"                      # Pricing assumptions (800-1500 words)
    SITE_ORGANIZATION = "site-organization"        # Site installation approach (1000-2000 words)
    PLANNING_NARRATIVE = "planning-narrative"      # Written planning description (500-1000 words)
    SAFETY_CUSTOMIZED = "safety-customized"        # Project-specific safety measures
    QUALITY_CUSTOMIZED = "quality-customized"      # Project-specific quality control
    ENVIRONMENTAL = "environmental"                # Environmental approach (RSE)
    SOCIAL_INSERTION = "social-insertion"          # Employment insertion hours
```

## Services to Implement

### 1. AI Generation Service
```python
# services/ai_generator.py

from anthropic import Anthropic
from typing import Dict, List, Optional
from enum import Enum

class AIContentGenerator:
    def __init__(self, claude_client, rag_service):
        self.claude = claude_client
        self.rag = rag_service
        self.templates = self._load_templates()

    async def generate_section(
        self,
        project_id: UUID,
        section_type: GenerationSectionType,
        requirement: RequiredSection,
        company_id: UUID
    ) -> GeneratedContent:
        """
        Main generation workflow:
        1. Gather context (RC, company blocks, past projects, RAG)
        2. Select appropriate AI model
        3. Build generation prompt
        4. Call AI API
        5. Assess quality
        6. Retry if quality low
        7. Save to database
        """

    async def _gather_context(
        self,
        project_id: UUID,
        section_type: GenerationSectionType,
        company_id: UUID
    ) -> GenerationContext:
        """
        Collect all context needed for generation:
        - Project info from RC analysis
        - Matched content blocks
        - Similar past projects
        - RAG-retrieved relevant content from old memoirs
        - Company standard approaches
        """

    def _select_model(
        self,
        section_type: GenerationSectionType
    ) -> str:
        """
        Choose AI model based on section type.

        Claude 3.5 Sonnet: Long-form, structured (methodology, organization)
        Claude 3 Haiku: Shorter, formulaic (hypotheses, planning narrative)
        """

    def _build_prompt(
        self,
        section_type: GenerationSectionType,
        context: GenerationContext,
        requirement: RequiredSection,
        template: Optional[str] = None
    ) -> str:
        """Build detailed generation prompt"""

    async def _generate_with_retry(
        self,
        prompt: str,
        model: str,
        max_retries: int = 2
    ) -> str:
        """Call AI with retry logic on failures"""

    async def _assess_quality(
        self,
        content: str,
        section_type: GenerationSectionType,
        requirement: RequiredSection
    ) -> QualityAssessment:
        """
        Assess generated content quality.

        Checks:
        - Length appropriate for section type
        - Structure (subsections, paragraphs)
        - Specificity (not too generic)
        - Language quality (French grammar)
        - Requirement coverage
        """

    async def _improve_content(
        self,
        content: str,
        quality_issues: List[str],
        section_type: GenerationSectionType
    ) -> str:
        """
        Attempt to improve low-quality content.

        Sends back to AI with specific improvement instructions.
        """
```

### 2. Prompt Builder Service
```python
# services/prompt_builder.py

class PromptBuilder:
    METHODOLOGY_PROMPT = """
You are writing the "ORGANISATION DU CHANTIER, MÉTHODOLOGIE DES TRAVAUX" section for a French construction technical memoir (mémoire technique).

CRITICAL CONTEXT:
This section is worth {points} points out of {total_points} total.
This is the most important section. Be comprehensive and detailed.

PROJECT INFORMATION:
{format_project_info(project)}

RC REQUIREMENTS:
{format_requirements(requirement)}

SPECIAL TECHNICAL REQUIREMENTS:
{format_special_requirements(project)}

COMPANY'S STANDARD METHODOLOGY:
{company_methodology}

SIMILAR PAST PROJECTS (for reference):
{format_past_projects(past_projects)}

EQUIPMENT AVAILABLE:
{format_equipment(equipment)}

REQUIREMENTS:
1. Write in formal French construction industry style
2. Structure with numbered subsections (2.1, 2.2, etc.)
3. Be specific: mention equipment names, techniques, timelines
4. For each work phase, describe:
   - How it will be executed
   - What equipment/materials will be used
   - Safety considerations
   - Quality control measures
   - Coordination with other trades
5. Reference company's experience and capabilities
6. Address all RC requirements explicitly
7. Emphasize techniques that score well
8. Include placeholder tags for images: {{{{IMAGE: description}}}}
9. Aim for 3000-4000 words

STRUCTURE:
2. ORGANISATION DU CHANTIER, MÉTHODOLOGIE DES TRAVAUX

2.1 Installation de chantier, études techniques et implantation
[Describe site installation, crane placement, base camp, surveying]

2.2 [First major work phase]
[Detail methodology]

2.3 [Second major work phase]
[Detail methodology]

... (continue for all work phases)

OUTPUT FORMAT:
Plain text with markdown-style headings.
Include {{{{IMAGE: description}}}} where images should be inserted.
Use bullet points sparingly (prefer paragraphs).

Begin writing now:
"""

    HYPOTHESES_PROMPT = """
You are writing the "HYPOTHÈSES DE CHIFFRAGE" (Pricing Assumptions) section for a French construction technical memoir.

PROJECT INFORMATION:
{format_project_info(project)}

COMPANY'S TYPICAL ASSUMPTIONS:
{company_standard_hypotheses}

DETECTED PROJECT SPECIFICS:
{format_project_specifics(project)}

TASK:
Generate a comprehensive list of pricing assumptions in French.

Categories to cover:
1. Site assumptions (access, utilities, existing conditions)
2. Scope assumptions (included/excluded, responsibilities)
3. Technical assumptions (foundations, concrete, crane, scaffolding)
4. Administrative assumptions (permits, studies, insurance)
5. Coordination assumptions (interfaces, common facilities)

FORMAT:
- Use bullet points (• not -)
- Be specific with measurements and quantities
- Reference project documents
- Formal French
- 50-70 bullet points

Example:
• SHOB totale = 7 238m²
• Il n'est pas prévu de frais d'occupation de voirie
• Une grue à tour sans ascenseur (hauteur 30m, flèche 40m) est prévue...

Begin writing now:
"""

    def build_methodology_prompt(self, context: Dict) -> str:
        """Build methodology generation prompt"""

    def build_hypotheses_prompt(self, context: Dict) -> str:
        """Build hypotheses generation prompt"""

    def build_site_org_prompt(self, context: Dict) -> str:
        """Build site organization prompt"""
```

### 3. Quality Assessment Service
```python
# services/quality_assessment.py

class QualityAssessor:
    def __init__(self, claude_client):
        self.claude = claude_client

    async def assess(
        self,
        content: str,
        section_type: GenerationSectionType,
        requirement: RequiredSection
    ) -> QualityAssessment:
        """
        Comprehensive quality assessment.

        Returns score 0.0-1.0 and list of issues.
        """

    def _check_length(
        self,
        content: str,
        section_type: GenerationSectionType
    ) -> Tuple[float, List[str]]:
        """Check if content is appropriate length"""

    def _check_structure(
        self,
        content: str,
        section_type: GenerationSectionType
    ) -> Tuple[float, List[str]]:
        """Check structure (subsections, paragraphs, formatting)"""

    async def _check_specificity(
        self,
        content: str
    ) -> Tuple[float, List[str]]:
        """
        Check specificity vs. generic content.

        Uses AI to assess:
        - Specific equipment names/models
        - Exact measurements
        - Concrete project details
        - Not vague descriptions
        """

    def _check_language(
        self,
        content: str
    ) -> Tuple[float, List[str]]:
        """Check French language quality"""

    async def _check_requirement_coverage(
        self,
        content: str,
        requirement: RequiredSection
    ) -> Tuple[float, List[str]]:
        """Check if all RC requirements addressed"""
```

### 4. RAG Integration for Context
```python
# Enhance existing services/rag.py

class RAGService:
    async def get_relevant_content(
        self,
        query: str,
        section_type: str,
        company_id: UUID,
        memoire_ids: Optional[List[UUID]] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Retrieve relevant content from past memoirs.

        For AI generation context.
        """
```

## API Endpoints

```python
# routers/generation.py

@router.post("/api/projects/{project_id}/generate")
async def start_generation(
    project_id: UUID,
    config: GenerationConfig,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> GenerationStartedResponse:
    """
    Start AI content generation (async).

    Config:
    - sections_to_generate: List of section types
    - temperature: AI temperature (0.0-1.0)
    - use_rag: Whether to use RAG for context

    Returns task ID for polling
    """

@router.get("/api/projects/{project_id}/generation/status")
async def get_generation_status(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> GenerationStatusResponse:
    """
    Get generation progress.

    Status:
    - pending: Queued
    - gathering_context: Loading context
    - generating: AI generating (section 3/8)
    - assessing: Quality checks
    - completed: Done
    - failed: Error
    """

@router.get("/api/projects/{project_id}/sections")
async def get_generated_sections(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> List[GeneratedSection]:
    """Get all generated sections for project"""

@router.get("/api/projects/{project_id}/sections/{section_id}")
async def get_section_detail(
    project_id: UUID,
    section_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> GeneratedSectionDetail:
    """Get section with quality metrics"""

@router.post("/api/projects/{project_id}/sections/{section_id}/regenerate")
async def regenerate_section(
    project_id: UUID,
    section_id: UUID,
    config: RegenerationConfig,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> GeneratedSection:
    """
    Regenerate section with different parameters.

    Config:
    - improvement_instructions: User feedback
    - temperature: Adjust creativity
    - use_different_examples: Use different past projects
    """

@router.patch("/api/projects/{project_id}/sections/{section_id}")
async def update_section_content(
    project_id: UUID,
    section_id: UUID,
    content: str,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> GeneratedSection:
    """Manually edit generated content"""

@router.post("/api/projects/{project_id}/sections/{section_id}/approve")
async def approve_section(
    project_id: UUID,
    section_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Mark section as reviewed and approved"""
```

## Pydantic Models

```python
# models/generation.py

class GenerationConfig(BaseModel):
    sections_to_generate: List[GenerationSectionType]
    temperature: float = 0.3
    use_rag: bool = True
    max_rag_chunks: int = 10

class GeneratedSection(BaseModel):
    id: UUID
    project_id: UUID
    section_type: GenerationSectionType
    title: str
    content: str
    quality_score: float
    generated_at: datetime
    model_used: str
    tokens_used: int
    cost_usd: float
    reviewed: bool
    approved: bool

class QualityAssessment(BaseModel):
    overall_score: float
    length_score: float
    structure_score: float
    specificity_score: float
    language_score: float
    coverage_score: float
    issues: List[str]
    suggestions: List[str]

class GenerationStatusResponse(BaseModel):
    status: str
    progress: int  # 0-100
    current_section: Optional[str]
    sections_completed: int
    sections_total: int
    estimated_time_remaining: Optional[int]  # seconds

class RegenerationConfig(BaseModel):
    improvement_instructions: Optional[str]
    temperature: Optional[float]
    use_different_examples: bool = False
```

## WebSocket Updates

```python
# websocket/generation.py

async def send_generation_progress(
    project_id: UUID,
    status: str,
    section: str,
    progress: int,
    quality_score: Optional[float] = None
):
    """Send real-time generation updates"""
```

## Implementation Steps

1. Create `services/prompt_builder.py` with prompt templates
2. Create `services/quality_assessment.py` for QA
3. Create `services/ai_generator.py` with core generation logic
4. Enhance `services/rag.py` for context retrieval
5. Create `routers/generation.py` with endpoints
6. Create Pydantic models in `models/generation.py`
7. Implement WebSocket updates
8. Add cost tracking to database
9. Test with real RC requirements
10. Optimize prompts for quality and cost

## Testing Checklist

- [ ] Can generate methodology section (3000+ words)
- [ ] Can generate hypotheses section (50-70 bullets)
- [ ] Generated content is in French
- [ ] Content is specific (not generic)
- [ ] Quality assessment catches low-quality output
- [ ] Retry logic improves poor generations
- [ ] RAG provides relevant context
- [ ] Cost tracking records token usage
- [ ] Regeneration with feedback works
- [ ] Manual editing saves correctly
- [ ] WebSocket updates in real-time
- [ ] Multi-tenant isolation enforced

## Performance Considerations

- Context gathering: 2-5 seconds
- AI generation per section:
  - Short sections (hypotheses): 10-20 seconds
  - Long sections (methodology): 30-60 seconds
- Quality assessment: 5-10 seconds
- Total for 8 sections: 3-5 minutes

## Cost Estimation

Claude API costs per memoir:
- Methodology: ~$0.30 (large section)
- Hypotheses: ~$0.10
- Other sections: ~$0.15 each
- **Total: ~$1.00-$1.50 per memoir**

With retries and quality checks: ~$2.00 per memoir

## Dependencies
- Task 01 (Database Schema)
- Task 02 (Authentication)
- Task 03 (Content Library)
- Task 04 (RC Analyzer)
- Task 05 (Content Matcher)
- Existing RAG service (services/rag.py)
- Claude API

## Estimated Effort
**6-7 days**

## Success Criteria
- Generates professional French content
- Quality score >0.8 for 90% of generations
- <5 minutes total generation time
- Cost <$2.50 per memoir
- User can regenerate unsatisfactory sections
- All RC requirements addressed in generated content

## Future Enhancements
- Fine-tuned model on company's writing style
- Multi-modal generation (include charts, diagrams)
- Automatic image selection for placeholders
- Learning from user edits to improve prompts
- Parallel generation of independent sections
