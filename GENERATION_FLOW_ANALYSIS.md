# Complete Generation Flow Analysis

## Current State: What We're Building

**Goal**: A polished, production-ready landing page generator where users can describe their product and get a professional landing page in ~60-120 seconds.

**User Experience Target**:
- Smooth, confidence-inspiring progress indicators
- Clear error messages with actionable next steps
- Resilient to network issues and API rate limits
- No confusing states (progress jumping, mysterious failures)
- Professional feel that matches quality SaaS products

---

## Complete Generation Flow Map

### 1. Frontend: Project Creation (Step 1)
**File**: `frontend/pages/projects/new.tsx` (lines 256-299)

**Current Issues**:
- ✅ FIXED: Character counter added
- ✅ FIXED: Error toast on failure

**Flow**:
```
User enters name → handleCreateProject() → projectsAPI.create() → Backend creates project → Frontend moves to Step 2
```

---

### 2. Frontend: Description & Extraction (Step 2)
**File**: `frontend/pages/projects/new.tsx` (lines 301-303)

**Current Issues**:
- ❌ **No loading state feedback** - User doesn't know extraction is happening
- ❌ **No retry on failure** - If extract fails, user must refresh
- ❌ **Empty description allowed** - Button enabled even with empty input
- ❌ **No character limit** - Could send huge prompts

**Flow**:
```
User enters description → handleExtract() → llm_service.extract_product_info() → Backend returns structured data → Frontend moves to Step 3
```

**Backend Issues** (`backend/app/services/llm.py:22-114`):
- ✅ FIXED: JSON parsing now handles markdown fences
- ❌ **No timeout handling** - 60s timeout could leave user hanging
- ❌ **Generic fallback** - Returns vague defaults on error instead of asking user to retry
- ❌ **No streaming** - User waits with no feedback

---

### 3. Frontend: Template Selection (Step 3)
**File**: `frontend/pages/projects/new.tsx` (lines 306-359)

**Current Issues**:
- ❌ **Loading spinner on ALL templates** - Should only show on clicked template
- ❌ **No template preview** - User picks blindly
- ❌ **Questions generation blocks UI** - Should show spinner on selected template only
- ❌ **No error handling** - If questions fail, user is stuck

**Flow**:
```
User selects template → handleSelectTemplate() → llm_service.generate_questions() → Frontend moves to Step 4
```

**Backend Issues** (`backend/app/services/llm.py:116-158`):
- ❌ **No retry on failure** - Questions fail = user stuck
- ❌ **Returns only 1 generic question on error** - Should prompt retry instead
- ❌ **No validation** - Could return malformed questions

---

### 4. Frontend: Answer Questions (Step 4)
**File**: `frontend/pages/projects/new.tsx` (lines 362-448)

**Current Issues**:
- ❌ **Required fields not enforced** - Can submit empty required answers
- ❌ **No validation feedback** - User doesn't know what's missing
- ❌ **Generate button shows wrong state** - Says "Starting generation..." but might fail instantly

**Flow**:
```
User answers questions → handleGenerate() → API creates generation → Celery task starts → Frontend moves to Step 5
```

---

### 5. Backend: Generation Creation
**File**: `backend/app/api/generate.py` (lines 150-267)

**Current Flow**:
```
1. Validate request
2. Check rate limits (3 per hour)
3. Check project exists
4. Check for pending generations (idempotency)
5. Check user tier limits
6. Create Generation record
7. Increment user counter
8. Queue Celery task
9. Return 202 Accepted
```

**Issues**:
- ✅ Good: Idempotency check prevents duplicate generations
- ✅ Good: Detailed error messages for limits
- ❌ **Race condition**: User counter incremented before task starts - if task fails immediately, no refund
- ❌ **No validation of input_data** - Could have missing required fields
- ❌ **No preview mode** - User can't test without using credits

---

### 6. Celery: Main Generation Task
**File**: `backend/app/tasks/generation.py` (lines 34-233)

**Current Flow**:
```
1. ANALYZING (10%) - Load generation, validate template
2. GENERATING_COPY (20%) - LLM generates all copy fields
3. GENERATING_IMAGES (40-60%) - DALL-E generates images in parallel
4. Image upload to R2 (progress updates per image)
5. ASSEMBLING (85%) - Inject copy & images into HTML template
6. COMPLETE (100%) - Update database, mark project as GENERATED
```

**Critical Issues**:

#### 6a. Error Handling
- ✅ FIXED: total_cost now defined before use
- ✅ Good: Soft/hard timeouts (9min/10min)
- ✅ Good: Retry logic for transient failures (3 attempts with exponential backoff)
- ✅ Good: Credit refund on failure
- ❌ **Progress resets to 0 on failure** - Should stay at failure point
- ❌ **Error messages too technical** - "JSONDecodeError" doesn't help user

#### 6b. Progress Updates
- ❌ **Progress can go backwards** - Celery retry resets to ANALYZING (10%)
- ❌ **No intermediate updates during LLM** - Stuck at 20% for 30-60 seconds
- ❌ **Image generation slow** - 4 parallel workers, but could be 6-8
- ❌ **R2 upload not timed** - Could hang silently

#### 6c. Timeout Handling
- ❌ **Frontend shows wrong message** - "Usually takes 60-120s" but timeout is 9 minutes
- ❌ **No early warning** - Should tell user if taking >3 minutes
- ❌ **Soft timeout handling** - Just marks failed, doesn't explain why

