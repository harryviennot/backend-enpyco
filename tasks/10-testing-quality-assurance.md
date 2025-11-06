# Task 10: Comprehensive Testing & Quality Assurance

## Overview
Implement comprehensive testing strategy covering unit tests, integration tests, end-to-end tests, and quality assurance processes.

## Current State
- No test suite
- No CI/CD pipeline
- Manual testing only

## Goal
Production-ready testing infrastructure with:
- Unit tests (>80% coverage)
- Integration tests for APIs
- End-to-end workflow tests
- Load testing
- Security testing
- CI/CD pipeline with automated testing

## Testing Strategy

### 1. Unit Tests (pytest)
```python
# tests/unit/test_rc_analyzer.py

import pytest
from services.rc_analyzer import RCAnalyzer

@pytest.fixture
def rc_analyzer():
    return RCAnalyzer(mock_claude_client)

def test_extract_text_from_pdf(rc_analyzer, sample_rc_pdf):
    text = rc_analyzer._extract_text(sample_rc_pdf)
    assert len(text) > 1000
    assert "Règlement de Consultation" in text

def test_find_scoring_section(rc_analyzer, sample_rc_text):
    scoring = rc_analyzer._find_scoring_section(sample_rc_text)
    assert "Critères de jugement" in scoring or "Notation" in scoring

def test_validate_analysis(rc_analyzer, mock_analysis_data):
    validated = rc_analyzer._validate_analysis(mock_analysis_data)
    assert validated.project_info is not None
    assert len(validated.required_sections) > 0
```

```python
# tests/unit/test_content_matcher.py

def test_rule_based_matching(content_matcher, presentation_requirement):
    match = await content_matcher._rule_based_match(
        presentation_requirement,
        company_id
    )
    assert match is not None
    assert match.confidence > 0.8
    assert len(match.matched_blocks) > 0

def test_confidence_calculation(content_matcher):
    confidence = content_matcher._calculate_confidence(
        requirement, blocks, "rule-based"
    )
    assert 0.0 <= confidence <= 1.0
```

```python
# tests/unit/test_ai_generator.py

def test_prompt_building(ai_generator):
    prompt = ai_generator._build_prompt(
        SectionType.METHODOLOGY,
        context,
        requirement
    )
    assert "MÉTHODOLOGIE DES TRAVAUX" in prompt
    assert str(requirement.points) in prompt

def test_quality_check_length(quality_assessor):
    short_content = "This is too short."
    score, issues = quality_assessor._check_length(
        short_content,
        SectionType.METHODOLOGY
    )
    assert score < 0.7
    assert len(issues) > 0
```

### 2. Integration Tests
```python
# tests/integration/test_api_endpoints.py

@pytest.mark.asyncio
async def test_create_content_block(async_client, auth_headers):
    response = await async_client.post(
        "/api/content-blocks",
        json={
            "type": "company-profile",
            "title": "Test Company Profile",
            "content": "Company description...",
            "tags": ["company", "test"]
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Company Profile"

@pytest.mark.asyncio
async def test_rc_analysis_workflow(async_client, auth_headers, sample_rc_file):
    # Upload RC
    response = await async_client.post(
        f"/api/projects/{project_id}/upload-rc",
        files={"file": sample_rc_file},
        headers=auth_headers
    )
    assert response.status_code == 200

    # Start analysis
    response = await async_client.post(
        f"/api/projects/{project_id}/analyze-rc",
        headers=auth_headers
    )
    assert response.status_code == 200

    # Poll status
    for _ in range(30):  # Wait up to 30 seconds
        response = await async_client.get(
            f"/api/projects/{project_id}/analysis/status",
            headers=auth_headers
        )
        status = response.json()["status"]
        if status == "completed":
            break
        await asyncio.sleep(1)

    assert status == "completed"

    # Get results
    response = await async_client.get(
        f"/api/projects/{project_id}/analysis",
        headers=auth_headers
    )
    assert response.status_code == 200
    analysis = response.json()
    assert len(analysis["required_sections"]) > 0
```

