# Task 09: Project Workflow Orchestration

## Overview
Build the orchestration layer that manages the entire memoir generation workflow from project creation through final document export, including state management, error recovery, and user review cycles.

## Current State
- Individual services exist (RC analysis, matching, generation, document)
- No unified workflow management
- No state machine for project status

## Goal
Complete workflow orchestration with:
- Project state machine (draft → submitted)
- Automatic workflow progression
- Manual intervention points
- Error recovery and retry
- Workflow status tracking
- Background job management

## Project Workflow States

```python
class ProjectStatus(str, Enum):
    DRAFT = "draft"                        # Created, no RC uploaded
    RC_UPLOADED = "rc_uploaded"            # RC uploaded, not analyzed
    RC_ANALYZING = "rc_analyzing"          # RC analysis in progress
    RC_ANALYZED = "rc_analyzed"            # RC analysis complete
    MATCHING = "matching"                   # Content matching in progress
    MATCHED = "matched"                     # Matches ready for review
    CUSTOMIZING = "customizing"             # User customizing matches
    MATCH_APPROVED = "match_approved"       # Matches approved, ready for generation
    GENERATING = "generating"               # AI generating sections
    GENERATED = "generated"                 # Sections generated, ready for review
    REVIEWING = "reviewing"                 # User reviewing/editing sections
    BUILDING_DOCUMENT = "building_document" # Assembling Word document
    DOCUMENT_READY = "document_ready"       # Document ready for download
    COMPLETED = "completed"                 # User marked as complete
    SUBMITTED = "submitted"                 # Submitted to client
    FAILED = "failed"                       # Error state
```

## Services to Implement

