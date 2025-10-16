# 🚨 Critical: Celery Worker Not Running

## The Problem

Your generation is stuck because **the Celery worker service is not running**.

Looking at your Railway logs, I see:
- ✅ Backend API is running (handles HTTP requests)
- ❌ Celery worker is NOT running (doesn't process background tasks)

**Evidence:**
- Generation task queued at `18:47:12`
- Frontend polls for status every 2 seconds
- No Celery logs showing task processing
- Generation stays at 0% or low progress forever
- Task never completes

## Why This Happens

The Celery worker is a **separate service** from your backend API. They both use the same codebase but run different commands:

- **Backend**: `uvicorn app.main:app`
- **Celery Worker**: `celery -A app.tasks.celery worker`

In Railway, you need **TWO services**:
1. `backend` - Your API (already running)
2. `worker` - Celery worker (MISSING)

## How to Fix in Railway

### Option 1: Add Worker Service (Recommended)

1. **In Railway Dashboard:**
   - Go to your project
   - Click "New Service"
   - Connect to same GitHub repo
   - Name it "worker"

2. **Set Start Command:**
   ```bash
   celery -A app.tasks.celery worker --loglevel=info
   ```

3. **Copy Environment Variables:**
   - Copy ALL env vars from `backend` service to `worker` service
   - Especially: DATABASE_URL, REDIS_URL, ANTHROPIC_API_KEY, OPENAI_API_KEY, R2 credentials

4. **Set Service Variables:**
   ```
   SERVICE_NAME=worker
   PYTHON_VERSION=3.11
   ```

5. **Deploy**
   - Worker will start automatically
   - Check logs to verify it's running

6. **Look for These Logs:**
   ```
   [2025-10-16 ...] celery@worker ready.
   [2025-10-16 ...] celery.worker.strategy ...
   ```

### Option 2: Quick Test with Railway CLI

**If you have Railway CLI installed:**

```bash
# Open a new terminal
railway run celery -A app.tasks.celery worker --loglevel=info

# Keep this running in background
```

This will process tasks temporarily but won't persist after you close terminal.

### Option 3: Combined Service (Not Recommended for Production)

You can run both in one service using a process manager:

**Create `Procfile`:**
```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.tasks.celery worker --loglevel=info
```

**Install Honcho:**
```bash
pip install honcho
```

**Update Railway start command:**
```bash
honcho start
```

⚠️ This works but Railway prefers separate services for better scaling and monitoring.

## Verify Worker is Running

Once worker is deployed, test generation again:

1. Create new project
2. Generate landing page
3. Check Railway logs for **both services**:

**Backend logs should show:**
```
INFO: POST /api/v1/generate HTTP/1.1 202 Accepted
🔍 RAW Generation request body: {...}
```

**Worker logs should show:**
```
[2025-10-16 ...] Task app.tasks.generation.process_generation[...] received
[2025-10-16 ...] 📊 Starting generation for project: ...
[2025-10-16 ...] Status: ANALYZING (10%)
[2025-10-16 ...] Status: GENERATING_COPY (20%)
[2025-10-16 ...] Calling Claude API for copy generation...
[2025-10-16 ...] Status: GENERATING_IMAGES (40%)
[2025-10-16 ...] Calling DALL-E for 4 images...
[2025-10-16 ...] Status: ASSEMBLING (85%)
[2025-10-16 ...] Status: COMPLETE (100%)
[2025-10-16 ...] Task app.tasks.generation.process_generation[...] succeeded
```

## How to Check Current Worker Status

### In Railway Dashboard:
1. Go to your project
2. Click "Services" tab
3. Look for service named "worker" or "celery"
4. Check if it's deployed and running

### Using Railway CLI:
```bash
railway list

# Should show something like:
# - backend (running)
# - frontend (running)  
# - worker (running) ← This should exist!
```

### Check Redis Connection:
Worker needs Redis for task queue. Verify Redis is connected:

```bash
railway variables

# Should see:
# REDIS_URL=redis://...
```

## Troubleshooting Worker Issues

### Worker Starts But Crashes:
**Check logs for:**
- Missing environment variables
- Redis connection failed
- Import errors
- Permission issues

**Common fixes:**
- Ensure all env vars are set
- Check Redis is provisioned
- Verify Python packages installed

### Worker Runs But Doesn't Process Tasks:
**Check:**
1. Redis URL is correct
2. Worker is connecting to same Redis as backend
3. Task name matches: `app.tasks.generation.process_generation`
4. Celery app is initialized properly

### Tasks Fail Immediately:
**Check worker logs for:**
- Missing API keys (Claude, OpenAI, R2)
- Database connection issues
- Import errors in task code

## Expected Behavior After Fix

Once worker is running:

1. ✅ Generation starts within seconds
2. ✅ Progress updates every few seconds (10% → 20% → 40% → 85% → 100%)
3. ✅ Completes in 60-120 seconds
4. ✅ Page preview appears
5. ✅ Can publish immediately

## Current Workaround for Testing

Until worker is set up, you **cannot test generation**. The tasks will queue but never process.

**What you CAN test:**
- ✅ Signup/login
- ✅ Create project
- ✅ Extract info (API call, not background task)
- ✅ Template selection
- ✅ Questions (API call, not background task)

**What you CANNOT test:**
- ❌ Generate landing page (requires worker)
- ❌ View generated preview (no generation completes)
- ❌ Publish (nothing to publish)
- ❌ Signups (page isn't generated)

## Files to Check

Verify these files exist and are correct:

**`backend/app/tasks/__init__.py`:**
```python
from celery import Celery

celery_app = Celery(
    'app',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)
```

**`backend/app/tasks/generation.py`:**
```python
from app.tasks import celery_app

@celery_app.task(...)
def process_generation(generation_id: str):
    # Task code
```

## Testing Celery Connection

Run this in Railway CLI to test:

```bash
railway run python -c "
from app.tasks import celery_app
from app.config import settings

print(f'Celery broker: {settings.REDIS_URL}')
print(f'Celery app: {celery_app}')
print('Testing connection...')
celery_app.control.inspect().active()
print('✅ Connected!')
"
```

## Summary

**Problem:** Celery worker not running = generations never process

**Solution:** Add separate "worker" service in Railway that runs:
```bash
celery -A app.tasks.celery worker --loglevel=info
```

**Priority:** HIGH - This blocks ALL generation testing

**Time to Fix:** 5-10 minutes to set up service in Railway

**After Fix:** Generations will complete in 60-120 seconds

---

## Quick Start After Worker is Running

1. ✅ Verify worker logs show "celery@worker ready"
2. ✅ Create new project
3. ✅ Generate landing page
4. ✅ Watch worker logs for task processing
5. ✅ Generation should complete in <2 minutes
6. ✅ Continue with rest of testing

**Need help setting this up? Let me know which method you want to use (separate service, CLI, or Procfile).**
