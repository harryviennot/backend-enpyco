# Task 08: WebSocket Service for Real-Time Updates

## Overview
Implement WebSocket connections to provide real-time progress updates during long-running operations (RC analysis, content matching, AI generation, document generation).

## Current State
- No real-time updates
- Users must poll for status

## Goal
WebSocket-based real-time updates for:
- RC analysis progress
- Content matching progress
- AI content generation (section by section)
- Document generation progress
- Error notifications
- Completion notifications

## Technology Choice

FastAPI WebSockets with connection management

## Components to Implement

### 1. WebSocket Manager
```python
# services/websocket_manager.py

from fastapi import WebSocket
from typing import Dict, List
from uuid import UUID
import json
from datetime import datetime

class ConnectionManager:
    def __init__(self):
        # Store active connections by project_id
        self.active_connections: Dict[UUID, List[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        project_id: UUID,
        user_id: UUID
    ):
        """
        Accept WebSocket connection for a project.

        Authenticate user and verify project access.
        """
        await websocket.accept()

        if project_id not in self.active_connections:
            self.active_connections[project_id] = []

        self.active_connections[project_id].append(websocket)

    def disconnect(
        self,
        websocket: WebSocket,
        project_id: UUID
    ):
        """Remove connection"""
        if project_id in self.active_connections:
            self.active_connections[project_id].remove(websocket)

            # Clean up empty project lists
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket
    ):
        """Send message to specific connection"""
        await websocket.send_json(message)

    async def broadcast_to_project(
        self,
        project_id: UUID,
        message: dict
    ):
        """
        Broadcast message to all connections watching a project.

        Used for progress updates that all users should see.
        """
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"Error broadcasting to connection: {e}")
                    # Connection broken, will be cleaned up on disconnect

# Global instance
connection_manager = ConnectionManager()
```

### 2. Progress Update Service
```python
# services/progress_updater.py

from uuid import UUID
from typing import Optional
from datetime import datetime

class ProgressUpdater:
    def __init__(self, connection_manager):
        self.manager = connection_manager

    async def send_rc_analysis_progress(
        self,
        project_id: UUID,
        status: str,
        progress: int,
        message: str
    ):
        """Send RC analysis progress update"""
        await self.manager.broadcast_to_project(project_id, {
            "type": "rc_analysis_progress",
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_matching_progress(
        self,
        project_id: UUID,
        current_requirement: str,
        requirements_completed: int,
        requirements_total: int,
        progress: int
    ):
        """Send content matching progress"""
        await self.manager.broadcast_to_project(project_id, {
            "type": "matching_progress",
            "current_requirement": current_requirement,
            "requirements_completed": requirements_completed,
            "requirements_total": requirements_total,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_generation_progress(
        self,
        project_id: UUID,
        current_section: str,
        sections_completed: int,
        sections_total: int,
        progress: int,
        quality_score: Optional[float] = None
    ):
        """Send AI generation progress"""
        await self.manager.broadcast_to_project(project_id, {
            "type": "generation_progress",
            "current_section": current_section,
            "sections_completed": sections_completed,
            "sections_total": sections_total,
            "progress": progress,
            "quality_score": quality_score,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_document_generation_progress(
        self,
        project_id: UUID,
        status: str,
        progress: int,
        message: str
    ):
        """Send document generation progress"""
        await self.manager.broadcast_to_project(project_id, {
            "type": "document_generation_progress",
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_error(
        self,
        project_id: UUID,
        operation: str,
        error_message: str
    ):
        """Send error notification"""
        await self.manager.broadcast_to_project(project_id, {
            "type": "error",
            "operation": operation,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        })

    async def send_completion(
        self,
        project_id: UUID,
        operation: str,
        result: dict
    ):
        """Send completion notification"""
        await self.manager.broadcast_to_project(project_id, {
            "type": "completion",
            "operation": operation,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
```

