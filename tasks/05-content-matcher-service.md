# Task 05: Content Matcher Service (Smart Requirement Matching)

## Overview
Build intelligent content matching system that maps RC requirements to company content blocks using rule-based matching and AI semantic analysis.

## Current State
- RC analysis provides structured requirements
- Content library has reusable blocks
- No connection between requirements and content

## Goal
Automatic content matching that:
- Maps requirements to relevant content blocks
- Uses rule-based matching for standard sections
- Uses AI semantic matching for complex requirements
- Provides confidence scores
- Identifies gaps (needs generation or upload)
- Allows customization via chat interface

## Matching Strategies

### 1. Rule-Based Matching (Fast, Deterministic)
For standard, predictable sections:
- Company presentation → company-profile blocks
- Team/CVs → person-cv blocks
- Equipment → equipment blocks
- Safety procedures → procedure blocks with 'safety' tag

### 2. AI Semantic Matching (Slower, Smarter)
For complex, non-standard requirements:
- Use Claude to understand requirement intent
- Compare with content block descriptions
- Match based on semantic similarity
- Handle project-specific nuances

## Services to Implement

### 1. Content Matcher Service
```python
# services/content_matcher.py

from typing import List, Dict, Optional
from uuid import UUID

class ContentMatcher:
    def __init__(self, db, claude_client):
        self.db = db
        self.claude = claude_client
        self.rules = self._load_matching_rules()

    async def match_requirements(
        self,
        project_id: UUID,
        company_id: UUID
    ) -> List[ContentMatch]:
        """
        Main matching workflow:
        1. Get RC requirements from analysis
        2. Get company content blocks
        3. Apply rule-based matching first
        4. Use AI for unmatched/low-confidence matches
        5. Identify gaps
        6. Save matches to database
        """

    async def _rule_based_match(
        self,
        requirement: RequiredSection,
        content_blocks: List[ContentBlock]
    ) -> Optional[ContentMatch]:
        """
        Apply deterministic matching rules.

        Returns match if confidence > 0.8
        """

    async def _ai_semantic_match(
        self,
        requirement: RequiredSection,
        content_blocks: List[ContentBlock],
        project_context: Dict
    ) -> ContentMatch:
        """
        Use Claude for semantic matching.

        Sends:
        - Requirement description
        - Available content blocks (titles, tags, preview)
        - Project context

        Returns:
        - Matched block IDs
        - Confidence score
        - Reasoning
        - Gap identification
        """

    def _calculate_confidence(
        self,
        requirement: RequiredSection,
        matched_blocks: List[ContentBlock],
        match_type: str
    ) -> float:
        """
        Calculate confidence score (0.0 to 1.0).

        Factors:
        - Tag overlap
        - Content type match
        - Recency of use
        - Past success rate
        """

    async def customize_matches(
        self,
        project_id: UUID,
        user_message: str,
        company_id: UUID
    ) -> CustomizationResponse:
        """
        Handle user customization requests via chat.

        Examples:
        - "Add Pierre's CV to the team section"
        - "Remove the old crane, use the new Potain instead"
        - "Use the Toulouse project as reference instead"
        """
```

### 2. Matching Rules Engine
```python
# services/matching_rules.py

MATCHING_RULES = {
    'presentation': {
        'block_types': ['company-profile', 'certification'],
        'required_tags': ['company', 'présentation'],
        'confidence': 0.9,
        'mandatory': True
    },
    'human-resources': {
        'block_types': ['person-cv'],
        'required_tags': ['team', 'équipe', 'cv'],
        'confidence': 0.9,
        'mandatory': True,
        'min_count': 3  # Need at least 3 CVs
    },
    'equipment': {
        'block_types': ['equipment'],
        'required_tags': ['materiel', 'équipement'],
        'confidence': 0.85,
        'mandatory': True
    },
    'methodology': {
        'block_types': ['methodology-template', 'past-project-reference'],
        'required_tags': ['méthodologie', 'travaux'],
        'confidence': 0.7,  # Lower: likely needs customization
        'needs_generation': True
    },
    'safety': {
        'block_types': ['procedure'],
        'required_tags': ['sécurité', 'safety', 'PPSPS'],
        'confidence': 0.85,
        'needs_customization': True  # Project-specific elements
    },
    'quality': {
        'block_types': ['procedure', 'certification'],
        'required_tags': ['qualité', 'quality', 'ISO'],
        'confidence': 0.85
    },
    'planning': {
        'block_types': [],
        'needs_upload': True,  # User must provide planning
        'needs_generation': True  # AI generates narrative
    },
    'hypotheses': {
        'block_types': ['methodology-template'],
        'required_tags': ['hypothèses', 'chiffrage'],
        'confidence': 0.6,
        'needs_generation': True  # Always project-specific
    }
}

class RuleEngine:
    def match(
        self,
        requirement: RequiredSection,
        content_blocks: List[ContentBlock]
    ) -> Optional[RuleMatch]:
        """Apply matching rules"""

    def get_rule(self, requirement_id: str) -> Optional[Dict]:
        """Get matching rule for requirement type"""
```