---

### 7. LLM Service: Copy Generation
**File**: `backend/app/services/llm.py` (lines 160-269)

**Current Flow**:
```
1. Build prompt with template fields + input data
2. Call Claude with 4096 max tokens
3. Extract JSON from response (handles markdown)
4. Validate copy content (no emojis, no generic phrases)
5. Retry once if validation fails
6. Calculate cost
7. Return (copy, cost)
```

**Issues**:
- ✅ FIXED: JSON extraction handles markdown fences
- ✅ Good: Retry on validation failure
- ✅ Good: Cost tracking
- ❌ **Only 1 retry** - Should retry 2-3 times before giving up
- ❌ **Validation too strict?** - Might reject good copy
- ❌ **No streaming** - 30-60s with no progress
- ❌ **Template in every retry** - Wastes tokens, should remember context

---

### 8. Image Service: Image Generation
**File**: `backend/app/services/images.py` (lines 97-144)

**Current Flow**:
```
1. Build prompts for each image spec
2. Generate 4 images in parallel (ThreadPoolExecutor)
3. Retry failed images once
4. Calculate cost ($0.04 per image)
5. Return (images, cost)
```

**Issues**:
- ✅ Good: Parallel generation
- ✅ Good: Retry logic
- ❌ **Only 4 workers** - Could be 6-8 for faster generation
- ❌ **No timeout per image** - Single slow image blocks all progress
- ❌ **Retry delay not specified** - Immediate retry might hit same rate limit
- ❌ **No fallback image** - Failed image = broken landing page

---

### 9. Frontend: Generation Status Polling
**File**: `frontend/hooks/useGeneration.ts` (lines 4-30)

**Current Flow**:
```
1. Poll every 2 seconds
2. Check status
3. Stop on COMPLETE or FAILED
4. Display progress bar
```

**Issues**:
- ✅ Good: Stops polling when done
- ❌ **Too aggressive** - 2 second polling = 30 requests per minute
- ❌ **No backoff** - Should slow down after 3+ minutes
- ❌ **Refetch on error stops** - One network error stops all polling
- ❌ **No retry on stuck** - If backend stuck, user never knows

---

### 10. Frontend: Progress Display
**File**: `frontend/pages/projects/new.tsx` (lines 460-563)

**Current Flow**:
```
1. Show spinner
2. Display status message
3. Show progress bar
4. Show time estimate (60-120s)
5. Show timeout warning after 3 minutes
```

**Issues**:
- ❌ **Time estimate wrong** - Says 60-120s but backend timeout is 9 minutes
- ❌ **Warning too late** - Shows at 3 minutes, but should show at 90 seconds
- ❌ **No explicit retry button** - User must navigate away and retry manually
- ❌ **Progress can jump backwards** - If Celery retries, goes from 40% → 10%
- ❌ **No "stuck" detection** - If progress doesn't change for 60s, should warn

---

## Summary of Critical Issues

### 🔴 User-Facing Critical (Breaks UX)
1. **Progress resets/jumps backwards** when Celery retries
2. **No retry button on failure** - user must navigate away
3. **Timeout warning shows too late** (3min vs 90s)
4. **Time estimate wrong** (says 60-120s, actually up to 9min)
5. **Template selection blocks all templates** instead of just selected one
6. **No loading feedback during extraction** (15-30s of nothing)
7. **Required fields not validated** - can submit empty required answers

### 🟡 Technical Critical (Could Break in Production)
8. **Race condition in credit deduction** - credits taken before task starts
9. **Image generation too slow** - only 4 parallel, should be 8
10. **Polling too aggressive** - 30 requests/minute for 9 minutes = 270 requests
11. **LLM only retries once** - should retry 2-3 times
12. **No timeout on individual images** - one slow image blocks everything
13. **JSON parsing fallback too generic** - should fail loudly, not silently

### 🟢 Polish Issues (Annoying but not breaking)
14. **No template preview** - user picks blindly
15. **No validation feedback** on question answers
16. **Error messages too technical** - "JSONDecodeError" vs "Something went wrong"
17. **No "stuck" detection** - if progress stops, no warning
18. **Extraction returns vague defaults** instead of asking user to be more specific

---

## Recommended Fix Priority

### Phase 1: Critical UX Fixes (Do First)
1. ✅ Fix progress reset - don't reset to 0 on retry, keep at last progress
2. Add retry button on failure with clear CTA
3. Fix timeout warnings (show at 90s, 3min, 5min)
4. Fix time estimate (say "1-3 minutes typically, up to 5 minutes")
5. Template loading - only show spinner on clicked template
6. Add loading state during extraction

### Phase 2: Resilience (Do Second)
7. Increase image parallelization to 8 workers
8. Add LLM retry logic (3 attempts with backoff)
9. Fix polling backoff (2s for first 2min, then 5s, then 10s)
10. Add timeout per image (60s max)
11. Fix credit race condition (deduct only after task starts)

### Phase 3: Polish (Do Third)
12. Add validation on question answers
13. Improve error messages (user-friendly, actionable)
14. Add template preview
15. Add "stuck" detection (warn if no progress for 60s)
16. Better extraction fallback (ask user for more detail)

---

## Next Steps

I'll now implement Phase 1 fixes comprehensively, not just quick patches.