### 3. WebSocket Authentication
```python
# dependencies/websocket_auth.py

from fastapi import WebSocket, HTTPException, status
from urllib.parse import parse_qs
import jwt

async def authenticate_websocket(
    websocket: WebSocket,
    project_id: UUID
) -> User:
    """
    Authenticate WebSocket connection.

    Extracts JWT token from query parameters:
    ws://api/ws/projects/{project_id}?token=<jwt>
    """
    # Extract token from query params
    query_string = websocket.scope.get("query_string", b"").decode()
    query_params = parse_qs(query_string)
    token = query_params.get("token", [None])[0]

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        # Decode JWT
        payload = decode_token(token)
        user_id = payload.get("sub")

        # Fetch user
        user = await db.users.get(user_id)
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=401, detail="Invalid user")

        # Verify project access
        project = await db.projects.get(project_id)
        if project.company_id != user.company_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            raise HTTPException(status_code=403, detail="Access denied")

        return user

    except jwt.ExpiredSignatureError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception as e:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        raise HTTPException(status_code=500, detail=str(e))
```

## WebSocket Endpoints

```python
# routers/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from uuid import UUID

router = APIRouter()

@router.websocket("/ws/projects/{project_id}")
async def project_updates(
    websocket: WebSocket,
    project_id: UUID
):
    """
    WebSocket endpoint for project updates.

    Sends real-time updates for:
    - RC analysis
    - Content matching
    - AI generation
    - Document generation

    Connection URL:
    ws://api/ws/projects/{project_id}?token=<jwt>
    """
    # Authenticate
    user = await authenticate_websocket(websocket, project_id)

    # Connect
    await connection_manager.connect(
        websocket,
        project_id,
        user.id
    )

    try:
        # Keep connection alive and handle client messages
        while True:
            # Receive messages (for heartbeat or client commands)
            data = await websocket.receive_text()

            # Handle ping/pong for keep-alive
            if data == "ping":
                await websocket.send_text("pong")

            # Handle other client messages if needed
            # (e.g., cancel operation, request status)

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, project_id)
        print(f"Client disconnected from project {project_id}")

@router.websocket("/ws/notifications")
async def user_notifications(websocket: WebSocket):
    """
    WebSocket endpoint for user-level notifications.

    Sends notifications across all projects for a user.
    """
    # Similar to project updates but user-scoped
    pass
```

## Integration with Services

### Update RC Analyzer
```python
# services/rc_analyzer.py

class RCAnalyzer:
    def __init__(self, claude_client, progress_updater):
        self.claude = claude_client
        self.progress = progress_updater

    async def analyze_rc(self, rc_pdf_path: str, project_id: UUID) -> RCAnalysis:
        # Send progress: Starting
        await self.progress.send_rc_analysis_progress(
            project_id,
            status="extracting_text",
            progress=10,
            message="Extracting text from PDF..."
        )

        # Extract text
        text = self._extract_text(rc_pdf_path)

        # Send progress: Analyzing
        await self.progress.send_rc_analysis_progress(
            project_id,
            status="analyzing",
            progress=40,
            message="Analyzing document with AI..."
        )

        # Call Claude API
        analysis = await self._call_claude_api(text)

        # Send progress: Completing
        await self.progress.send_rc_analysis_progress(
            project_id,
            status="completed",
            progress=100,
            message="Analysis complete!"
        )

        return analysis
```

### Update Content Matcher
```python
# services/content_matcher.py

class ContentMatcher:
    def __init__(self, db, claude_client, progress_updater):
        self.db = db
        self.claude = claude_client
        self.progress = progress_updater

    async def match_requirements(
        self,
        project_id: UUID,
        company_id: UUID
    ) -> List[ContentMatch]:
        requirements = await self._get_requirements(project_id)
        total = len(requirements)

        for i, req in enumerate(requirements):
            # Send progress
            await self.progress.send_matching_progress(
                project_id,
                current_requirement=req.title,
                requirements_completed=i,
                requirements_total=total,
                progress=int((i / total) * 100)
            )

            # Perform matching
            match = await self._match_requirement(req, company_id)

        # Send completion
        await self.progress.send_matching_progress(
            project_id,
            current_requirement="Complete",
            requirements_completed=total,
            requirements_total=total,
            progress=100
        )
```

