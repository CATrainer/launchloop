# Production Fixes Implementation Plan

Based on audit findings, here's the systematic fix plan with code changes required.

---

## Critical Fixes - Implementation Details

### CRITICAL-1: Implement Structured Logging

**Files to modify:**
- Create: `backend/app/utils/logger.py`
- Modify: All files using `print()`

**Implementation:**
```python
# app/utils/logger.py
import logging
import sys
from app.config import settings

def setup_logger(name: str) -> logging.Logger:
    """Setup structured logger"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Usage:
# from app.utils.logger import setup_logger
# logger = setup_logger(__name__)
# logger.info("Message", extra={"user_id": user_id, "project_id": project_id})
```

**Effort:** 3-4 hours (replace all print statements)

---

### CRITICAL-2: Fix Database Session Management

**Files to modify:**
- `backend/app/middleware/auth.py`
- `backend/app/middleware/rate_limit.py`
- `backend/app/tasks/generation.py`
- `backend/app/database.py`

**Changes:**

1. **Remove last_active_at from every request:**
```python
# middleware/auth.py - REMOVE these lines:
user.last_active_at = datetime.utcnow()
db.commit()

# Instead: Update via background task every 5 minutes or batch
```

2. **Add connection pooling config:**
```python
# database.py
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)
```

3. **Fix rate limiting:**
```python
# middleware/rate_limit.py
def check_rate_limit(identifier: str, action: str, ...):
    # Use FastAPI's Depends(get_db) pattern instead of SessionLocal()
    # Pass db as parameter
```

**Effort:** 2-3 hours

---

### CRITICAL-3: Add Generation Retry Logic

**Files to modify:**
- `backend/app/tasks/generation.py`
- `backend/app/services/generation.py`

**Implementation:**
```python
# tasks/generation.py
@celery_app.task(
    base=GenerationTask,
    bind=True,
    time_limit=600,  # 10 minutes
    soft_time_limit=540,
    max_retries=3,  # Add retry
    default_retry_delay=60  # Wait 60s between retries
)
def process_generation(self, generation_id: str, db=None):
    try:
        # ... generation logic ...
    except (APIError, RateLimitError, TimeoutError) as exc:
        # Transient errors - retry
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
    except Exception as e:
        # Permanent errors - fail immediately
        generation_service.update_generation_progress(
            db, generation_id, GenerationStatus.FAILED, 0, str(e)
        )
        # REFUND USER CREDIT
        refund_user_credit(db, generation_id)
        raise

def refund_user_credit(db, generation_id):
    """Refund user credit on failure"""
    generation = db.query(Generation).get(generation_id)
    user = generation.project.user
    if generation.type == GenerationType.NEW:
        user.generations_used_this_month = max(0, user.generations_used_this_month - 1)
    else:
        user.revisions_used_this_month = max(0, user.revisions_used_this_month - 1)
    db.commit()
```

**Effort:** 2-3 hours

---

### CRITICAL-4: Add Email Validation

**Files to modify:**
- `backend/app/utils/validators.py`
- `backend/app/api/auth.py`
- `backend/app/api/signups.py`

**Implementation:**
```python
# utils/validators.py
import re
from email_validator import validate_email, EmailNotValidError

def validate_email_address(email: str) -> tuple[bool, str]:
    """Validate email format and optionally DNS"""
    try:
        # Basic format check
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False, "Invalid email format"
        
        # More thorough validation
        validated = validate_email(email, check_deliverability=False)
        return True, validated.email
    except EmailNotValidError as e:
        return False, str(e)

# Usage in endpoints:
is_valid, error_or_email = validate_email_address(signup_data.email)
if not is_valid:
    raise HTTPException(400, detail=f"Invalid email: {error_or_email}")
```

**Dependencies:** `pip install email-validator`

**Effort:** 1-2 hours

---

### CRITICAL-5: Track Actual API Costs

**Files to modify:**
- `backend/app/services/llm.py`
- `backend/app/services/images.py`
- `backend/app/tasks/generation.py`

