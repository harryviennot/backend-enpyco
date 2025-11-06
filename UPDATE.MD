# Technical Architecture Document

## AI-Powered Construction Technical Memoir Generator

**Version:** 1.0  
**Date:** November 6, 2024  
**Project Codename:** MemoirAI  
**Target Users:** Construction companies (Gros Œuvre contractors)  
**Primary Client:** ENPYCO / Groupe BERNADET

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Definition & Business Case](#2-problem-definition--business-case)
3. [System Architecture Overview](#3-system-architecture-overview)
4. [Core Components](#4-core-components)
5. [Data Models](#5-data-models)
6. [Technology Stack Decisions](#6-technology-stack-decisions)
7. [AI Integration Strategy](#7-ai-integration-strategy)
8. [User Interface Design](#8-user-interface-design)
9. [Document Generation Pipeline](#9-document-generation-pipeline)
10. [Security & Data Privacy](#10-security--data-privacy)
11. [Deployment Architecture](#11-deployment-architecture)
12. [Development Phases & Timeline](#12-development-phases--timeline)
13. [Success Metrics](#13-success-metrics)
14. [Risk Analysis & Mitigation](#14-risk-analysis--mitigation)
15. [Future Enhancements](#15-future-enhancements)

---

## 1. Executive Summary

### What We're Building

An intelligent document assembly system that reduces technical memoir (mémoire technique) creation time from **4-5 days to 1-2 hours** by:

1. **Analyzing** construction consultation requirements (RC)
2. **Matching** requirements to reusable company content
3. **Generating** project-specific sections with AI
4. **Assembling** professional Word documents with proper formatting

### Why This Approach

After analyzing real technical memoirs and understanding user workflows, we determined that:

- ❌ **NOT building:** A visual block editor (too complex, unnecessary)
- ❌ **NOT building:** A Word replacement (users already know Word)
- ✅ **BUILDING:** A smart assembly system that outputs editable Word documents

**Key Insight:** 60% of memoir content is reusable. The value is in **intelligent organization and AI-assisted generation**, not in providing a new editing interface.

### Expected Outcomes

- **Time savings:** 75-80% reduction in memoir creation time
- **Quality improvement:** Consistent formatting, no missed requirements
- **Scoring optimization:** AI tailors content to maximize RC scoring criteria
- **Scalability:** One person can handle multiple simultaneous memoir requests

---

## 2. Problem Definition & Business Case

### Current State Problems

From stakeholder interviews (Clément NOEL, ENPYCO):

1. **Excessive Time Consumption**

   - 4-5 days per memoir
   - Much of this is repetitive work (copy/paste from previous memoirs)
   - Urgent requests create bottlenecks

2. **Quality Issues**

   - "Informations trop complètes et/ou trop lourdes"
   - "Visuel peu attrayant voir indigeste"
   - "Présentation peu graphique"
   - Company hired design agency to address visual problems

3. **Inconsistency**

   - Different team members write differently
   - Hard to maintain consistent quality
   - Easy to miss RC requirements

4. **Limited Value-Add**
   - "Le chargé d'étude n'apporte aucune plus-value" (on repetitive parts)
   - Technical experts spending time on formatting, not on technical excellence

### Business Value Proposition

**For Construction Companies:**

- Respond to more RFPs (increase bid volume by 3-4x)
- Free up technical staff for actual project work
- Improve win rate through optimized, complete responses
- Maintain consistent brand/quality across all submissions

**Market Potential:**

- Every construction trade (electrician, plumber, HVAC, etc.) has this pain
- Français construction market: €150B+ annually
- Each company submits 20-100+ RFPs per year
- Potential SaaS model: €200-500/memoir or €2K-5K/month subscription

### Success Criteria

**Primary:**

- Generate complete memoir in < 2 hours (including user review time)
- 90%+ of generated content requires no modification
- User satisfaction score > 8/10

**Secondary:**

- Estimated RC score within 5 points of actual score
- 95%+ of RC requirements covered automatically
- Zero missed sections or formatting errors

---

## 3. System Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     WEB BROWSER                          │
│                   (React Frontend)                       │
└────────────────┬───────────────────────────┬────────────┘
                 │                           │
                 │ HTTPS/REST                │ WebSocket
                 │                           │ (real-time updates)
                 ↓                           ↓
┌────────────────────────────────────────────────────────┐
│              API GATEWAY (FastAPI)                      │
│  ┌──────────┬──────────┬──────────┬──────────────┐    │
│  │  Auth    │   File   │  Project │   Content    │    │
│  │ Service  │  Upload  │   Mgmt   │   Library    │    │
│  └──────────┴──────────┴──────────┴──────────────┘    │
└────────┬──────────┬──────────┬──────────┬─────────────┘
         │          │          │          │
         ↓          ↓          ↓          ↓
┌────────────────────────────────────────────────────────┐
│                 CORE SERVICES LAYER                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │RC Analyzer  │ │Content      │ │Document     │     │
│  │   Service   │ │Matcher      │ │Generator    │     │
│  │             │ │Service      │ │Service      │     │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘     │
│         │               │               │             │
│         └───────────────┼───────────────┘             │
│                         ↓                             │
│              ┌────────────────────┐                   │
│              │ AI Orchestration   │                   │
│              │    Service         │                   │
│              └─────────┬──────────┘                   │
└────────────────────────┼────────────────────────────────┘
                         │
                         ↓
         ┌───────────────────────────────┐
         │   External AI Services        │
         │  ┌──────────┐  ┌──────────┐  │
         │  │ Claude   │  │  GPT-4   │  │
         │  │   API    │  │   API    │  │
         │  └──────────┘  └──────────┘  │
         └───────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│                   DATA LAYER                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐     │
│  │ PostgreSQL  │ │   S3/Blob   │ │    Redis    │     │
│  │  (Metadata) │ │  (Files)    │ │   (Cache)   │     │
│  └─────────────┘ └─────────────┘ └─────────────┘     │
└────────────────────────────────────────────────────────┘
```

### Architecture Principles

**1. Separation of Concerns**

- **Why:** Each service has one clear responsibility
- **Benefit:** Easy to test, maintain, and scale independently

**2. Document-Centric Design**

- **Why:** Everything revolves around assembling the final Word document
- **Benefit:** Clear data flow, easy to understand

**3. AI as a Service Layer**

- **Why:** AI providers may change, models improve over time
- **Benefit:** Can swap providers without changing core logic

**4. Stateless Services**

- **Why:** Enables horizontal scaling
- **Benefit:** Can handle multiple simultaneous memoir generations

**5. Async Processing**

- **Why:** Document generation takes 2-3 minutes
- **Benefit:** Non-blocking UI, better user experience

---

## 4. Core Components

### 4.1 RC Analyzer Service

**Purpose:** Extract structured requirements from RC PDFs

**Why This Is Critical:**

- RCs are the "requirements specification" for memoirs
- Missing a requirement = lost points = lost contract
- Manual analysis takes 2-3 hours and is error-prone

**Input:**

- RC PDF file (typically 20-80 pages)
- Optional: CCTP (technical specs)

**Output:**

```json
{
  "projectInfo": {
    "name": "Construction 51 logements collectifs",
    "client": "CDC Habitat",
    "location": "Cité Blanche, Toulouse",
    "deadline": "2023-06-12T12:00:00Z"
  },
  "requiredSections": [
    {
      "id": "presentation",
      "title": "Présentation de l'entreprise",
      "description": "Company profile, certifications, experience",
      "points": 10,
      "requirements": [
        "Company history",
        "Relevant certifications",
        "Similar past projects"
      ]
    },
    {
      "id": "human-resources",
      "title": "Moyens humains",
      "description": "Team structure and CVs",
      "points": 15,
      "requirements": [
        "Dedicated team structure",
        "CVs with relevant experience",
        "Organizational chart"
      ]
    }
    // ... more sections
  ],
  "specialRequirements": [
    "Béton bas carbone (CEMEX VERTUA)",
    "Façades préfabriquées type Duomurs",
    "Planning: 8 months, 1000m²/month pace"
  ],
  "format": {
    "type": "free", // or "imposed"
    "template": null, // or path to Word template if imposed
    "pageLimit": null,
    "language": "fr"
  },
  "scoringCriteria": {
    "total": 100,
    "breakdown": {
      "technical": 60,
      "methodology": 25,
      "team": 15
    },
    "emphasis": ["methodology", "planning"] // what gets most points
  }
}
```

**Technology Choice:**

```python
# Primary: PyPDF2 for PDF parsing
import PyPDF2
from typing import Dict, List

class RCAnalyzer:
    def __init__(self, claude_api_key: str):
        self.claude_api = ClaudeAPI(claude_api_key)

    def analyze(self, rc_pdf_path: str) -> RCAnalysis:
        # Step 1: Extract text from PDF
        text = self._extract_text(rc_pdf_path)

        # Step 2: Find the scoring/requirements section
        # Usually titled "Critères de jugement" or "Notation"
        scoring_section = self._find_scoring_section(text)

        # Step 3: Use Claude to structure the requirements
        analysis = self.claude_api.analyze(
            prompt=self._build_analysis_prompt(text, scoring_section),
            context={"document_type": "RC", "language": "fr"}
        )

        # Step 4: Validate and structure the output
        validated = self._validate_analysis(analysis)

        return validated

    def _build_analysis_prompt(self, text: str, scoring: str) -> str:
        return f"""
You are analyzing a French construction consultation regulation (Règlement de Consultation).

TASK: Extract structured information about technical memoir requirements.

SCORING SECTION (most important):
{scoring}

FULL DOCUMENT:
{text}

Extract:
1. Required memoir sections with point values
2. Specific requirements for each section
3. Any special technical requirements
4. Submission format (free or imposed template)
5. Deadline and submission details

Return valid JSON matching the RCAnalysis schema.
Pay special attention to:
- Point values for each section
- Mandatory vs. optional elements
- Technical specifications mentioned
- Past project requirements
"""
```

**Why Claude API:**

- Excellent at understanding French construction terminology
- Large context window (200K tokens) = can process entire RC
- Structured output capability
- Better than GPT-4 for document analysis tasks (in our testing)

**Error Handling:**

```python
class RCAnalysisError(Exception):
    """Base exception for RC analysis failures"""
    pass

class PDFExtractionError(RCAnalysisError):
    """Failed to extract text from PDF"""
    pass

class ScoringNotFoundError(RCAnalysisError):
    """Could not locate scoring criteria in RC"""
    # Fallback: Ask user to manually identify scoring pages
    pass

class AIAnalysisError(RCAnalysisError):
    """AI returned invalid or incomplete analysis"""
    # Fallback: Use template-based extraction
    pass
```

---

### 4.2 Content Library Service

**Purpose:** Store, organize, and retrieve reusable company content

**Why This Is The Core Value:**

- 60% of memoir content is reusable
- Companies have this content scattered across old memoirs
- Organization is key: tagged, searchable, versioned

**Database Schema:**

```sql
-- Companies table
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB
);

-- Content blocks table (the heart of the system)
CREATE TABLE content_blocks (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    type VARCHAR(50) NOT NULL, -- 'company-profile', 'person-cv', 'equipment', etc.
    title VARCHAR(255) NOT NULL,
    content TEXT, -- Main text content
    metadata JSONB, -- Flexible structure for different block types
    tags TEXT[], -- For searching: ['logements', 'béton-armé', 'toulouse']
    version INT DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id)
);

-- Example metadata for different block types:

-- For 'person-cv':
{
  "name": "Pierre BAGUET",
  "role": "Conducteur de travaux",
  "experience_years": 30,
  "expertise": ["logements collectifs", "béton armé", "rénovation"],
  "cv_file_url": "s3://bucket/cvs/pierre-baguet.pdf",
  "photo_url": "s3://bucket/photos/pierre.jpg",
  "contact": {"email": "...", "phone": "..."}
}

-- For 'equipment':
{
  "name": "Grue Potain MDT 218 AJ8",
  "type": "crane",
  "specifications": {
    "height": "30m",
    "reach": "40m",
    "capacity": "8t"
  },
  "applicable_to": ["buildings >20m", "logements"],
  "photos": ["s3://...", "s3://..."],
  "datasheet_url": "s3://..."
}

-- For 'procedure':
{
  "procedure_type": "safety-covid",
  "applies_to": ["all-projects"],
  "last_updated": "2023-01-15",
  "regulatory_basis": ["Code du travail", "..."],
  "content_sections": ["prevention", "PPE", "site-organization"]
}

-- Files storage (all actual files in S3/Blob)
CREATE TABLE files (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50), -- 'pdf', 'docx', 'image', etc.
    storage_url TEXT NOT NULL, -- S3/Blob URL
    size_bytes BIGINT,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    uploaded_by UUID REFERENCES users(id),
    metadata JSONB -- dimensions for images, page count for PDFs, etc.
);

-- Linking content blocks to files (many-to-many)
CREATE TABLE block_files (
    block_id UUID REFERENCES content_blocks(id),
    file_id UUID REFERENCES files(id),
    relationship VARCHAR(50), -- 'main-file', 'photo', 'certificate', etc.
    PRIMARY KEY (block_id, file_id)
);

-- Past projects (for references)
CREATE TABLE past_projects (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    name VARCHAR(255) NOT NULL,
    client VARCHAR(255),
    year INT,
    project_type VARCHAR(100), -- 'logements collectifs', 'rénovation', etc.
    description TEXT,
    techniques_used TEXT[], -- ['Duomurs', 'préfabrication', ...]
    success_factors TEXT[], -- What made it successful
    photos TEXT[], -- URLs to project photos
    is_referenceable BOOLEAN DEFAULT TRUE, -- Can we mention this in new memoirs?
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Templates (for structured sections)
CREATE TABLE section_templates (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    section_type VARCHAR(100), -- 'methodology', 'safety', 'quality', etc.
    title VARCHAR(255),
    template_content TEXT, -- Text with placeholders: {{project_name}}, {{team_size}}
    placeholders JSONB, -- List of available placeholders
    usage_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_content_blocks_company ON content_blocks(company_id);
CREATE INDEX idx_content_blocks_type ON content_blocks(type);
CREATE INDEX idx_content_blocks_tags ON content_blocks USING GIN(tags);
CREATE INDEX idx_content_blocks_active ON content_blocks(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_past_projects_company ON past_projects(company_id);
CREATE INDEX idx_past_projects_type ON past_projects(project_type);
```

**Why PostgreSQL:**

- **JSONB support:** Content blocks have flexible structure (different types need different metadata)
- **Full-text search:** Built-in search across content
- **GIN indexes:** Fast array searching (tags)
- **ACID compliance:** Critical for versioning and consistency
- **Mature ecosystem:** Well-understood, reliable, great tooling

**Content Library API:**

```python
from fastapi import APIRouter, UploadFile, Depends
from typing import List, Optional
from uuid import UUID

router = APIRouter(prefix="/api/library")

@router.post("/blocks")
async def create_block(
    block: ContentBlockCreate,
    files: Optional[List[UploadFile]] = None,
    user: User = Depends(get_current_user)
) -> ContentBlock:
    """
    Create a new reusable content block.

    Why separate endpoint: Creating blocks is distinct from using them
    """
    # Upload files to S3
    file_ids = []
    if files:
        for file in files:
            file_id = await storage_service.upload(
                file=file,
                company_id=user.company_id,
                uploaded_by=user.id
            )
            file_ids.append(file_id)

    # Create block in database
    block_id = await db.content_blocks.insert({
        "company_id": user.company_id,
        "type": block.type,
        "title": block.title,
        "content": block.content,
        "metadata": block.metadata,
        "tags": block.tags,
        "created_by": user.id
    })

    # Link files to block
    if file_ids:
        await db.block_files.insert_many([
            {"block_id": block_id, "file_id": fid, "relationship": "attachment"}
            for fid in file_ids
        ])

    return await db.content_blocks.get(block_id)

@router.get("/blocks/search")
async def search_blocks(
    query: str,
    type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    user: User = Depends(get_current_user)
) -> List[ContentBlock]:
    """
    Search content library.

    Why flexible search: Users need to find content by keywords, tags, type
    """
    filters = {"company_id": user.company_id, "is_active": True}

    if type:
        filters["type"] = type

    if tags:
        filters["tags"] = {"$contains": tags}  # PostgreSQL array contains

    # Full-text search on title and content
    if query:
        results = await db.content_blocks.search(
            query=query,
            filters=filters,
            limit=50
        )
    else:
        results = await db.content_blocks.find(filters, limit=50)

    return results

@router.get("/blocks/{block_id}")
async def get_block(
    block_id: UUID,
    user: User = Depends(get_current_user)
) -> ContentBlock:
    """Get a specific content block with all associated files."""
    block = await db.content_blocks.get(block_id)

    # Security check
    if block.company_id != user.company_id:
        raise PermissionDeniedError()

    # Load associated files
    block.files = await db.block_files.get_files(block_id)

    return block

@router.put("/blocks/{block_id}")
async def update_block(
    block_id: UUID,
    updates: ContentBlockUpdate,
    user: User = Depends(get_current_user)
) -> ContentBlock:
    """
    Update a content block.

    Why versioning: Keep history of changes for audit trail
    """
    block = await db.content_blocks.get(block_id)

    # Security check
    if block.company_id != user.company_id:
        raise PermissionDeniedError()

    # Increment version
    await db.content_blocks.update(block_id, {
        **updates.dict(exclude_unset=True),
        "version": block.version + 1,
        "updated_at": datetime.now()
    })

    return await db.content_blocks.get(block_id)

@router.get("/projects/similar")
async def find_similar_projects(
    project_type: str,
    techniques: List[str],
    user: User = Depends(get_current_user)
) -> List[PastProject]:
    """
    Find past projects similar to current project.

    Why this matters: Good references score points in memoirs
    """
    # Match on project type and techniques used
    similar = await db.past_projects.find({
        "company_id": user.company_id,
        "project_type": project_type,
        "techniques_used": {"$overlap": techniques},  # Array overlap
        "is_referenceable": True
    })

    # Sort by similarity score (number of matching techniques)
    similar.sort(
        key=lambda p: len(set(p.techniques_used) & set(techniques)),
        reverse=True
    )

    return similar[:5]  # Top 5 most similar
```

**Why This Design:**

1. **Flexible metadata (JSONB):** Different content types have different structure
2. **Array columns for tags:** Fast searching, easy to query
3. **Separate files table:** Clean separation of metadata vs. binary data
4. **Versioning:** Track changes, can revert if needed
5. **Company isolation:** Multi-tenant from day one

---

### 4.3 Content Matcher Service

**Purpose:** Match RC requirements to available content blocks

**Why This Is Smart:**

- Saves users time: don't make them manually select every block
- Ensures completeness: won't miss requirements
- Learns from past successful memoirs

**Algorithm:**

```python
from typing import List, Dict, Set
from dataclasses import dataclass

@dataclass
class Requirement:
    id: str
    title: str
    description: str
    type: str  # 'presentation', 'team', 'methodology', etc.
    points: int
    keywords: Set[str]

@dataclass
class Match:
    requirement_id: str
    content_blocks: List[UUID]
    confidence: float  # 0.0 to 1.0
    match_reason: str
    needs_generation: bool  # True if no good match found
    needs_upload: bool  # True if user needs to provide (e.g., planning)

class ContentMatcher:
    def __init__(self, db, claude_api):
        self.db = db
        self.claude_api = claude_api

    async def match_requirements(
        self,
        requirements: List[Requirement],
        company_id: UUID,
        project_context: Dict
    ) -> List[Match]:
        """
        Match requirements to content library.

        Algorithm:
        1. Rule-based matching for standard sections
        2. Semantic matching using AI for complex requirements
        3. Identify what needs to be generated or uploaded
        """
        matches = []

        for req in requirements:
            # Step 1: Try rule-based matching first (fast)
            rule_match = await self._rule_based_match(req, company_id)

            if rule_match and rule_match.confidence > 0.8:
                matches.append(rule_match)
                continue

            # Step 2: Use AI for semantic matching (slower but smarter)
            ai_match = await self._ai_semantic_match(
                req, company_id, project_context
            )

            matches.append(ai_match)

        return matches

    async def _rule_based_match(
        self,
        req: Requirement,
        company_id: UUID
    ) -> Optional[Match]:
        """
        Fast, deterministic matching for standard cases.

        Why rule-based first: Many requirements are standardized
        - "Présentation entreprise" → company profile block
        - "Moyens humains" → team CVs
        - "Certifications" → certification blocks
        """
        rules = {
            'presentation': {
                'block_types': ['company-profile', 'certification'],
                'required_tags': ['company'],
                'confidence': 0.9
            },
            'human-resources': {
                'block_types': ['person-cv', 'org-chart'],
                'required_tags': ['team'],
                'confidence': 0.9
            },
            'equipment': {
                'block_types': ['equipment'],
                'required_tags': ['materiel'],
                'confidence': 0.9
            },
            'safety': {
                'block_types': ['procedure'],
                'required_tags': ['safety', 'securite'],
                'confidence': 0.85
            },
            'quality': {
                'block_types': ['procedure', 'certification'],
                'required_tags': ['quality', 'qualite'],
                'confidence': 0.85
            }
        }

        rule = rules.get(req.type)
        if not rule:
            return None

        # Find matching blocks
        blocks = await self.db.content_blocks.find({
            'company_id': company_id,
            'type': {'$in': rule['block_types']},
            'tags': {'$contains_any': rule['required_tags']},
            'is_active': True
        })

        if not blocks:
            return None

        return Match(
            requirement_id=req.id,
            content_blocks=[b.id for b in blocks],
            confidence=rule['confidence'],
            match_reason=f"Rule-based: matched {len(blocks)} blocks of type {rule['block_types']}",
            needs_generation=False,
            needs_upload=False
        )

    async def _ai_semantic_match(
        self,
        req: Requirement,
        company_id: UUID,
        project_context: Dict
    ) -> Match:
        """
        Use AI to understand requirement and find best matching content.

        Why AI here: Some requirements are complex or non-standard
        """
        # Get all potentially relevant blocks
        candidate_blocks = await self.db.content_blocks.find({
            'company_id': company_id,
            'is_active': True
        }, limit=100)  # Limit for performance

        # Ask Claude to analyze
        analysis = await self.claude_api.analyze({
            'prompt': f"""
Analyze this memoir requirement and determine which content blocks are relevant.

REQUIREMENT:
Title: {req.title}
Description: {req.description}
Type: {req.type}
Keywords: {', '.join(req.keywords)}

PROJECT CONTEXT:
{json.dumps(project_context, indent=2)}

AVAILABLE CONTENT BLOCKS:
{json.dumps([{
    'id': str(b.id),
    'type': b.type,
    'title': b.title,
    'tags': b.tags,
    'content_preview': b.content[:200] if b.content else None
} for b in candidate_blocks], indent=2)}

TASK:
1. Identify which blocks are relevant (return block IDs)
2. Assess if the requirement can be fully satisfied with existing blocks
3. Determine if AI generation is needed for project-specific content
4. Identify if user upload is needed (e.g., for planning, site plans)

Return JSON:
{{
    "relevant_blocks": ["block-id-1", "block-id-2"],
    "confidence": 0.75,
    "reasoning": "explanation",
    "needs_generation": false,
    "needs_upload": false,
    "generation_type": null  // or "methodology", "hypotheses", etc.
}}
""",
            'response_format': 'json'
        })

        return Match(
            requirement_id=req.id,
            content_blocks=[UUID(bid) for bid in analysis['relevant_blocks']],
            confidence=analysis['confidence'],
            match_reason=analysis['reasoning'],
            needs_generation=analysis['needs_generation'],
            needs_upload=analysis['needs_upload']
        )
```

**Why This Two-Step Approach:**

1. **Performance:** Rule-based matching is instant
2. **Cost:** AI calls are expensive; only use when necessary
3. **Reliability:** Rules handle 70% of cases deterministically
4. **Flexibility:** AI handles edge cases and complex requirements

**Confidence Scoring:**

```python
def calculate_confidence(
    requirement: Requirement,
    blocks: List[ContentBlock],
    match_type: str
) -> float:
    """
    Calculate confidence score for a match.

    Why confidence matters: User should know which matches to review
    """
    if match_type == 'rule-based':
        # High confidence for standard matches
        if blocks and requirement.type in ['presentation', 'equipment']:
            return 0.9
        elif blocks:
            return 0.8
        else:
            return 0.0

    elif match_type == 'semantic':
        # AI provides confidence, but we adjust based on:
        # - Number of matching tags
        # - Recency of content
        # - Past usage success

        ai_confidence = 0.7  # from AI analysis

        # Boost if tags match
        tag_match_ratio = len(
            set(requirement.keywords) &
            set([tag for b in blocks for tag in b.tags])
        ) / len(requirement.keywords)

        ai_confidence += 0.2 * tag_match_ratio

        # Boost if recently used successfully
        # (track which blocks were used in successful past memoirs)
        recent_success = any(
            b.metadata.get('last_used_success') and
            (datetime.now() - b.metadata['last_used_success']).days < 90
            for b in blocks
        )
        if recent_success:
            ai_confidence += 0.1

        return min(ai_confidence, 1.0)

    return 0.0
```

---

### 4.4 AI Content Generation Service

**Purpose:** Generate project-specific sections that can't be reused

**Why This Is The "Magic":**

- Can't reuse methodology verbatim (project-specific)
- Can't reuse hypotheses (project-specific)
- Can adapt standard procedures to specific project requirements

**Generation Strategy:**

```python
from enum import Enum
from typing import Dict, Any, Optional

class SectionType(Enum):
    HYPOTHESES = "hypotheses"  # Project pricing assumptions
    METHODOLOGY = "methodology"  # How work will be executed
    SITE_ORGANIZATION = "site-organization"  # Site installation approach
    PLANNING_NARRATIVE = "planning-narrative"  # Written planning description
    SAFETY_CUSTOMIZED = "safety-customized"  # Project-specific safety
    QUALITY_CUSTOMIZED = "quality-customized"  # Project-specific quality

class AIContentGenerator:
    def __init__(self, claude_api, gpt_api):
        self.claude_api = claude_api
        self.gpt_api = gpt_api
        self.generation_templates = self._load_templates()

    async def generate_section(
        self,
        section_type: SectionType,
        project_context: Dict[str, Any],
        company_knowledge: Dict[str, Any],
        template: Optional[str] = None
    ) -> GeneratedContent:
        """
        Generate a memoir section tailored to the project.

        Why carefully structured prompts:
        - Need consistent output format
        - Must match company's writing style
        - Should optimize for RC scoring criteria
        """
        # Choose the right AI model for the task
        model = self._select_model(section_type)

        # Build generation prompt
        prompt = self._build_prompt(
            section_type=section_type,
            project_context=project_context,
            company_knowledge=company_knowledge,
            template=template
        )

        # Generate content
        result = await model.generate(
            prompt=prompt,
            max_tokens=4000,  # ~3000 words
            temperature=0.3,  # Lower = more consistent
            stop_sequences=None
        )

        # Post-process
        content = self._post_process(result, section_type)

        # Quality check
        quality_score = await self._quality_check(content, section_type)

        return GeneratedContent(
            section_type=section_type,
            content=content,
            quality_score=quality_score,
            generation_metadata={
                'model': model.name,
                'tokens_used': result.tokens,
                'generation_time': result.elapsed_time
            }
        )

    def _select_model(self, section_type: SectionType) -> AIModel:
        """
        Choose AI model based on section requirements.

        Why different models for different tasks:
        - Claude: Better at long-form, structured French content
        - GPT-4: Better at creative variation, shorter content
        """
        if section_type in [
            SectionType.METHODOLOGY,
            SectionType.SITE_ORGANIZATION
        ]:
            # Need long-form, detailed, structured content
            return self.claude_api

        elif section_type in [
            SectionType.HYPOTHESES,
            SectionType.PLANNING_NARRATIVE
        ]:
            # Shorter, more formulaic content
            return self.gpt_api

        else:
            # Default to Claude for French content
            return self.claude_api

    def _build_prompt(
        self,
        section_type: SectionType,
        project_context: Dict,
        company_knowledge: Dict,
        template: Optional[str]
    ) -> str:
        """
        Build a detailed prompt for content generation.

        Why detailed prompts matter:
        - AI needs context to generate relevant content
        - Must understand company's style and approach
        - Should optimize for scoring criteria
        """
        if section_type == SectionType.METHODOLOGY:
            return self._build_methodology_prompt(
                project_context, company_knowledge, template
            )
        elif section_type == SectionType.HYPOTHESES:
            return self._build_hypotheses_prompt(
                project_context, company_knowledge
            )
        # ... other section types

    def _build_methodology_prompt(
        self,
        project: Dict,
        company: Dict,
        template: Optional[str]
    ) -> str:
        """
        Prompt for generating methodology section.

        This is the most complex and highest-value section (25 points typical).
        """
        return f"""
You are writing the "ORGANISATION DU CHANTIER, MÉTHODOLOGIE DES TRAVAUX" section for a French construction technical memoir (mémoire technique).

CRITICAL CONTEXT:
This section is worth {project['scoring']['methodology_points']} points out of {project['scoring']['total']} total.
This is the most important section. Be comprehensive and detailed.

PROJECT INFORMATION:
- Project: {project['name']}
- Type: {project['type']}
- Size: {project['size']}
- Location: {project['location']}
- Key requirements from RC: {json.dumps(project['rc_requirements'], indent=2)}
- Special technical requirements: {json.dumps(project['special_requirements'], indent=2)}

COMPANY'S STANDARD APPROACH (adapt this to the project):
{company['standard_methodology']}

EQUIPMENT AVAILABLE:
{json.dumps(company['equipment_list'], indent=2)}

PAST SIMILAR PROJECTS (for reference):
{json.dumps(company['similar_projects'], indent=2)}

{f"TEMPLATE TO FOLLOW:\\n{template}" if template else ""}

SCORING CRITERIA (optimize for these):
{json.dumps(project['methodology_scoring_criteria'], indent=2)}

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
7. Emphasize techniques that score well (e.g., prefabrication, low-carbon concrete)
8. Include placeholder tags for images: {{{{IMAGE: description}}}}
9. Aim for 3000-4000 words (this is a major section)

STRUCTURE:
2. ORGANISATION DU CHANTIER, MÉTHODOLOGIE DES TRAVAUX

2.1 Installation de chantier, études techniques et implantation
[Describe site installation, crane placement, base camp setup, surveying]

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

    def _build_hypotheses_prompt(
        self,
        project: Dict,
        company: Dict
    ) -> str:
        """
        Prompt for generating project assumptions section.

        Why this section: Lists all assumptions made in the pricing estimate.
        Typical length: 1-2 pages, bullet points
        """
        return f"""
You are writing the "HYPOTHÈSES DE CHIFFRAGE" (Pricing Assumptions) section for a French construction technical memoir.

PROJECT INFORMATION:
- Project: {project['name']}
- Size: {project['size']}
- Location: {project['location']}
- Project documents provided: {', '.join(project['documents_provided'])}

COMPANY'S TYPICAL ASSUMPTIONS (adapt/add to these):
{company['standard_hypotheses']}

DETECTED PROJECT SPECIFICS (from CCTP analysis):
{json.dumps(project['detected_specifics'], indent=2)}

TASK:
Generate a comprehensive list of pricing assumptions. Include:

1. Site assumptions:
   - Access roads, utilities, existing conditions
   - Site occupation rights (voirie)
   - Condition of adjacent structures

2. Scope assumptions:
   - What is included vs. excluded
   - Responsibilities (prorata, etc.)
   - Work limits

3. Technical assumptions:
   - Foundation types and depths
   - Concrete specifications
   - Crane sizing and placement
   - Scaffolding approach

4. Administrative assumptions:
   - Permits and approvals
   - Studies (G3, etc.)
   - Insurance and bonds

5. Coordination assumptions:
   - Interfaces with other trades
   - Common facilities
   - Project management structure

FORMAT:
- Use bullet points (• not -)
- Be specific with measurements and quantities
- Reference project documents when applicable
- Write in formal French
- Group by category
- Typical length: 50-70 bullet points

Example:
• SHOB totale = 7 238m²
• Il n'est pas prévu de frais d'occupation de voirie
• Une grue à tour sans ascenseur (hauteur 30m, flèche 40m) est prévue...

Begin writing now:
"""

    async def _quality_check(
        self,
        content: str,
        section_type: SectionType
    ) -> float:
        """
        Assess quality of generated content.

        Why quality checks matter:
        - AI can occasionally generate low-quality content
        - Need to alert user if manual review needed
        - Can retry generation if quality too low
        """
        checks = {
            'length': self._check_length(content, section_type),
            'structure': self._check_structure(content, section_type),
            'specificity': await self._check_specificity(content),
            'language': self._check_language_quality(content)
        }

        # Weighted average
        weights = {
            'length': 0.2,
            'structure': 0.3,
            'specificity': 0.3,
            'language': 0.2
        }

        score = sum(checks[k] * weights[k] for k in checks)

        return score

    def _check_length(self, content: str, section_type: SectionType) -> float:
        """
        Check if content is appropriate length.

        Why this matters: Too short = missing information, too long = bloated
        """
        word_count = len(content.split())

        expected_ranges = {
            SectionType.METHODOLOGY: (2500, 4000),
            SectionType.HYPOTHESES: (800, 1500),
            SectionType.SITE_ORGANIZATION: (1000, 2000),
            SectionType.PLANNING_NARRATIVE: (500, 1000),
        }

        min_words, max_words = expected_ranges.get(
            section_type,
            (500, 2000)  # default
        )

        if word_count < min_words:
            return 0.5  # Too short
        elif word_count > max_words:
            return 0.7  # Too long
        else:
            # Perfect range = 1.0
            # Score decreases as you move away from center
            center = (min_words + max_words) / 2
            distance = abs(word_count - center) / (max_words - min_words)
            return 1.0 - (distance * 0.3)

    def _check_structure(self, content: str, section_type: SectionType) -> float:
        """
        Check if content has proper structure.

        Why this matters: Sections need subsections, paragraphs, formatting
        """
        # Count subsection headers (e.g., "2.1", "2.2")
        import re
        subsections = len(re.findall(r'^\d+\.\d+', content, re.MULTILINE))

        # Count paragraphs
        paragraphs = len([p for p in content.split('\n\n') if p.strip()])

        # Count image placeholders
        images = len(re.findall(r'\{\{IMAGE:', content))

        if section_type == SectionType.METHODOLOGY:
            # Expect 5-10 subsections, 20-40 paragraphs, 3-8 images
            structure_score = (
                0.4 * min(subsections / 7.5, 1.0) +  # Subsections
                0.4 * min(paragraphs / 30, 1.0) +    # Paragraphs
                0.2 * min(images / 5, 1.0)           # Images
            )
        elif section_type == SectionType.HYPOTHESES:
            # Expect bullet points, not paragraphs
            bullets = len(re.findall(r'^•', content, re.MULTILINE))
            structure_score = min(bullets / 60, 1.0)
        else:
            # Generic structure check
            structure_score = min((subsections + paragraphs) / 20, 1.0)

        return structure_score

    async def _check_specificity(self, content: str) -> float:
        """
        Check if content is specific vs. generic.

        Why this matters: Generic content doesn't score well
        Good: "Grue Potain MDT 218 AJ8, hauteur 30m, flèche 40m"
        Bad: "Une grue adaptée sera utilisée"
        """
        # Use AI to assess specificity
        assessment = await self.claude_api.analyze({
            'prompt': f"""
Rate the specificity of this construction methodology text on a scale of 0.0 to 1.0.

Specific content includes:
- Equipment names and models
- Exact measurements and quantities
- Specific techniques and materials
- Named certifications and standards
- Concrete project details

Generic content includes:
- Vague descriptions ("appropriate equipment")
- Missing measurements
- No brand/model names
- Generic statements

TEXT:
{content[:2000]}  # Sample first 2000 chars

Return only a number between 0.0 and 1.0
""",
            'max_tokens': 10
        })

        try:
            return float(assessment.strip())
        except:
            return 0.7  # Default if parsing fails

    def _check_language_quality(self, content: str) -> float:
        """
        Check French language quality.

        Why this matters: Grammatical errors look unprofessional
        """
        # Basic checks:
        # - No obvious errors (random characters, broken words)
        # - Proper French construction terminology
        # - Formal register (no informal language)

        issues = 0

        # Check for obvious errors
        if re.search(r'[^\w\s\.,;:!?\'\"()àâäéèêëïîôùûüÿæœç-]', content):
            issues += 1  # Random characters

        # Check for informal language (should be rare in technical docs)
        informal_words = ['ok', 'bon', 'voilà', 'donc bon']
        if any(word in content.lower() for word in informal_words):
            issues += 1

        # Check for proper technical terms
        required_terms = ['béton', 'coffrage', 'plancher', 'fondation']
        found_terms = sum(1 for term in required_terms if term in content.lower())
        if found_terms < 2:
            issues += 1  # Doesn't look like construction content

        # Score: 1.0 - (0.2 * issues)
        return max(1.0 - (0.2 * issues), 0.0)
```

**Why This Architecture:**

1. **Model Selection:** Use best AI for each task (Claude for long-form, GPT for short)
2. **Detailed Prompts:** AI needs context to generate quality content
3. **Quality Checks:** Catch low-quality output before showing to user
4. **Retry Logic:** If quality low, can regenerate automatically
5. **Structured Output:** Ensures content fits into document template

---

### 4.5 Document Generator Service

**Purpose:** Assemble final Word document from all components

**Why Word Generation Is Non-Trivial:**

- Must preserve professional formatting
- Images must be embedded correctly
- Tables, headers, footers, page numbers
- Table of contents must be generated
- Must match company's visual style

**Technology Choice:**

```python
# Using python-docx library
# Why: Most mature, well-documented, actively maintained

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from typing import List, Dict, Any
import io

class WordDocumentGenerator:
    def __init__(self, template_manager):
        self.template_manager = template_manager

    async def generate_memoir(
        self,
        sections: List[SectionContent],
        project_info: Dict,
        company_info: Dict,
        style_config: StyleConfig,
        annexes: List[Annex]
    ) -> io.BytesIO:
        """
        Generate complete technical memoir as Word document.

        Why Word specifically:
        - Industry standard for document exchange
        - Clients can edit before submission
        - Supports all required features (images, tables, TOC)
        - Can be converted to PDF easily
        """
        # Load base template
        doc = self._create_document_from_template(style_config.template_name)

        # Apply company styling
        self._apply_company_style(doc, company_info, style_config)

        # Generate cover page
        self._add_cover_page(doc, project_info, company_info)

        # Add table of contents
        self._add_table_of_contents(doc, sections)

        # Add each section
        for section in sections:
            self._add_section(doc, section, style_config)

        # Add annexes
        if annexes:
            self._add_annexes(doc, annexes, style_config)

        # Post-processing
        self._add_page_numbers(doc)
        self._add_headers_footers(doc, project_info, company_info)
        self._finalize_formatting(doc)

        # Save to bytes
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        return buffer

    def _create_document_from_template(self, template_name: str) -> Document:
        """
        Load base template.

        Why templates:
        - Consistent styling across all memoirs
        - Pre-configured styles (headings, body, captions)
        - Company branding (colors, fonts)
        """
        template_path = self.template_manager.get_template(template_name)

        if template_path:
            # Load existing template
            doc = Document(template_path)
        else:
            # Create new document with default styling
            doc = Document()
            self._setup_default_styles(doc)

        return doc

    def _setup_default_styles(self, doc: Document):
        """
        Configure document styles.

        Why custom styles matter:
        - Consistent formatting throughout document
        - Easy to apply (just set style name)
        - Can update all instances by changing style
        """
        styles = doc.styles

        # Heading 1 style (Section headers)
        h1 = styles.add_style('Custom Heading 1', WD_STYLE_TYPE.PARAGRAPH)
        h1.font.name = 'Arial'
        h1.font.size = Pt(16)
        h1.font.bold = True
        h1.font.color.rgb = RGBColor(0, 51, 102)  # Dark blue
        h1.paragraph_format.space_before = Pt(24)
        h1.paragraph_format.space_after = Pt(12)
        h1.paragraph_format.keep_with_next = True

        # Heading 2 style (Subsection headers)
        h2 = styles.add_style('Custom Heading 2', WD_STYLE_TYPE.PARAGRAPH)
        h2.font.name = 'Arial'
        h2.font.size = Pt(14)
        h2.font.bold = True
        h2.font.color.rgb = RGBColor(0, 51, 102)
        h2.paragraph_format.space_before = Pt(18)
        h2.paragraph_format.space_after = Pt(6)
        h2.paragraph_format.keep_with_next = True

        # Body text style
        body = styles.add_style('Custom Body', WD_STYLE_TYPE.PARAGRAPH)
        body.font.name = 'Arial'
        body.font.size = Pt(11)
        body.paragraph_format.space_after = Pt(6)
        body.paragraph_format.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
        body.paragraph_format.line_spacing = 1.15
        body.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        # Caption style (for images/tables)
        caption = styles.add_style('Custom Caption', WD_STYLE_TYPE.PARAGRAPH)
        caption.font.name = 'Arial'
        caption.font.size = Pt(9)
        caption.font.italic = True
        caption.font.color.rgb = RGBColor(89, 89, 89)
        caption.paragraph_format.space_before = Pt(3)
        caption.paragraph_format.space_after = Pt(9)
        caption.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def _add_cover_page(
        self,
        doc: Document,
        project: Dict,
        company: Dict
    ):
        """
        Create professional cover page.

        Why cover page matters: First impression, branding
        """
        # Add section break for cover page
        section = doc.add_section()

        # Company logo (centered, top)
        if company.get('logo_url'):
            logo_path = self._download_image(company['logo_url'])
            paragraph = doc.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = paragraph.add_run()
            run.add_picture(logo_path, width=Inches(2.5))

        # Vertical space
        doc.add_paragraph()
        doc.add_paragraph()

        # Document title
        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.add_run("MÉMOIRE TECHNIQUE")
        title_run.font.size = Pt(24)
        title_run.font.bold = True
        title_run.font.color.rgb = RGBColor(0, 51, 102)

        # Vertical space
        doc.add_paragraph()

        # Project name
        project_para = doc.add_paragraph()
        project_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        project_run = project_para.add_run(project['name'])
        project_run.font.size = Pt(18)
        project_run.font.bold = True

        # Vertical space
        doc.add_paragraph()
        doc.add_paragraph()

        # Project details table
        table = doc.add_table(rows=4, cols=2)
        table.style = 'Light Grid Accent 1'

        details = [
            ('Client:', project['client']),
            ('Localisation:', project['location']),
            ('Lot:', project['lot']),
            ('Date:', project['submission_date'].strftime('%d/%m/%Y'))
        ]

        for i, (label, value) in enumerate(details):
            table.rows[i].cells[0].text = label
            table.rows[i].cells[0].paragraphs[0].runs[0].font.bold = True
            table.rows[i].cells[1].text = value

        # Vertical space
        doc.add_paragraph()
        doc.add_paragraph()

        # Company name at bottom
        company_para = doc.add_paragraph()
        company_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        company_run = company_para.add_run(company['name'])
        company_run.font.size = Pt(14)
        company_run.font.bold = True

        # Company address
        address_para = doc.add_paragraph()
        address_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        address_para.add_run(f"{company['address']}\n{company['city']}")

        # Page break after cover
        doc.add_page_break()

    def _add_table_of_contents(
        self,
        doc: Document,
        sections: List[SectionContent]
    ):
        """
        Generate table of contents.

        Why TOC matters: Required in professional documents, helps navigation
        """
        # TOC heading
        toc_heading = doc.add_paragraph()
        toc_run = toc_heading.add_run("SOMMAIRE")
        toc_run.font.size = Pt(16)
        toc_run.font.bold = True
        toc_run.font.color.rgb = RGBColor(0, 51, 102)

        doc.add_paragraph()  # Space

        # Build TOC table
        toc_entries = []
        for i, section in enumerate(sections, start=1):
            toc_entries.append((f"{i}. {section.title}", section.title))

            # Add subsections if any
            if section.subsections:
                for j, subsection in enumerate(section.subsections, start=1):
                    toc_entries.append((f"  {i}.{j} {subsection.title}", subsection.title))

        # Add annexes
        if any(s.has_annexes for s in sections):
            toc_entries.append(("ANNEXES", "Annexes"))

        # Create TOC table
        table = doc.add_table(rows=len(toc_entries), cols=2)
        table.style = 'Light List'

        for i, (title, ref) in enumerate(toc_entries):
            # Entry title
            cell = table.rows[i].cells[0]
            cell.text = title

            # Page number placeholder (Word will fill this in)
            page_cell = table.rows[i].cells[1]
            page_cell.text = "X"  # Placeholder
            page_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Page break after TOC
        doc.add_page_break()

    def _add_section(
        self,
        doc: Document,
        section: SectionContent,
        style: StyleConfig
    ):
        """
        Add a section with proper formatting.

        Why careful formatting: Professional appearance, readability
        """
        # Section number and title
        heading = doc.add_heading(level=1)
        heading.text = f"{section.number}. {section.title.upper()}"
        heading.style = 'Custom Heading 1'

        # Section content (parse and format)
        content_parts = self._parse_content(section.content)

        for part in content_parts:
            if part['type'] == 'paragraph':
                p = doc.add_paragraph(part['text'])
                p.style = 'Custom Body'

            elif part['type'] == 'subsection':
                sub = doc.add_heading(level=2)
                sub.text = part['text']
                sub.style = 'Custom Heading 2'

            elif part['type'] == 'bullet':
                p = doc.add_paragraph(part['text'], style='List Bullet')

            elif part['type'] == 'image':
                self._add_image(doc, part['data'], part.get('caption'), style)

            elif part['type'] == 'table':
                self._add_table(doc, part['data'], style)

        # Subsections
        if section.subsections:
            for subsection in section.subsections:
                self._add_subsection(doc, subsection, style)

    def _add_image(
        self,
        doc: Document,
        image_data: Dict,
        caption: Optional[str],
        style: StyleConfig
    ):
        """
        Add image with proper sizing and caption.

        Why careful image handling:
        - Images must fit on page
        - Must maintain aspect ratio
        - Must be properly captioned
        """
        # Download/load image
        image_path = image_data.get('path') or self._download_image(image_data['url'])

        # Determine appropriate width
        # Standard page width: 6.5 inches (with margins)
        max_width = Inches(6.5)

        # Get image dimensions
        from PIL import Image
        img = Image.open(image_path)
        aspect_ratio = img.width / img.height

        # Calculate dimensions
        if image_data.get('size') == 'full':
            width = max_width
        elif image_data.get('size') == 'half':
            width = max_width / 2
        else:
            # Default: fit to page width
            width = min(Inches(img.width / 96), max_width)  # 96 DPI

        # Add image
        paragraph = doc.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragraph.add_run()
        run.add_picture(image_path, width=width)

        # Add caption if provided
        if caption:
            caption_para = doc.add_paragraph(caption)
            caption_para.style = 'Custom Caption'

    def _add_table(
        self,
        doc: Document,
        table_data: Dict,
        style: StyleConfig
    ):
        """
        Add formatted table.

        Why tables: Present structured data (scoring, team, equipment)
        """
        rows = table_data['rows']
        cols = table_data['cols']

        table = doc.add_table(rows=rows, cols=cols)
        table.style = 'Light Grid Accent 1'

        # Headers
        if table_data.get('headers'):
            for i, header in enumerate(table_data['headers']):
                cell = table.rows[0].cells[i]
                cell.text = header
                cell.paragraphs[0].runs[0].font.bold = True
                cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                # Background color
                self._set_cell_background(cell, RGBColor(0, 51, 102))
                cell.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

        # Data rows
        for row_idx, row_data in enumerate(table_data['data'], start=1):
            for col_idx, cell_data in enumerate(row_data):
                table.rows[row_idx].cells[col_idx].text = str(cell_data)

        # Auto-fit columns
        table.autofit = True

    def _set_cell_background(self, cell, color: RGBColor):
        """Set cell background color (requires low-level XML manipulation)."""
        shading_elm = OxmlElement('w:shd')
        shading_elm.set(qn('w:fill'), f"{color.rgb[0]:02x}{color.rgb[1]:02x}{color.rgb[2]:02x}")
        cell._element.get_or_add_tcPr().append(shading_elm)

    def _add_headers_footers(
        self,
        doc: Document,
        project: Dict,
        company: Dict
    ):
        """
        Add headers and footers to all pages.

        Why: Professional documents have branded headers/footers
        """
        section = doc.sections[0]

        # Header
        header = section.header
        header_para = header.paragraphs[0]
        header_para.text = f"{company['name']} - {project['name']}"
        header_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        header_para.style = 'Header'

        # Footer with page number
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = "Page "
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Add page number field
        run = footer_para.add_run()
        fldChar1 = OxmlElement('w:fldChar')
        fldChar1.set(qn('w:fldCharType'), 'begin')
        run._r.append(fldChar1)

        instrText = OxmlElement('w:instrText')
        instrText.set(qn('xml:space'), 'preserve')
        instrText.text = "PAGE"
        run._r.append(instrText)

        fldChar2 = OxmlElement('w:fldChar')
        fldChar2.set(qn('w:fldCharType'), 'end')
        run._r.append(fldChar2)

    def _add_page_numbers(self, doc: Document):
        """Add page numbers to all pages except cover."""
        # (Handled in _add_headers_footers)
        pass

    def _finalize_formatting(self, doc: Document):
        """
        Final formatting passes.

        Why: Ensure consistent spacing, no orphans/widows, etc.
        """
        for paragraph in doc.paragraphs:
            # Prevent orphan/widow lines
            paragraph.paragraph_format.widow_control = True

            # Keep headings with next paragraph
            if paragraph.style.name.startswith('Heading'):
                paragraph.paragraph_format.keep_with_next = True
```

**Why This Is Complex:**

1. **Word XML Structure:** python-docx abstracts it, but still complex
2. **Image Handling:** Must resize, maintain aspect ratio, position correctly
3. **Professional Formatting:** Headers, footers, TOC, page numbers
4. **Style Consistency:** Every element must use proper styles
5. **Multi-page Layout:** Must handle page breaks, sections

**Quality Assurance:**

```python
class DocumentQA:
    """Quality assurance checks for generated documents."""

    async def validate_document(self, doc_bytes: bytes) -> QAReport:
        """
        Run quality checks on generated document.

        Why QA: Catch issues before user sees document
        """
        doc = Document(io.BytesIO(doc_bytes))

        issues = []

        # Check 1: All required sections present
        sections_found = [p.text for p in doc.paragraphs if p.style.name == 'Heading 1']
        missing_sections = set(REQUIRED_SECTIONS) - set(sections_found)
        if missing_sections:
            issues.append(f"Missing sections: {', '.join(missing_sections)}")

        # Check 2: Images loaded correctly
        image_count = sum(1 for rel in doc.part.rels.values()
                         if "image" in rel.reltype)
        if image_count == 0:
            issues.append("No images found in document")

        # Check 3: Table of contents present
        has_toc = any("SOMMAIRE" in p.text for p in doc.paragraphs)
        if not has_toc:
            issues.append("Table of contents missing")

        # Check 4: Page count reasonable
        page_count = len(doc.sections)  # Approximate
        if page_count < 20:
            issues.append(f"Document seems too short: ~{page_count} pages")
        elif page_count > 100:
            issues.append(f"Document seems too long: ~{page_count} pages")

        # Check 5: No empty paragraphs (excessive spacing)
        empty_paras = sum(1 for p in doc.paragraphs if not p.text.strip())
        if empty_paras > 50:
            issues.append(f"Too many empty paragraphs: {empty_paras}")

        return QAReport(
            passed=len(issues) == 0,
            issues=issues,
            stats={
                'sections': len(sections_found),
                'images': image_count,
                'approximate_pages': page_count,
                'word_count': sum(len(p.text.split()) for p in doc.paragraphs)
            }
        )
```

---

## 5. Data Models

### Core Entities

```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

# ============================================================================
# COMPANIES & USERS
# ============================================================================

class Company(BaseModel):
    """A construction company using the platform."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    address: str
    city: str
    postal_code: str
    phone: str
    email: str
    logo_url: Optional[str] = None
    certifications: List[str] = []  # ['Qualibat 2113', 'Ethibat']
    settings: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        orm_mode = True

class User(BaseModel):
    """A user within a company."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    email: str
    full_name: str
    role: str  # 'admin', 'user', 'viewer'
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = None

# ============================================================================
# CONTENT LIBRARY
# ============================================================================

class ContentBlockType(str, Enum):
    COMPANY_PROFILE = "company-profile"
    PERSON_CV = "person-cv"
    EQUIPMENT = "equipment"
    PROCEDURE = "procedure"
    CERTIFICATION = "certification"
    PAST_PROJECT = "past-project"
    TEMPLATE = "template"

class ContentBlock(BaseModel):
    """A reusable piece of content."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    type: ContentBlockType
    title: str
    content: Optional[str] = None  # Main text content
    metadata: Dict[str, Any] = {}  # Type-specific data
    tags: List[str] = []
    version: int = 1
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: UUID

    # Relationships
    files: List['File'] = []

    class Config:
        orm_mode = True

class File(BaseModel):
    """A file stored in the system."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    filename: str
    file_type: str  # 'pdf', 'docx', 'jpg', etc.
    storage_url: str  # S3/Blob URL
    size_bytes: int
    uploaded_at: datetime = Field(default_factory=datetime.now)
    uploaded_by: UUID
    metadata: Dict[str, Any] = {}  # e.g., dimensions for images

    class Config:
        orm_mode = True

class PastProject(BaseModel):
    """A past project that can be referenced."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    name: str
    client: str
    year: int
    project_type: str  # 'logements collectifs', etc.
    description: str
    techniques_used: List[str] = []
    success_factors: List[str] = []
    photos: List[str] = []  # URLs
    is_referenceable: bool = True
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# PROJECTS & MEMOIRS
# ============================================================================

class ProjectStatus(str, Enum):
    DRAFT = "draft"
    RC_ANALYSIS = "rc-analysis"
    CONTENT_MATCHING = "content-matching"
    GENERATION = "generation"
    REVIEW = "review"
    COMPLETED = "completed"
    SUBMITTED = "submitted"

class Project(BaseModel):
    """A memoir project."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID
    name: str
    client: str
    location: str
    project_type: str
    size: Optional[str] = None  # e.g., "7238m² SHOB"
    lot: Optional[str] = None  # e.g., "Lot 3: Gros œuvre"
    deadline: Optional[datetime] = None
    status: ProjectStatus = ProjectStatus.DRAFT

    # Analysis results
    rc_analysis: Optional['RCAnalysis'] = None
    content_matches: List['ContentMatch'] = []

    # Generated sections
    sections: List['SectionContent'] = []

    # Final document
    final_document_url: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: UUID

    class Config:
        orm_mode = True

class RCAnalysis(BaseModel):
    """Results of analyzing an RC document."""
    project_id: UUID
    rc_file_url: str

    # Extracted information
    required_sections: List['RequiredSection']
    scoring_criteria: Dict[str, int]  # section_id -> points
    special_requirements: List[str]
    format_type: str  # 'free' or 'imposed'
    imposed_template_url: Optional[str] = None

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.now)
    confidence: float  # 0.0 to 1.0

class RequiredSection(BaseModel):
    """A section required by the RC."""
    id: str  # e.g., 'presentation', 'human-resources'
    title: str
    description: str
    requirements: List[str]
    points: int
    keywords: List[str]  # For matching

class ContentMatch(BaseModel):
    """A match between requirement and content."""
    requirement_id: str
    content_block_ids: List[UUID]
    confidence: float
    match_reason: str
    needs_generation: bool = False
    needs_upload: bool = False
    generation_type: Optional[str] = None

class SectionType(str, Enum):
    COVER = "cover"
    TOC = "toc"
    CONTENT = "content"
    ANNEX = "annex"

class SectionContent(BaseModel):
    """Content for a memoir section."""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    type: SectionType
    number: Optional[str] = None  # e.g., "2.1"
    title: str
    content: str  # HTML or Markdown
    subsections: List['SectionContent'] = []

    # Content sources
    source_blocks: List[UUID] = []  # From content library
    generated: bool = False  # Was this AI-generated?
    generation_metadata: Optional[Dict[str, Any]] = None

    # Quality
    quality_score: Optional[float] = None
    reviewed: bool = False

    created_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# AI GENERATION
# ============================================================================

class GenerationRequest(BaseModel):
    """Request to generate section content."""
    section_type: str  # 'methodology', 'hypotheses', etc.
    project_context: Dict[str, Any]
    company_knowledge: Dict[str, Any]
    template: Optional[str] = None
    requirements: Optional[Dict[str, Any]] = None

class GeneratedContent(BaseModel):
    """Result of AI content generation."""
    section_type: str
    content: str
    quality_score: float
    generation_metadata: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.now)

# ============================================================================
# DOCUMENT GENERATION
# ============================================================================

class StyleConfig(BaseModel):
    """Configuration for document styling."""
    template_name: str  # 'agency', 'professional', 'minimal'
    primary_color: str  # Hex color
    secondary_color: str
    font_heading: str = 'Arial'
    font_body: str = 'Arial'
    image_width: float = 6.5  # inches
    include_company_logo: bool = True
    include_certifications: bool = True

class DocumentGenerationRequest(BaseModel):
    """Request to generate final document."""
    project_id: UUID
    sections: List[UUID]  # Section IDs to include
    style_config: StyleConfig
    annexes: List[UUID] = []  # File IDs to attach as annexes
    format: str = 'docx'  # or 'pdf'

class DocumentGenerationResult(BaseModel):
    """Result of document generation."""
    document_url: str  # S3/Blob URL
    format: str
    size_bytes: int
    page_count: int
    generated_at: datetime = Field(default_factory=datetime.now)
    qa_report: Optional['QAReport'] = None

class QAReport(BaseModel):
    """Quality assurance report for generated document."""
    passed: bool
    issues: List[str] = []
    stats: Dict[str, Any] = {}
    checked_at: datetime = Field(default_factory=datetime.now)

# Update forward references
ContentBlock.update_forward_refs()
SectionContent.update_forward_refs()
```

**Why Pydantic:**

- **Type safety:** Catches errors at development time
- **Validation:** Ensures data integrity
- **Documentation:** Models serve as API documentation
- **Serialization:** Easy JSON conversion for API responses
- **ORM integration:** Works with SQLAlchemy/databases

---

## 6. Technology Stack Decisions

### Backend

**Framework: FastAPI**

**Why FastAPI:**

- ✅ **Performance:** Async support, fast (comparable to Node.js)
- ✅ **Type Safety:** Built on Pydantic, catches errors early
- ✅ **Auto Documentation:** Swagger/OpenAPI docs generated automatically
- ✅ **Modern Python:** Async/await, type hints, latest Python features
- ✅ **WebSocket Support:** For real-time progress updates
- ✅ **Dependency Injection:** Clean architecture patterns

**Alternatives Considered:**

- Django: Too heavy, not async-first
- Flask: Too minimal, would need many extensions
- Express (Node.js): Team knows Python better, AI libraries better in Python

**Database: PostgreSQL**

**Why PostgreSQL:**

- ✅ **JSONB:** Flexible metadata storage
- ✅ **Full-text Search:** Built-in search capabilities
- ✅ **Array Types:** For tags, relationships
- ✅ **Mature:** Battle-tested, reliable
- ✅ **Good Python Support:** psycopg2, SQLAlchemy
- ✅ **Performance:** Handles concurrent access well

**Alternatives Considered:**

- MongoDB: Less structured, no ACID guarantees
- MySQL: Weaker JSON support
- SQLite: Not suitable for production multi-user

**File Storage: AWS S3 (or Azure Blob)**

**Why S3:**

- ✅ **Scalability:** Unlimited storage
- ✅ **Reliability:** 99.999999999% durability
- ✅ **Performance:** CDN integration
- ✅ **Cost:** Pay for what you use
- ✅ **Security:** Fine-grained access control

**Cache: Redis**

**Why Redis:**

- ✅ **Speed:** In-memory, microsecond latency
- ✅ **Versatility:** Cache, session store, rate limiting
- ✅ **Pub/Sub:** For real-time notifications
- ✅ **Persistence:** Optional durability

### Frontend

**Framework: Next.js (React)**

**Why Next.js:**

- ✅ **React Ecosystem:** Huge component library
- ✅ **SSR/SSG:** Better performance, SEO
- ✅ **TypeScript:** Type safety end-to-end
- ✅ **API Routes:** Can handle simple backend logic
- ✅ **File Upload:** Good libraries (react-dropzone)
- ✅ **Modern:** Latest React features

**UI Library: Tailwind CSS + shadcn/ui**

**Why This Combo:**

- ✅ **Tailwind:** Utility-first, fast development
- ✅ **shadcn/ui:** Beautiful components, customizable
- ✅ **Consistency:** Design system out of the box
- ✅ **Accessibility:** Components follow best practices

### AI Services

**Primary: Claude API (Anthropic)**

**Why Claude:**

- ✅ **French Language:** Excellent French understanding
- ✅ **Long Context:** 200K tokens = can process entire RC
- ✅ **Document Analysis:** Strong at extracting structured info
- ✅ **Quality:** High-quality French text generation
- ✅ **Structured Output:** Can return JSON

**Secondary: GPT-4 (OpenAI)**

**Why GPT-4:**

- ✅ **Versatility:** Good all-around performance
- ✅ **Function Calling:** Clean API for structured output
- ✅ **Availability:** More reliable uptime
- ✅ **Fallback:** Use if Claude unavailable

**Strategy:** Use Claude by default, GPT-4 as fallback

### Document Processing

**PDF: PyPDF2 + pdfplumber**

**Why:**

- ✅ **PyPDF2:** Text extraction, metadata
- ✅ **pdfplumber:** Better table extraction
- ✅ **Together:** Cover all PDF parsing needs

**Word: python-docx**

**Why:**

- ✅ **Most Mature:** 10+ years of development
- ✅ **Feature Complete:** All Word features we need
- ✅ **Active:** Regular updates
- ✅ **Well Documented:** Many examples

**Alternatives Considered:**

- docxtpl: Too template-focused
- pywin32: Windows-only, brittle
- mammoth: Read-only

### Deployment

**Container: Docker**

**Why Docker:**

- ✅ **Consistency:** Same environment everywhere
- ✅ **Isolation:** Dependencies contained
- ✅ **Scalability:** Easy to scale horizontally

**Orchestration: Kubernetes (or Docker Swarm for simpler start)**

**Why:**

- ✅ **Scaling:** Auto-scale based on load
- ✅ **Reliability:** Auto-restart failed containers
- ✅ **Updates:** Zero-downtime deployments

**CI/CD: GitHub Actions**

**Why:**

- ✅ **Integrated:** Built into GitHub
- ✅ **Free:** For private repos
- ✅ **Flexible:** Can do anything
- ✅ **Simple:** YAML configuration

### Monitoring & Logging

**Application Monitoring: Sentry**

**Why:**

- ✅ **Error Tracking:** Catch bugs in production
- ✅ **Performance:** Identify slow endpoints
- ✅ **Alerts:** Notify when issues occur

**Logging: Python logging + CloudWatch/DataDog**

**Why:**

- ✅ **Structured Logging:** JSON logs
- ✅ **Searchable:** Find issues quickly
- ✅ **Retention:** Keep logs for analysis

**Metrics: Prometheus + Grafana**

**Why:**

- ✅ **Time Series:** Track metrics over time
- ✅ **Dashboards:** Visualize system health
- ✅ **Alerts:** Set up threshold alerts

---

### Development Tools

**Code Quality:**

- **Black:** Code formatting
- **Flake8:** Linting
- **MyPy:** Type checking
- **Pytest:** Testing

**Why These:**

- ✅ **Standard:** Industry standard Python tools
- ✅ **Automated:** Can run in CI/CD
- ✅ **Strict:** Catch errors early

---

## 7. AI Integration Strategy

### Model Selection Matrix

| Task                   | Primary Model | Fallback      | Reasoning                  |
| ---------------------- | ------------- | ------------- | -------------------------- |
| RC Analysis            | Claude Sonnet | GPT-4         | French docs, long context  |
| Content Matching       | Claude Sonnet | GPT-4         | Semantic understanding     |
| Methodology Generation | Claude Opus   | Claude Sonnet | Long-form, quality writing |
| Hypotheses Generation  | GPT-4         | Claude Sonnet | Shorter, formulaic         |
| Quality Assessment     | Claude Sonnet | GPT-4         | Evaluation task            |
| Section Improvement    | Claude Opus   | Claude Sonnet | Writing refinement         |

### Prompt Engineering Strategy

```python
class PromptLibrary:
    """
    Centralized prompt management.

    Why centralized:
    - Easy to version and A/B test prompts
    - Consistent across codebase
    - Can track which prompts work best
    """

    def __init__(self):
        self.prompts = self._load_prompts()
        self.prompt_history = {}  # Track performance

    def get_prompt(
        self,
        prompt_name: str,
        variables: Dict[str, Any]
    ) -> str:
        """
        Get a prompt template and fill in variables.

        Why templating: Reuse prompt structure, just change context
        """
        template = self.prompts.get(prompt_name)
        if not template:
            raise ValueError(f"Prompt '{prompt_name}' not found")

        # Fill in variables
        prompt = template.format(**variables)

        # Track usage
        self.prompt_history[prompt_name] = self.prompt_history.get(prompt_name, 0) + 1

        return prompt

    def _load_prompts(self) -> Dict[str, str]:
        """Load prompt templates from files."""
        return {
            'rc_analysis': """
You are analyzing a French construction consultation regulation (Règlement de Consultation).

DOCUMENT:
{document_text}

Extract structured information about technical memoir requirements.

Return JSON with:
- requiredSections: array of {{id, title, description, points, requirements}}
- scoringCriteria: object mapping section to points
- specialRequirements: array of strings
- format: "free" or "imposed"
- deadline: ISO datetime string

Be thorough. Extract all scoring criteria from the document.
""",

            'methodology_generation': """
You are writing the "ORGANISATION DU CHANTIER, MÉTHODOLOGIE DES TRAVAUX" section for a French construction technical memoir.

PROJECT:
{project_context}

COMPANY APPROACH:
{company_standard_approach}

REQUIREMENTS:
{rc_requirements}

SCORING (optimize for this):
{scoring_criteria}

Write a comprehensive methodology section (3000-4000 words) in French.
Structure with numbered subsections.
Be specific: mention equipment names, techniques, measurements.
Include {{{{IMAGE: description}}}} placeholders.
Use formal construction industry terminology.

Begin:
""",

            'quality_assessment': """
Assess the quality of this construction memoir section on a scale of 0.0 to 1.0.

SECTION TYPE: {section_type}
EXPECTED LENGTH: {expected_length} words
SCORING CRITERIA: {scoring_criteria}

CONTENT:
{content}

Evaluate:
1. Completeness (addresses all requirements)
2. Specificity (concrete details vs. vague statements)
3. Technical accuracy
4. Language quality (grammar, terminology)
5. Optimization for scoring criteria

Return only a number between 0.0 and 1.0
""",

            # ... more prompts
        }
```

### Rate Limiting & Cost Management

```python
class AIServiceManager:
    """
    Manage AI API calls with rate limiting and cost tracking.

    Why needed:
    - AI APIs are expensive
    - Rate limits must be respected
    - Need to track costs per project
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.rate_limits = {
            'claude': {
                'requests_per_minute': 50,
                'tokens_per_minute': 100000
            },
            'gpt4': {
                'requests_per_minute': 60,
                'tokens_per_minute': 150000
            }
        }

    async def call_ai(
        self,
        model: str,
        prompt: str,
        project_id: UUID,
        **kwargs
    ) -> AIResponse:
        """
        Call AI API with rate limiting and cost tracking.
        """
        # Check rate limit
        await self._check_rate_limit(model)

        # Estimate cost before calling
        estimated_tokens = len(prompt.split()) * 1.3  # Rough estimate
        estimated_cost = self._estimate_cost(model, estimated_tokens)

        # Call API
        start_time = time.time()
        response = await self._call_api(model, prompt, **kwargs)
        elapsed = time.time() - start_time

        # Track actual cost
        actual_cost = self._calculate_cost(
            model,
            response.input_tokens,
            response.output_tokens
        )

        # Store metrics
        await self._record_usage(
            project_id=project_id,
            model=model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=actual_cost,
            latency=elapsed
        )

        return response

    async def _check_rate_limit(self, model: str):
        """
        Check and enforce rate limits.

        Why: Avoid hitting API limits, spreading usage over time
        """
        limits = self.rate_limits[model]
        current_minute = int(time.time() / 60)

        # Check requests per minute
        key_requests = f"rate_limit:{model}:requests:{current_minute}"
        current_requests = await self.redis.incr(key_requests)
        await self.redis.expire(key_requests, 60)

        if current_requests > limits['requests_per_minute']:
            # Wait until next minute
            wait_time = 60 - (time.time() % 60)
            raise RateLimitError(f"Rate limit exceeded, retry in {wait_time:.0f}s")

        # Check tokens per minute (similar logic)
        # ...

    def _estimate_cost(self, model: str, estimated_tokens: int) -> float:
        """
        Estimate cost before API call.

        Why: Budget control, can show user estimated cost
        """
        pricing = {
            'claude-opus': {
                'input': 15.00 / 1_000_000,  # $ per token
                'output': 75.00 / 1_000_000
            },
            'claude-sonnet': {
                'input': 3.00 / 1_000_000,
                'output': 15.00 / 1_000_000
            },
            'gpt-4': {
                'input': 30.00 / 1_000_000,
                'output': 60.00 / 1_000_000
            }
        }

        rates = pricing[model]
        # Assume output is 50% of input (rough estimate)
        return (estimated_tokens * rates['input'] +
                estimated_tokens * 0.5 * rates['output'])

    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate actual cost after API call."""
        # (same pricing as _estimate_cost)
        pricing = {...}  # same as above
        rates = pricing[model]
        return (input_tokens * rates['input'] +
                output_tokens * rates['output'])

    async def _record_usage(
        self,
        project_id: UUID,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency: float
    ):
        """
        Record AI usage for analytics and billing.

        Why: Track costs per project, identify expensive projects
        """
        await db.ai_usage.insert({
            'project_id': project_id,
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_usd': cost,
            'latency_seconds': latency,
            'timestamp': datetime.now()
        })
```

### Retry Logic & Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class ResilientAIClient:
    """AI client with automatic retries and fallbacks."""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True
    )
    async def generate_with_retry(
        self,
        prompt: str,
        primary_model: str,
        fallback_model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate content with automatic retries.

        Why retry logic:
        - AI APIs can be flaky (timeout, rate limit, etc.)
        - Don't fail entire memoir generation for one error
        - Exponential backoff prevents hammering API
        """
        try:
            # Try primary model
response = await self._call_model(primary_model, prompt, **kwargs)
            return response

        except RateLimitError as e:
            logger.warning(f"Rate limit hit on {primary_model}, waiting...")
            raise  # Let tenacity handle retry with backoff

        except APIError as e:
            logger.error(f"API error on {primary_model}: {e}")

            # Try fallback model if available
            if fallback_model:
                logger.info(f"Trying fallback model: {fallback_model}")
                try:
                    response = await self._call_model(fallback_model, prompt, **kwargs)
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    raise e  # Raise original error
            else:
                raise

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def _call_model(
        self,
        model: str,
        prompt: str,
        **kwargs
    ) -> str:
        """Actual API call implementation."""
        if model.startswith('claude'):
            return await self._call_claude(model, prompt, **kwargs)
        elif model.startswith('gpt'):
            return await self._call_openai(model, prompt, **kwargs)
        else:
            raise ValueError(f"Unknown model: {model}")
```
