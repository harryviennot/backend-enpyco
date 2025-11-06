# Task 02: Authentication & Authorization System

## Overview
Implement JWT-based authentication with multi-tenant support and role-based access control (RBAC).

## Current State
- No authentication system
- No user management
- Open API endpoints

## Goal
Secure API with:
- User registration and login
- JWT token generation and validation
- Role-based permissions
- Multi-tenant data isolation
- Session management

## Components to Implement

### 1. Password Hashing
```python
# utils/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### 2. JWT Token Management
```python
# utils/auth.py
import jwt
from datetime import datetime, timedelta
from typing import Optional

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
```

### 3. Authentication Dependencies
```python
# dependencies/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Fetch user from database
        user = await db.users.get(user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_active_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user
```

### 4. Multi-Tenant Middleware
```python
# middleware/tenant.py
from fastapi import Request, HTTPException
from typing import Optional

class TenantMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract user from token
        user = getattr(request.state, "user", None)

        # Add company_id to request state for easy access
        if user:
            request.state.company_id = user.company_id

        response = await call_next(request)
        return response

# Dependency for enforcing tenant isolation
async def get_company_id(user: User = Depends(get_current_user)) -> UUID:
    return user.company_id
```

### 5. Permission System
```python
# utils/permissions.py
from enum import Enum
from typing import List

class Permission(str, Enum):
    # Content library
    CONTENT_READ = "content:read"
    CONTENT_WRITE = "content:write"
    CONTENT_DELETE = "content:delete"

    # Projects
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"

    # Users (admin only)
    USER_MANAGE = "user:manage"

    # Company settings (admin only)
    COMPANY_SETTINGS = "company:settings"

ROLE_PERMISSIONS = {
    "admin": [p for p in Permission],  # All permissions
    "user": [
        Permission.CONTENT_READ,
        Permission.CONTENT_WRITE,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
    ],
    "viewer": [
        Permission.CONTENT_READ,
        Permission.PROJECT_READ,
    ]
}

def check_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.role, [])

def require_permission(permission: Permission):
    async def permission_checker(user: User = Depends(get_current_user)):
        if not check_permission(user, permission):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {permission.value}"
            )
        return user
    return permission_checker
```

## API Endpoints to Implement

### 1. Authentication Routes
```python
# routers/auth.py

@router.post("/auth/register")
async def register_company(
    company_data: CompanyRegistration
) -> RegisterResponse:
    """Register new company with first admin user"""
    # Create company
    # Create admin user
    # Return access + refresh tokens

@router.post("/auth/login")
async def login(credentials: LoginCredentials) -> TokenResponse:
    """Login user and return JWT tokens"""
    # Verify email/password
    # Generate access + refresh tokens
    # Update last_login timestamp
    # Log audit event

@router.post("/auth/refresh")
async def refresh_token(refresh_token: str) -> TokenResponse:
    """Get new access token using refresh token"""
    # Validate refresh token
    # Generate new access token
    # Return tokens

@router.post("/auth/logout")
async def logout(user: User = Depends(get_current_user)):
    """Logout user (optional: blacklist token)"""
    # Log audit event
    # Optionally add token to blacklist in Redis

@router.get("/auth/me")
async def get_current_user_info(
    user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current user information"""
    return user
```

### 2. User Management Routes (Admin Only)
```python
# routers/users.py

@router.get("/api/users")
async def list_users(
    company_id: UUID = Depends(get_company_id),
    user: User = Depends(require_permission(Permission.USER_MANAGE))
) -> List[User]:
    """List all users in company"""

@router.post("/api/users")
async def create_user(
    user_data: UserCreate,
    company_id: UUID = Depends(get_company_id),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE))
) -> User:
    """Create new user in company"""

@router.patch("/api/users/{user_id}")
async def update_user(
    user_id: UUID,
    updates: UserUpdate,
    company_id: UUID = Depends(get_company_id),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE))
) -> User:
    """Update user (role, active status, etc.)"""

@router.delete("/api/users/{user_id}")
async def delete_user(
    user_id: UUID,
    company_id: UUID = Depends(get_company_id),
    current_user: User = Depends(require_permission(Permission.USER_MANAGE))
):
    """Deactivate user"""
```

### 3. Audit Logging
```python
# utils/audit.py

async def log_audit_event(
    action: str,
    user_id: Optional[UUID],
    resource_type: str,
    resource_id: Optional[UUID],
    details: dict,
    request: Request
):
    """Log audit event to database"""
    await db.audit_log.insert({
        "action": action,
        "user_id": user_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "details": details,
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        "timestamp": datetime.utcnow()
    })
```

## Pydantic Models

```python
# models/auth.py

class LoginCredentials(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60

class CompanyRegistration(BaseModel):
    company_name: str
    address: str
    city: str
    postal_code: str
    phone: str
    email: str
    admin_name: str
    admin_email: str
    admin_password: str = Field(min_length=8)

class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str = Field(min_length=8)
    role: str = "user"

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
```

## Environment Variables

Add to `.env`:
```bash
JWT_SECRET_KEY=<generate-secure-random-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Implementation Steps

1. Install dependencies: `passlib[bcrypt]`, `python-jose[cryptography]`
2. Create `utils/security.py` for password hashing
3. Create `utils/auth.py` for JWT token management
4. Create `dependencies/auth.py` for FastAPI dependencies
5. Create `middleware/tenant.py` for multi-tenant isolation
6. Create `utils/permissions.py` for RBAC
7. Create `routers/auth.py` with auth endpoints
8. Create `routers/users.py` with user management
9. Create `utils/audit.py` for audit logging
10. Update `main.py` to include auth routes and middleware
11. Protect existing routes with `Depends(get_current_user)`

## Testing Checklist

- [ ] User can register new company
- [ ] User can login with email/password
- [ ] JWT tokens are generated correctly
- [ ] Access token expires after configured time
- [ ] Refresh token works to get new access token
- [ ] Invalid tokens are rejected (401)
- [ ] Expired tokens are rejected (401)
- [ ] Users can only access their company's data
- [ ] Admin can create/manage users
- [ ] Regular users cannot access admin endpoints (403)
- [ ] Viewers have read-only access
- [ ] Audit log captures all authentication events
- [ ] Password is hashed in database (never plain text)

## Dependencies
- Task 01 (Database Schema Migration) must be completed
- `passlib[bcrypt]` for password hashing
- `python-jose[cryptography]` for JWT
- Redis (optional, for token blacklisting)

## Estimated Effort
**3-4 days**

## Success Criteria
- Secure JWT-based authentication working
- Multi-tenant isolation enforced at API level
- Role-based access control implemented
- All endpoints protected with authentication
- Audit logging for security events
- Comprehensive test coverage

## Security Considerations
- Use strong SECRET_KEY (256-bit random)
- Hash passwords with bcrypt (cost factor 12)
- Validate password strength on registration
- Implement rate limiting on login endpoint
- Use HTTPS in production
- Set secure HTTP-only cookies for tokens (if using cookies)
- Implement token refresh rotation
- Log all authentication events