### 1. Workflow Orchestrator
```python
# services/workflow_orchestrator.py

from typing import Optional, Dict
from uuid import UUID

class WorkflowOrchestrator:
    def __init__(
        self,
        db,
        rc_analyzer,
        content_matcher,
        ai_generator,
        document_generator,
        progress_updater
    ):
        self.db = db
        self.rc_analyzer = rc_analyzer
        self.matcher = content_matcher
        self.generator = ai_generator
        self.doc_gen = document_generator
        self.progress = progress_updater

    async def start_rc_analysis(
        self,
        project_id: UUID,
        rc_file_url: str
    ):
        """
        Start RC analysis workflow step.

        State transition: rc_uploaded → rc_analyzing → rc_analyzed
        """
        try:
            # Update status
            await self.db.projects.update(project_id, {
                "status": ProjectStatus.RC_ANALYZING
            })

            # Run analysis
            analysis = await self.rc_analyzer.analyze_rc(rc_file_url, project_id)

            # Update status
            await self.db.projects.update(project_id, {
                "status": ProjectStatus.RC_ANALYZED
            })

            # Auto-trigger next step?
            # await self.start_content_matching(project_id)

        except Exception as e:
            await self._handle_error(project_id, "rc_analysis", e)

    async def start_content_matching(
        self,
        project_id: UUID
    ):
        """
        Start content matching workflow step.

        State transition: rc_analyzed → matching → matched
        """
        try:
            await self.db.projects.update(project_id, {
                "status": ProjectStatus.MATCHING
            })

            # Get company_id
            project = await self.db.projects.get(project_id)

            # Run matching
            matches = await self.matcher.match_requirements(
                project_id,
                project.company_id
            )

            await self.db.projects.update(project_id, {
                "status": ProjectStatus.MATCHED
            })

        except Exception as e:
            await self._handle_error(project_id, "matching", e)

    async def approve_matches(
        self,
        project_id: UUID
    ):
        """
        User approves matches.

        State transition: matched → match_approved

        Ready for AI generation.
        """
        await self.db.projects.update(project_id, {
            "status": ProjectStatus.MATCH_APPROVED
        })

        # Auto-trigger generation
        await self.start_generation(project_id)

    async def start_generation(
        self,
        project_id: UUID,
        sections_to_generate: Optional[List[str]] = None
    ):
        """
        Start AI content generation.

        State transition: match_approved → generating → generated
        """
        try:
            await self.db.projects.update(project_id, {
                "status": ProjectStatus.GENERATING
            })

            project = await self.db.projects.get(project_id)

            # Determine sections to generate
            if not sections_to_generate:
                # Get from matches marked as needs_generation
                matches = await self.db.content_matches.find({
                    "project_id": project_id,
                    "needs_generation": True
                })
                sections_to_generate = [m.requirement_id for m in matches]

            # Generate sections
            await self.generator.generate_sections(
                project_id,
                sections_to_generate,
                project.company_id
            )

            await self.db.projects.update(project_id, {
                "status": ProjectStatus.GENERATED
            })

        except Exception as e:
            await self._handle_error(project_id, "generation", e)

    async def regenerate_section(
        self,
        project_id: UUID,
        section_id: UUID,
        instructions: Optional[str] = None
    ):
        """
        Regenerate a specific section with user feedback.

        Does not change project status.
        """
        # Get section
        section = await self.db.sections.get(section_id)

        # Regenerate
        new_content = await self.generator.regenerate_section(
            section,
            instructions
        )

        # Update section
        await self.db.sections.update(section_id, {
            "content": new_content.content,
            "quality_score": new_content.quality_score,
            "version": section.version + 1
        })

    async def approve_sections(
        self,
        project_id: UUID
    ):
        """
        User approves all sections.

        State transition: generated → reviewing → approved

        Ready for document generation.
        """
        await self.db.projects.update(project_id, {
            "status": ProjectStatus.REVIEWING
        })

        # Auto-trigger document generation
        await self.start_document_generation(project_id)

    async def start_document_generation(
        self,
        project_id: UUID,
        config: Optional[DocumentConfig] = None
    ):
        """
        Generate final Word document.

        State transition: reviewing → building_document → document_ready
        """
        try:
            await self.db.projects.update(project_id, {
                "status": ProjectStatus.BUILDING_DOCUMENT
            })

            project = await self.db.projects.get(project_id)

            # Generate document
            doc_url = await self.doc_gen.generate_memoir(
                project_id,
                project.company_id,
                config
            )

            # Update project
            await self.db.projects.update(project_id, {
                "status": ProjectStatus.DOCUMENT_READY,
                "final_document_url": doc_url
            })

        except Exception as e:
            await self._handle_error(project_id, "document_generation", e)

    async def mark_completed(
        self,
        project_id: UUID
    ):
        """
        User marks project as completed.

        State transition: document_ready → completed
        """
        await self.db.projects.update(project_id, {
            "status": ProjectStatus.COMPLETED,
            "completed_at": datetime.utcnow()
        })

    async def mark_submitted(
        self,
        project_id: UUID,
        submission_details: Dict
    ):
        """
        User marks as submitted to client.

        State transition: completed → submitted
        """
        await self.db.projects.update(project_id, {
            "status": ProjectStatus.SUBMITTED,
            "submitted_at": datetime.utcnow(),
            "submission_details": submission_details
        })

    async def _handle_error(
        self,
        project_id: UUID,
        operation: str,
        error: Exception
    ):
        """Handle workflow errors"""
        # Log error
        print(f"Error in {operation} for project {project_id}: {error}")

        # Update status
        await self.db.projects.update(project_id, {
            "status": ProjectStatus.FAILED,
            "error_details": {
                "operation": operation,
                "error": str(error),
                "timestamp": datetime.utcnow().isoformat()
            }
        })

        # Send error notification
        await self.progress.send_error(
            project_id,
            operation,
            str(error)
        )

    async def retry_failed_operation(
        self,
        project_id: UUID
    ):
        """
        Retry failed operation.

        Looks at error_details to determine what failed.
        """
        project = await self.db.projects.get(project_id)

        if project.status != ProjectStatus.FAILED:
            raise ValueError("Project is not in failed state")

        operation = project.error_details.get("operation")

        # Clear error state
        await self.db.projects.update(project_id, {
            "error_details": None
        })

        # Retry appropriate operation
        if operation == "rc_analysis":
            await self.start_rc_analysis(project_id, project.rc_file_url)
        elif operation == "matching":
            await self.start_content_matching(project_id)
        elif operation == "generation":
            await self.start_generation(project_id)
        elif operation == "document_generation":
            await self.start_document_generation(project_id)
```