### 3. Chat Customization Service
```python
# services/match_customization.py

class MatchCustomizationService:
    def __init__(self, db, claude_client):
        self.db = db
        self.claude = claude_client

    async def handle_user_message(
        self,
        project_id: UUID,
        message: str,
        conversation_history: List[Dict],
        company_id: UUID
    ) -> CustomizationResponse:
        """
        Process user customization request.

        Uses Claude to:
        1. Understand user intent
        2. Identify content blocks to add/remove
        3. Update matches
        4. Generate confirmation message
        """

    def _build_customization_prompt(
        self,
        message: str,
        current_matches: List[ContentMatch],
        available_blocks: List[ContentBlock],
        requirements: List[RequiredSection]
    ) -> str:
        """Build prompt for customization"""

    async def _apply_customization(
        self,
        project_id: UUID,
        changes: List[Dict]
    ):
        """Apply changes to content matches"""
```

## API Endpoints

```python
# routers/content_matching.py

@router.post("/api/projects/{project_id}/match")
async def start_matching(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> MatchingStartedResponse:
    """
    Start content matching (async operation).

    Requires:
    - RC analysis completed
    - Content library has blocks

    Returns task ID for status polling
    """

@router.get("/api/projects/{project_id}/matches")
async def get_matches(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> MatchingResponse:
    """
    Get content matches for project.

    Returns:
    - List of requirements
    - Matched content blocks for each
    - Confidence scores
    - Gaps (needs generation/upload)
    """

@router.post("/api/projects/{project_id}/matches/customize")
async def customize_matches(
    project_id: UUID,
    request: CustomizationRequest,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> CustomizationResponse:
    """
    Customize matches via chat interface.

    Request:
    - message: User message
    - conversation_history: Previous messages

    Response:
    - Updated matches
    - AI response message
    - Actions taken
    """

@router.post("/api/projects/{project_id}/matches/approve")
async def approve_matches(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> ApprovalResponse:
    """
    Approve matches and lock for generation.

    Sets status: matching → matched
    """

@router.post("/api/projects/{project_id}/matches/{requirement_id}/override")
async def override_match(
    project_id: UUID,
    requirement_id: str,
    override: MatchOverride,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
) -> ContentMatch:
    """
    Manually override automatic match.

    Allows user to:
    - Add specific blocks
    - Remove blocks
    - Mark as "needs generation"
    - Mark as "needs upload"
    """
```

## Pydantic Models

```python
# models/content_matching.py

class ContentMatch(BaseModel):
    id: UUID
    project_id: UUID
    requirement_id: str
    requirement_title: str
    matched_blocks: List[UUID]
    confidence: float
    match_reason: str
    match_type: str  # 'rule-based', 'semantic', 'manual'
    needs_generation: bool
    needs_upload: bool
    approved: bool
    created_at: datetime

class MatchingResponse(BaseModel):
    project_id: UUID
    status: str  # 'in_progress', 'completed'
    matches: List[ContentMatchDetail]
    gaps: List[RequirementGap]
    overall_coverage: float  # Percentage of requirements matched

class ContentMatchDetail(ContentMatch):
    requirement: RequiredSection
    blocks: List[ContentBlock]

class RequirementGap(BaseModel):
    requirement_id: str
    requirement_title: str
    gap_type: str  # 'no_content', 'low_confidence', 'needs_generation'
    suggestion: str

class CustomizationRequest(BaseModel):
    message: str
    conversation_history: List[ChatMessage] = []

class CustomizationResponse(BaseModel):
    message: str  # AI response
    actions: List[str]  # Actions taken
    updated_matches: List[ContentMatch]

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime

class MatchOverride(BaseModel):
    add_blocks: List[UUID] = []
    remove_blocks: List[UUID] = []
    needs_generation: Optional[bool] = None
    needs_upload: Optional[bool] = None
```

## Matching Prompt Templates