**Implementation:**
```python
# services/llm.py
def generate_copy(self, ...) -> tuple[Dict[str, Any], float]:
    """Returns (generated_copy, cost)"""
    message = self.client.messages.create(...)
    
    # Calculate cost from usage
    # Claude: $15/1M input tokens, $75/1M output tokens
    input_cost = (message.usage.input_tokens / 1_000_000) * 15
    output_cost = (message.usage.output_tokens / 1_000_000) * 75
    total_cost = input_cost + output_cost
    
    return generated_copy, total_cost

# services/images.py
def generate_images(self, ...) -> tuple[list, float]:
    """Returns (images, total_cost)"""
    # DALL-E 3: $0.04 per 1024x1024 image
    cost_per_image = 0.04
    total_cost = len(images) * cost_per_image
    return images, total_cost

# tasks/generation.py
generated_copy, llm_cost = llm_service.generate_copy(...)
images, image_cost = image_service.generate_images(...)

generation_service.complete_generation(
    ...,
    llm_cost=llm_cost,
    image_cost=image_cost
)
```

**Effort:** 2-3 hours

---

### CRITICAL-6: Add Rate Limiting to Generation

**Files to modify:**
- `backend/app/api/generate.py`
- `backend/app/middleware/rate_limit.py`

**Implementation:**
```python
# api/generate.py
@router.post("", response_model=GenerationResponse)
async def create_generation(
    request: Request,
    ...
):
    # Add rate limiting
    check_rate_limit(
        user.id,
        "generation",
        max_count=3,  # 3 generations
        window_minutes=60  # per hour
    )
    
    # Rest of logic...
```

**Effort:** 1 hour

---

### CRITICAL-7: Cache Subdomain Lookups

**Files to modify:**
- `backend/app/middleware/subdomain.py`
- `backend/app/services/cache.py` (new)

**Implementation:**
```python
# services/cache.py
import redis
from app.config import settings
import json

redis_client = redis.from_url(settings.REDIS_URL)

def cache_project_html(subdomain: str, html: str, ttl: int = 3600):
    """Cache project HTML"""
    redis_client.setex(f"project:subdomain:{subdomain}", ttl, html)

def get_cached_project_html(subdomain: str) -> str | None:
    """Get cached project HTML"""
    cached = redis_client.get(f"project:subdomain:{subdomain}")
    return cached.decode() if cached else None

def invalidate_project_cache(subdomain: str):
    """Clear cache when project updated"""
    redis_client.delete(f"project:subdomain:{subdomain}")

# middleware/subdomain.py
async def subdomain_middleware(request: Request, call_next):
    # ... extract subdomain ...
    
    # Check cache first
    html = get_cached_project_html(subdomain)
    if html:
        return HTMLResponse(content=html)
    
    # Cache miss - hit database
    db = SessionLocal()
    try:
        project = db.query(Project).filter(...).first()
        if project and project.html_content:
            cache_project_html(subdomain, project.html_content)
            return HTMLResponse(content=project.html_content)
    finally:
        db.close()
    
    return await call_next(request)
```

**Effort:** 2-3 hours

---

### CRITICAL-8: Sanitize All User Input

**Files to modify:**
- `backend/app/utils/validators.py`
- `backend/app/services/generation.py`
- All API endpoints

**Implementation:**
```python
# utils/validators.py
import bleach
from markupsafe import escape

def sanitize_html_input(text: str) -> str:
    """Remove all HTML tags"""
    return bleach.clean(text, tags=[], strip=True)

def sanitize_text_input(text: str, max_length: int = 10000) -> str:
    """Sanitize plain text input"""
    if not text:
        return ""
    text = text[:max_length]
    text = text.replace('\x00', '')
    text = text.replace('\r\n', '\n')
    return text.strip()

def escape_for_html(text: str) -> str:
    """Escape HTML special characters"""
    return escape(text)

# services/generation.py - Use proper templating
def assemble_html(self, template_html: str, generated_copy: Dict, images: list) -> str:
    """Assemble with proper escaping"""
    from jinja2 import Template
    
    template = Template(template_html, autoescape=True)
    return template.render(
        **{k: escape_for_html(str(v)) for k, v in generated_copy.items()},
        images={img['id']: img.get('r2_url', '/placeholder.png') for img in images}
    )
```