### Update AI Generator
```python
# services/ai_generator.py

class AIContentGenerator:
    def __init__(self, claude_client, rag_service, progress_updater):
        self.claude = claude_client
        self.rag = rag_service
        self.progress = progress_updater

    async def generate_sections(
        self,
        project_id: UUID,
        section_types: List[GenerationSectionType],
        company_id: UUID
    ):
        total = len(section_types)

        for i, section_type in enumerate(section_types):
            # Send progress
            await self.progress.send_generation_progress(
                project_id,
                current_section=section_type.value,
                sections_completed=i,
                sections_total=total,
                progress=int((i / total) * 100)
            )

            # Generate section
            content = await self.generate_section(
                project_id,
                section_type,
                company_id
            )

            # Send quality score
            await self.progress.send_generation_progress(
                project_id,
                current_section=section_type.value,
                sections_completed=i + 1,
                sections_total=total,
                progress=int(((i + 1) / total) * 100),
                quality_score=content.quality_score
            )
```

## Client-Side Implementation Example

```typescript
// Frontend WebSocket client

class ProjectWebSocket {
  private ws: WebSocket | null = null;
  private projectId: string;
  private token: string;

  constructor(projectId: string, token: string) {
    this.projectId = projectId;
    this.token = token;
  }

  connect(onMessage: (data: any) => void) {
    const url = `ws://api/ws/projects/${this.projectId}?token=${this.token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      // Send periodic ping to keep alive
      setInterval(() => {
        this.ws?.send('ping');
      }, 30000); // Every 30 seconds
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      // Implement reconnection logic
    };
  }

  disconnect() {
    this.ws?.close();
  }
}

// Usage
const ws = new ProjectWebSocket(projectId, accessToken);
ws.connect((data) => {
  switch (data.type) {
    case 'rc_analysis_progress':
      updateProgressBar(data.progress);
      updateStatusMessage(data.message);
      break;

    case 'generation_progress':
      updateGenerationUI(data);
      break;

    case 'completion':
      handleOperationComplete(data.operation, data.result);
      break;

    case 'error':
      showErrorNotification(data.error);
      break;
  }
});
```

## Implementation Steps

1. Create `services/websocket_manager.py` for connection management
2. Create `services/progress_updater.py` for sending updates
3. Create `dependencies/websocket_auth.py` for authentication
4. Create `routers/websocket.py` with WebSocket endpoints
5. Update all long-running services to send progress
6. Add WebSocket routes to main.py
7. Test connection handling and message broadcasting
8. Test reconnection logic
9. Document WebSocket API for frontend

## Testing Checklist

- [ ] WebSocket connection established successfully
- [ ] JWT authentication works via query params
- [ ] Multi-tenant isolation (users only see their projects)
- [ ] RC analysis sends progress updates
- [ ] Content matching sends progress updates
- [ ] AI generation sends progress updates
- [ ] Document generation sends progress updates
- [ ] Multiple clients can connect to same project
- [ ] Disconnection handled gracefully
- [ ] Error messages sent via WebSocket
- [ ] Completion notifications sent
- [ ] Heartbeat/ping-pong keeps connection alive
- [ ] Connection cleanup on disconnect

## Error Handling

```python
# Robust error handling in services

try:
    # Perform operation
    result = await some_operation()

    # Send success
    await progress.send_completion(project_id, "operation", result)

except Exception as e:
    # Send error
    await progress.send_error(
        project_id,
        operation="operation_name",
        error_message=str(e)
    )

    # Re-raise for logging
    raise
```

## Performance Considerations

- Keep connection alive with ping/pong (every 30 seconds)
- Limit message size (compress large payloads if needed)
- Clean up disconnected connections promptly
- Use connection pooling for database queries
- Implement reconnection logic on client side

## Dependencies
- Task 01 (Database Schema)
- Task 02 (Authentication)
- FastAPI WebSockets
- Redis (optional, for multi-instance pub/sub)

## Estimated Effort
**2-3 days**

## Success Criteria
- Real-time progress updates for all long operations
- Stable WebSocket connections
- Proper authentication and authorization
- Graceful error handling
- Connection cleanup on disconnect
- <100ms message latency

## Future Enhancements
- Redis pub/sub for multi-instance deployments
- WebSocket clustering
- Message compression for large payloads
- Client-side message queuing for offline support
- WebSocket analytics and monitoring