### 2. Background Job Queue (Optional, using Celery or FastAPI BackgroundTasks)
```python
# services/background_jobs.py

from fastapi import BackgroundTasks

class JobQueue:
    """
    Manage background jobs for long-running operations.

    Simple implementation using FastAPI BackgroundTasks.
    For production, consider Celery with Redis.
    """

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    async def enqueue_rc_analysis(
        self,
        background_tasks: BackgroundTasks,
        project_id: UUID,
        rc_file_url: str
    ):
        """Enqueue RC analysis job"""
        background_tasks.add_task(
            self.orchestrator.start_rc_analysis,
            project_id,
            rc_file_url
        )

    async def enqueue_matching(
        self,
        background_tasks: BackgroundTasks,
        project_id: UUID
    ):
        """Enqueue content matching job"""
        background_tasks.add_task(
            self.orchestrator.start_content_matching,
            project_id
        )

    async def enqueue_generation(
        self,
        background_tasks: BackgroundTasks,
        project_id: UUID,
        sections: Optional[List[str]] = None
    ):
        """Enqueue AI generation job"""
        background_tasks.add_task(
            self.orchestrator.start_generation,
            project_id,
            sections
        )

    async def enqueue_document_generation(
        self,
        background_tasks: BackgroundTasks,
        project_id: UUID,
        config: Optional[DocumentConfig] = None
    ):
        """Enqueue document generation job"""
        background_tasks.add_task(
            self.orchestrator.start_document_generation,
            project_id,
            config
        )
```

## API Endpoints

```python
# routers/workflow.py

@router.post("/api/projects/{project_id}/workflow/analyze-rc")
async def trigger_rc_analysis(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Trigger RC analysis workflow step"""
    project = await db.projects.get(project_id)

    if not project.rc_storage_path:
        raise HTTPException(400, "No RC file uploaded")

    await job_queue.enqueue_rc_analysis(
        background_tasks,
        project_id,
        project.rc_storage_path
    )

    return {"message": "RC analysis started", "project_id": str(project_id)}

@router.post("/api/projects/{project_id}/workflow/match-content")
async def trigger_content_matching(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Trigger content matching workflow step"""
    await job_queue.enqueue_matching(background_tasks, project_id)
    return {"message": "Content matching started"}

@router.post("/api/projects/{project_id}/workflow/approve-matches")
async def approve_matches(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Approve matches and trigger generation"""
    await orchestrator.approve_matches(project_id)
    return {"message": "Matches approved, generation starting"}

@router.post("/api/projects/{project_id}/workflow/generate")
async def trigger_generation(
    project_id: UUID,
    config: GenerationConfig,
    background_tasks: BackgroundTasks,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Trigger AI generation workflow step"""
    await job_queue.enqueue_generation(
        background_tasks,
        project_id,
        config.sections_to_generate
    )
    return {"message": "Generation started"}

@router.post("/api/projects/{project_id}/workflow/build-document")
async def trigger_document_build(
    project_id: UUID,
    config: DocumentConfig,
    background_tasks: BackgroundTasks,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Trigger document generation"""
    await job_queue.enqueue_document_generation(
        background_tasks,
        project_id,
        config
    )
    return {"message": "Document generation started"}

@router.post("/api/projects/{project_id}/workflow/complete")
async def mark_project_complete(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Mark project as completed"""
    await orchestrator.mark_completed(project_id)
    return {"message": "Project marked as completed"}

@router.post("/api/projects/{project_id}/workflow/submit")
async def mark_project_submitted(
    project_id: UUID,
    submission: ProjectSubmission,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Mark project as submitted to client"""
    await orchestrator.mark_submitted(
        project_id,
        submission.dict()
    )
    return {"message": "Project marked as submitted"}

@router.post("/api/projects/{project_id}/workflow/retry")
async def retry_failed_workflow(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.PROJECT_WRITE))
):
    """Retry failed workflow step"""
    await orchestrator.retry_failed_operation(project_id)
    return {"message": "Retrying failed operation"}

@router.get("/api/projects/{project_id}/workflow/status")
async def get_workflow_status(
    project_id: UUID,
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(get_current_user)
) -> WorkflowStatus:
    """Get current workflow status"""
    project = await db.projects.get(project_id)

    return WorkflowStatus(
        status=project.status,
        current_step=_get_current_step(project.status),
        next_action=_get_next_action(project.status),
        can_proceed=_can_proceed(project),
        error=project.error_details
    )
```

## Pydantic Models

```python
# models/workflow.py

class WorkflowStatus(BaseModel):
    status: ProjectStatus
    current_step: str
    next_action: Optional[str]
    can_proceed: bool
    error: Optional[Dict]

class ProjectSubmission(BaseModel):
    submitted_to: str
    submission_date: datetime
    submission_method: str  # email, platform, physical
    notes: Optional[str]
```