**Dependencies:** `pip install bleach jinja2`

**Effort:** 3-4 hours

---

## High Priority Fixes - Summary

### HIGH-1: Refund Credits on Failure
- Already included in CRITICAL-3

### HIGH-2: Transaction Management
```python
# Use context manager for transactions
with db.begin():
    # All operations here
    # Automatically commits on success, rolls back on exception
```
**Effort:** 2 hours

### HIGH-3: Extend Celery Timeout
```python
@celery_app.task(time_limit=600, soft_time_limit=540)  # 10 minutes
```
**Effort:** 5 minutes

### HIGH-4: Real Health Checks
```python
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    checks = {
        "database": False,
        "redis": False,
        "celery": False,
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except:
        pass
    
    # Check Redis
    try:
        redis_client.ping()
        checks["redis"] = True
    except:
        pass
    
    # Check Celery
    try:
        result = celery_app.control.inspect().active()
        checks["celery"] = result is not None
    except:
        pass
    
    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503
    
    return JSONResponse(
        status_code=status_code,
        content={"status": "healthy" if all_healthy else "unhealthy", "checks": checks}
    )
```
**Effort:** 1 hour

### HIGH-5: Clean Error Messages
```python
# Create error handler
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Don't expose internal details
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."}
    )
```
**Effort:** 1-2 hours

### HIGH-6: Idempotency on Generation
```python
# Check for pending generation before creating new one
pending = db.query(Generation).filter(
    Generation.project_id == project_id,
    Generation.status.in_([GenerationStatus.PENDING, GenerationStatus.ANALYZING, ...])
).first()

if pending:
    return pending  # Return existing pending generation
```
**Effort:** 1 hour

### HIGH-7: Storage Error Handling
```python
def upload_image(self, image_data: bytes, ...) -> str:
    try:
        self.client.put_object(...)
        return url
    except ClientError as e:
        logger.error(f"Failed to upload image: {e}")
        raise StorageException(f"Upload failed: {e.response['Error']['Message']}")
```
**Effort:** 1 hour

### HIGH-8: Set Up Monitoring
- Sentry already configured
- Add to all exception handlers
- Add performance tracking
**Effort:** 2 hours

### HIGH-9: Secure Cookies
- Already using secure=True, httponly=True
- Add domain restriction in production
**Effort:** 30 minutes

---

## Total Implementation Time

| Priority | Time Estimate |
|----------|---------------|
| Critical (8 issues) | 16-22 hours (2-3 days) |
| High (9 issues) | 10-13 hours (1-2 days) |
| **Total** | **26-35 hours (3-5 days)** |

---

## Implementation Order

### Day 1 (8 hours)
1. ✅ Logging system (4 hours)
2. ✅ Database session fixes (2 hours)
3. ✅ Email validation (1 hour)
4. ✅ Rate limiting (1 hour)

### Day 2 (8 hours)
5. ✅ Generation retry + credit refunds (3 hours)
6. ✅ Input sanitization (3 hours)
7. ✅ Track actual costs (2 hours)

### Day 3 (8 hours)
8. ✅ Subdomain caching (3 hours)
9. ✅ Transaction management (2 hours)
10. ✅ Health checks (1 hour)
11. ✅ Error handling (2 hours)

### Day 4-5 (8-16 hours)
12. ✅ Remaining High priority items
13. ✅ Testing all fixes
14. ✅ Documentation updates

---

## Testing Plan

For each fix:
1. **Unit test** the changed code
2. **Integration test** in staging
3. **Load test** critical paths
4. **Verify logs** are working
5. **Check monitoring** alerts

---

**Ready to implement. Awaiting your approval to proceed.**