### 3. End-to-End Tests
```python
# tests/e2e/test_complete_workflow.py

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_memoir_generation(
    async_client,
    test_company,
    test_user,
    sample_rc_file
):
    """Test complete workflow from project creation to document download"""

    # 1. Create project
    response = await async_client.post(
        "/api/projects",
        json={"name": "Test Project", "client": "Test Client"},
        headers=auth_headers
    )
    project_id = response.json()["id"]

    # 2. Upload and analyze RC
    # ... (upload RC file)
    await wait_for_analysis_complete(project_id)

    # 3. Populate content library
    await create_sample_content_blocks(test_company.id)

    # 4. Match content
    response = await async_client.post(
        f"/api/projects/{project_id}/workflow/match-content",
        headers=auth_headers
    )
    await wait_for_matching_complete(project_id)

    # 5. Approve matches
    response = await async_client.post(
        f"/api/projects/{project_id}/workflow/approve-matches",
        headers=auth_headers
    )

    # 6. Wait for generation
    await wait_for_generation_complete(project_id)

    # 7. Build document
    response = await async_client.post(
        f"/api/projects/{project_id}/workflow/build-document",
        headers=auth_headers
    )
    await wait_for_document_ready(project_id)

    # 8. Download document
    response = await async_client.get(
        f"/api/projects/{project_id}/document/download",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # 9. Validate document
    doc_bytes = response.content
    assert len(doc_bytes) > 10000  # Reasonable document size
    # Could also open with python-docx and validate structure
```

### 4. Load Testing (Locust)
```python
# tests/load/locustfile.py

from locust import HttpUser, task, between

class MemoirUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Login before tests"""
        response = self.client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "testpassword"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def list_projects(self):
        self.client.get(
            "/api/projects",
            headers=self.headers
        )

    @task(2)
    def list_content_blocks(self):
        self.client.get(
            "/api/content-blocks",
            headers=self.headers
        )

    @task(1)
    def create_content_block(self):
        self.client.post(
            "/api/content-blocks",
            json={
                "type": "company-profile",
                "title": f"Test Block {random.randint(1, 1000)}",
                "content": "Test content",
                "tags": ["test"]
            },
            headers=self.headers
        )

# Run with: locust -f tests/load/locustfile.py --host=http://localhost:8000
```

### 5. Security Testing
```python
# tests/security/test_auth.py

def test_unauthenticated_access_blocked(client):
    """Verify endpoints require authentication"""
    endpoints = [
        "/api/projects",
        "/api/content-blocks",
        "/api/users"
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401

def test_multi_tenant_isolation(client, user1_token, user2_token):
    """Verify users can't access other companies' data"""

    # User 1 creates project
    response = client.post(
        "/api/projects",
        json={"name": "User 1 Project"},
        headers={"Authorization": f"Bearer {user1_token}"}
    )
    project_id = response.json()["id"]

    # User 2 (different company) tries to access
    response = client.get(
        f"/api/projects/{project_id}",
        headers={"Authorization": f"Bearer {user2_token}"}
    )
    assert response.status_code in [403, 404]

def test_sql_injection_protection(client, auth_headers):
    """Verify SQL injection is prevented"""
    malicious_input = "'; DROP TABLE users; --"

    response = client.post(
        "/api/content-blocks/search",
        json={"query": malicious_input},
        headers=auth_headers
    )

    # Should return safely (empty or error, but not crash)
    assert response.status_code in [200, 400]

    # Verify database still intact
    response = client.get("/api/users", headers=auth_headers)
    assert response.status_code == 200
```

## Test Fixtures

```python
# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app
from services.supabase import get_db

@pytest.fixture
def client():
    """Synchronous test client"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """Async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def test_company(db):
    """Create test company"""
    company = db.companies.insert({
        "name": "Test Company",
        "address": "123 Test St",
        "city": "Test City",
        "postal_code": "12345",
        "phone": "0123456789",
        "email": "test@company.com"
    })
    yield company
    db.companies.delete(company.id)

@pytest.fixture
def test_user(db, test_company):
    """Create test user"""
    user = db.users.insert({
        "company_id": test_company.id,
        "email": "user@test.com",
        "password_hash": hash_password("testpass"),
        "full_name": "Test User",
        "role": "admin"
    })
    yield user
    db.users.delete(user.id)

@pytest.fixture
def auth_headers(test_user):
    """Authentication headers"""
    token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_rc_pdf():
    """Sample RC PDF file"""
    return open("tests/fixtures/sample_rc.pdf", "rb")

@pytest.fixture
def mock_claude_client():
    """Mock Claude API client"""
    class MockClaude:
        async def analyze_document(self, prompt, **kwargs):
            return json.dumps({
                "project_info": {...},
                "required_sections": [...],
                # ... mock response
            })
    return MockClaude()
```

## CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/test.yml

name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: memoir_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          black --check .
          flake8 .
          mypy .

      - name: Run unit tests
        run: |
          pytest tests/unit -v --cov=services --cov=routers --cov-report=xml

      - name: Run integration tests
        run: |
          pytest tests/integration -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  e2e:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run E2E tests
        run: |
          pytest tests/e2e -v -m e2e
        env:
          CLAUDE_API_KEY: ${{ secrets.CLAUDE_API_KEY_TEST }}
```

## Test Data Management

```python
# tests/fixtures/data_factory.py

class DataFactory:
    """Factory for creating test data"""

    @staticmethod
    def create_rc_analysis(project_id: UUID, **overrides):
        """Create test RC analysis"""
        default = {
            "project_id": project_id,
            "rc_file_url": "s3://test/rc.pdf",
            "project_info": {
                "name": "Test Project",
                "client": "Test Client",
                "location": "Test Location",
                "deadline": "2024-12-31T12:00:00Z"
            },
            "required_sections": [
                {
                    "id": "presentation",
                    "title": "Présentation de l'entreprise",
                    "points": 10,
                    "requirements": ["Company history", "Certifications"]
                }
            ],
            "scoring_criteria": {"total": 100}
        }
        return {**default, **overrides}

    @staticmethod
    def create_content_block(company_id: UUID, **overrides):
        """Create test content block"""
        default = {
            "company_id": company_id,
            "type": "company-profile",
            "title": "Test Company Profile",
            "content": "Test content",
            "tags": ["test"],
            "is_active": True
        }
        return {**default, **overrides}
```

## Implementation Steps

1. Set up pytest and testing infrastructure
2. Create test fixtures and utilities
3. Write unit tests for all services
4. Write integration tests for API endpoints
5. Write E2E tests for complete workflows
6. Set up GitHub Actions CI/CD
7. Configure code coverage reporting
8. Set up load testing with Locust
9. Implement security tests
10. Document testing procedures

## Testing Checklist

### Unit Tests
- [ ] RC Analyzer (PDF extraction, Claude API, validation)
- [ ] Content Matcher (rule-based, AI semantic, confidence)
- [ ] AI Generator (prompt building, quality checks)
- [ ] Word Generator (document assembly, formatting)
- [ ] Authentication (password hashing, JWT)
- [ ] Permissions (RBAC, multi-tenancy)

### Integration Tests
- [ ] Auth endpoints (login, register, refresh)
- [ ] Content library CRUD
- [ ] RC analysis API
- [ ] Content matching API
- [ ] Generation API
- [ ] Document generation API
- [ ] WebSocket connections

### E2E Tests
- [ ] Complete memoir generation workflow
- [ ] Error recovery and retry
- [ ] Multi-user collaboration
- [ ] Document customization and regeneration

### Load Tests
- [ ] 100 concurrent users
- [ ] Sustained load (1 hour)
- [ ] API response times <200ms (p95)
- [ ] Document generation <1 min under load

### Security Tests
- [ ] Authentication required for all endpoints
- [ ] Multi-tenant isolation enforced
- [ ] SQL injection prevented
- [ ] XSS prevented
- [ ] CSRF protection
- [ ] Rate limiting

## Coverage Goals

- Overall code coverage: >80%
- Critical paths (workflow): >95%
- Services: >85%
- API routers: >80%

## Dependencies
- pytest
- pytest-asyncio
- pytest-cov
- httpx (async client)
- locust (load testing)
- black, flake8, mypy (linting)

## Estimated Effort
**4-5 days**

## Success Criteria
- >80% code coverage
- All critical paths tested
- CI/CD pipeline running
- Load tests passing
- Security tests passing
- Zero critical bugs

## Future Enhancements
- Visual regression testing
- Performance benchmarking
- Chaos engineering tests
- Contract testing for APIs
- Mutation testing