### Semantic Matching Prompt
```python
SEMANTIC_MATCHING_PROMPT = """
You are helping match a memoir requirement to relevant company content blocks.

REQUIREMENT:
Title: {requirement.title}
Description: {requirement.description}
Points: {requirement.points}
Keywords: {', '.join(requirement.keywords)}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2)}

AVAILABLE CONTENT BLOCKS:
{format_blocks_for_prompt(content_blocks)}

TASK:
1. Identify which content blocks are relevant to this requirement
2. Assess if existing blocks fully satisfy the requirement
3. Determine if AI generation is needed for customization
4. Determine if user must upload something (e.g., planning Gantt chart)

Return JSON:
{{
    "relevant_blocks": ["block-uuid-1", "block-uuid-2"],
    "confidence": 0.85,
    "reasoning": "Clear explanation of why these blocks match",
    "needs_generation": false,
    "needs_upload": false,
    "generation_type": null,
    "missing_elements": []
}}

Be conservative with confidence scores. If blocks don't fully match, lower confidence.
"""
```

### Customization Prompt
```python
CUSTOMIZATION_PROMPT = """
You are helping a user customize content matches for a memoir project.

CURRENT MATCHES:
{format_current_matches(matches)}

AVAILABLE CONTENT BLOCKS:
{format_available_blocks(blocks)}

REQUIREMENTS:
{format_requirements(requirements)}

USER MESSAGE:
"{user_message}"

CONVERSATION HISTORY:
{format_conversation(history)}

TASK:
Understand the user's request and determine what changes to make.

Possible actions:
- ADD_BLOCK: Add a content block to a requirement
- REMOVE_BLOCK: Remove a block from a requirement
- REPLACE_BLOCK: Replace one block with another
- MARK_GENERATION: Mark requirement as needing AI generation
- MARK_UPLOAD: Mark requirement as needing user upload

Return JSON:
{{
    "understood_intent": "Brief summary of what user wants",
    "actions": [
        {{
            "type": "ADD_BLOCK",
            "requirement_id": "team",
            "block_id": "uuid",
            "reason": "User requested Pierre's CV"
        }}
    ],
    "response_message": "Friendly confirmation of actions taken",
    "clarification_needed": null
}}

If you're unclear about the request, ask for clarification.
"""
```

## WebSocket Updates

```python
# websocket/matching.py

async def send_matching_progress(
    project_id: UUID,
    status: str,
    progress: int,
    current_requirement: Optional[str] = None
):
    """
    Send matching progress updates.

    Status values:
    - loading_content: Loading content blocks
    - matching: Processing requirements (1/10)
    - completed: All matches ready
    """
```

## Implementation Steps

1. Create `services/matching_rules.py` with rule definitions
2. Create `services/content_matcher.py` with core logic
3. Create `services/match_customization.py` for chat
4. Create `routers/content_matching.py` with endpoints
5. Create Pydantic models in `models/content_matching.py`
6. Implement WebSocket updates
7. Build confidence scoring algorithm
8. Test with various RC requirements
9. Optimize AI prompts for accuracy
10. Add logging for match quality tracking

## Testing Checklist

- [ ] Rule-based matching works for standard sections
- [ ] AI semantic matching returns relevant blocks
- [ ] Confidence scores are reasonable (0.0-1.0)
- [ ] Gap detection identifies missing content
- [ ] Chat customization understands add/remove requests
- [ ] Manual override allows full control
- [ ] Matches saved to database correctly
- [ ] WebSocket progress updates work
- [ ] Multi-tenant isolation enforced
- [ ] Can approve matches and lock
- [ ] Past successful matches improve future matching

## Performance Considerations

- Rule-based matching: <1 second
- AI semantic matching: 2-5 seconds per requirement
- Total matching time: 20-60 seconds for 10 requirements

## Cost Estimation

Claude API costs per matching session:
- Input: ~5,000 tokens per requirement
- Output: ~500 tokens
- 10 requirements ≈ $0.20-$0.30

## Dependencies
- Task 01 (Database Schema)
- Task 02 (Authentication)
- Task 03 (Content Library)
- Task 04 (RC Analyzer)
- Claude API

## Estimated Effort
**5-6 days**

## Success Criteria
- >80% of standard requirements matched automatically
- Confidence scores correlate with match quality
- Chat customization handles common requests
- Gaps clearly identified for user
- <1 minute total matching time
- User can easily review and adjust matches

## Future Enhancements
- Learning from past matches (track what gets approved)
- Embeddings-based similarity search
- Automatic suggestion of content blocks to create
- Batch matching for multiple projects