## State Transition Validation

```python
# utils/state_machine.py

VALID_TRANSITIONS = {
    ProjectStatus.DRAFT: [ProjectStatus.RC_UPLOADED],
    ProjectStatus.RC_UPLOADED: [ProjectStatus.RC_ANALYZING],
    ProjectStatus.RC_ANALYZING: [ProjectStatus.RC_ANALYZED, ProjectStatus.FAILED],
    ProjectStatus.RC_ANALYZED: [ProjectStatus.MATCHING],
    ProjectStatus.MATCHING: [ProjectStatus.MATCHED, ProjectStatus.FAILED],
    ProjectStatus.MATCHED: [ProjectStatus.CUSTOMIZING, ProjectStatus.MATCH_APPROVED],
    ProjectStatus.CUSTOMIZING: [ProjectStatus.MATCHED, ProjectStatus.MATCH_APPROVED],
    ProjectStatus.MATCH_APPROVED: [ProjectStatus.GENERATING],
    ProjectStatus.GENERATING: [ProjectStatus.GENERATED, ProjectStatus.FAILED],
    ProjectStatus.GENERATED: [ProjectStatus.REVIEWING, ProjectStatus.BUILDING_DOCUMENT],
    ProjectStatus.REVIEWING: [ProjectStatus.GENERATED, ProjectStatus.BUILDING_DOCUMENT],
    ProjectStatus.BUILDING_DOCUMENT: [ProjectStatus.DOCUMENT_READY, ProjectStatus.FAILED],
    ProjectStatus.DOCUMENT_READY: [ProjectStatus.COMPLETED, ProjectStatus.BUILDING_DOCUMENT],
    ProjectStatus.COMPLETED: [ProjectStatus.SUBMITTED],
    ProjectStatus.FAILED: [ProjectStatus.RC_ANALYZING, ProjectStatus.MATCHING, ProjectStatus.GENERATING, ProjectStatus.BUILDING_DOCUMENT]
}

def can_transition(from_status: ProjectStatus, to_status: ProjectStatus) -> bool:
    """Check if state transition is valid"""
    return to_status in VALID_TRANSITIONS.get(from_status, [])

def validate_transition(project: Project, new_status: ProjectStatus):
    """Raise exception if invalid transition"""
    if not can_transition(project.status, new_status):
        raise ValueError(
            f"Invalid state transition: {project.status} → {new_status}"
        )
```

## Implementation Steps

1. Create `services/workflow_orchestrator.py` with main workflow logic
2. Create `services/background_jobs.py` for job queuing
3. Create `utils/state_machine.py` for state validation
4. Create `routers/workflow.py` with workflow endpoints
5. Create Pydantic models in `models/workflow.py`
6. Integrate orchestrator with existing services
7. Add state transition validation
8. Test complete workflow end-to-end
9. Add error recovery and retry logic
10. Document workflow for frontend integration

## Testing Checklist

- [ ] Can create project (draft state)
- [ ] Can upload RC (rc_uploaded state)
- [ ] RC analysis transitions states correctly
- [ ] Content matching transitions states correctly
- [ ] Match approval triggers generation
- [ ] Generation transitions states correctly
- [ ] Section regeneration works without status change
- [ ] Document generation transitions correctly
- [ ] Can mark as completed
- [ ] Can mark as submitted
- [ ] Failed operations can be retried
- [ ] Invalid state transitions rejected
- [ ] Background jobs execute correctly
- [ ] WebSocket updates sent during workflow
- [ ] Multi-tenant isolation enforced

## Error Recovery

- Failed RC analysis: Retry with same file
- Failed matching: Clear matches and retry
- Failed generation: Retry individual sections
- Failed document: Rebuild from sections

## Dependencies
- Task 01-07 (All previous services)
- Task 08 (WebSocket for progress)
- FastAPI BackgroundTasks or Celery

## Estimated Effort
**3-4 days**

## Success Criteria
- Complete workflow from draft to submitted
- Automatic progression where appropriate
- Manual intervention points work
- Error recovery and retry functional
- State machine prevents invalid transitions
- Background jobs execute reliably

## Future Enhancements
- Workflow templates (fast-track for similar projects)
- Approval chains (multi-user review)
- Scheduled operations (generate at specific time)
- Workflow analytics (bottleneck identification)
- Parallel project processing
- Workflow rollback (undo state changes)
