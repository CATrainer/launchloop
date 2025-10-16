# Launch Loop - Railway Testing Checklist

## 🚀 Deployment Status

**Before testing, verify:**
- [ ] Backend deployed successfully on Railway
- [ ] Frontend deployed successfully on Railway
- [ ] Celery worker is running
- [ ] Check Railway logs for any startup errors

**Quick Health Check:**
```bash
# Check backend health
curl https://api.thelaunchloop.com/health

# Check frontend loads
open https://app.thelaunchloop.com
```

---

## 🧪 Test Flow 1: Complete User Journey (CRITICAL)

### 1.1 Signup & Login
- [ ] Navigate to `https://app.thelaunchloop.com/signup`
- [ ] Enter email and password (min 8 chars)
- [ ] Click "Sign Up"
- [ ] **Expected:** Redirect to `/dashboard`
- [ ] **Expected:** See empty state with "No projects yet"
- [ ] Logout and login again
- [ ] **Expected:** Can login successfully

**If fails:** Check Railway backend logs for auth errors

---

### 1.2 Create Project & Extract
- [ ] Click "New Project" or "Create First Project"
- [ ] Enter project name (e.g., "My SaaS Product")
- [ ] Click "Continue"
- [ ] **Expected:** Step 2 - Describe Your Product appears
- [ ] Enter product description (e.g., "A tool that helps developers deploy apps faster with one command")
- [ ] Click "Continue"
- [ ] **Expected:** See loading "Analyzing..."
- [ ] **Expected:** Template selection screen appears with "Problem First" template
- [ ] **Expected:** No errors in console

**If fails:** 
- Check Railway backend logs for `/generate/extract` errors
- Check Claude API key is set
- Check network tab in browser dev tools

---

### 1.3 Template & Questions
- [ ] Click on "Problem First" template
- [ ] **Expected:** See loading "Loading questions..."
- [ ] **Expected:** Questions form appears (3-5 questions)
- [ ] Fill in all required questions
- [ ] **Expected:** See tier limit warning banner if on free tier (already used 1/1)
- [ ] **Expected:** Generate button shows "🚀 Generate Landing Page"
- [ ] Click "Generate Landing Page"

**If tier limit reached:**
- [ ] **Expected:** Toast error appears: "Monthly generation limit reached"
- [ ] **Expected:** Button is disabled
- [ ] Stop here and run upgrade script (see section 7)

**If can generate:**
- [ ] **Expected:** Loading state with spinner
- [ ] **Expected:** Redirect to project page after ~60 seconds

**If fails:**
- Check Celery worker logs in Railway
- Check for task timeout errors
- Check DALL-E API key is set
- Check R2 credentials are set

---

### 1.4 View Generated Project (NEW - FIXED)
- [ ] **Expected:** Land on `/projects/[id]` page
- [ ] **Expected:** Status badge shows "GENERATED" (blue)
- [ ] **Expected:** See project name at top
- [ ] **Expected:** See 3 stat cards: Signups, Template, Created date
- [ ] **Expected:** See "👁️ Preview Page" button in top right
- [ ] Click "Preview Page" button
- [ ] **Expected:** Iframe appears showing generated landing page
- [ ] **Expected:** Page looks professional (not broken HTML)
- [ ] **Expected:** Page has images (4 total)
- [ ] **Expected:** Page has copy text (no {{VARIABLES}} showing)
- [ ] Click "Open in new tab" link
- [ ] **Expected:** Opens in new window with full page
- [ ] Close preview tab, click "📊 Show Stats" to return

**If fails:**
- If stuck on "GENERATING" forever: Generation failed or timed out
- Check Railway backend logs for generation task errors
- Check if html_content field is populated in database
- Check if images uploaded to R2 successfully

---

### 1.5 Publish Project (NEW - FIXED)
- [ ] Scroll down to "Publish Your Page" section
- [ ] **Expected:** See subdomain input field
- [ ] Enter subdomain (e.g., "my-test-app")
- [ ] **Expected:** See preview text: "Your page will be live at my-test-app.thelaunchloop.com"
- [ ] Click "🚀 Publish Page" button
- [ ] **Expected:** See loading spinner "Publishing..."
- [ ] **Expected:** Success toast appears: "Project published successfully!"
- [ ] **Expected:** Status badge changes to "PUBLISHED" (green)
- [ ] **Expected:** Green banner appears showing live URL
- [ ] **Expected:** "Unpublish" button appears in top right
- [ ] **Expected:** Publish section disappears

**If fails:**
- Check Railway logs for `/projects/{id}/publish` errors
- Check if subdomain was saved to database
- Check if subdomain is already taken (unique constraint)

---

### 1.6 Visit Published Page (NEW - CRITICAL)
- [ ] Click the live URL in green banner (e.g., `https://my-test-app.thelaunchloop.com`)
- [ ] **Expected:** Page opens in new tab
- [ ] **Expected:** Page loads correctly (not 404)
- [ ] **Expected:** Page has all images
- [ ] **Expected:** Page has all copy text
- [ ] **Expected:** Page is scrollable
- [ ] Scroll to bottom of page
- [ ] **Expected:** See "Join Waitlist" section with email form
- [ ] **Expected:** Email input field exists
- [ ] **Expected:** Submit button exists

**If fails:**
- If 404: Check subdomain middleware in backend logs
- If blank: Check html_content is being served
- If no signup form: Check template.html has CTA section
- If images broken: Check R2 URLs are public

---

### 1.7 Test Signup Form (CRITICAL)
- [ ] On published page, scroll to bottom
- [ ] Enter test email (e.g., "test@example.com")
- [ ] Click "Join Waitlist" button
- [ ] **Expected:** Form disappears
- [ ] **Expected:** Success message appears: "🎉 Thanks for joining! We'll be in touch soon."

**If fails:**
- Check browser console for JavaScript errors
- Check network tab for `/api/v1/signups` request
- Check request payload has email and subdomain
- Check Railway backend logs for signup endpoint errors

---

### 1.8 View Signups (NEW - FIXED)
- [ ] Go back to browser tab with project detail page
- [ ] Refresh the page
- [ ] **Expected:** Signups count increments (0 → 1)
- [ ] **Expected:** "Signups" section appears below stats
- [ ] **Expected:** See table with email and timestamp
- [ ] **Expected:** See "📥 Export CSV" button
- [ ] Click "Export CSV"
- [ ] **Expected:** CSV file downloads
- [ ] Open CSV file
- [ ] **Expected:** Has headers: Email, Signed Up At, Referrer, User Agent
- [ ] **Expected:** Has your test email

**If fails:**
- Check `/signups/project/{id}` endpoint
- Check signups_count in database
- Check signup was actually created in database

---

### 1.9 Unpublish Project (NEW - FIXED)
- [ ] Click "Unpublish" button in top right
- [ ] **Expected:** Loading state "Unpublishing..."
- [ ] **Expected:** Success toast: "Project unpublished successfully"
- [ ] **Expected:** Status changes to "GENERATED"
- [ ] **Expected:** Green URL banner disappears
- [ ] **Expected:** "Publish Your Page" section reappears
- [ ] **Expected:** Unpublish button disappears
- [ ] Try visiting the subdomain URL again
- [ ] **Expected:** 404 or "Page not found"

**If fails:**
- Check `/projects/{id}/unpublish` endpoint
- Check project status changed in database
- Check subdomain middleware properly handles unpublished pages

---

## 🧪 Test Flow 2: Tier Limits & Upgrade

### 2.1 Verify Tier Limit Display
- [ ] On Dashboard, check tier display
- [ ] **Expected:** Shows "[Free Tier] • 1 / 1 generations used" (if you generated once)
- [ ] **Expected:** Shows red banner "Generation Limit Reached"
- [ ] **Expected:** "New Project" button is disabled and shows "🚫 Limit Reached"

### 2.2 Try to Create Another Project
- [ ] Try navigating to `/projects/new` directly
- [ ] Fill out form and try to generate
- [ ] **Expected:** See tier limit banner (red)
- [ ] **Expected:** Generate button disabled
- [ ] **Expected:** Button text: "🚫 Generation Limit Reached - Upgrade to Continue"

### 2.3 Upgrade Account (Manual for Testing)
Run in Railway CLI:
```bash
railway run --service backend python scripts/check_user.py YOUR_EMAIL@example.com
```
- [ ] **Expected:** See user info with Free tier, 1/1 generations used

```bash
railway run --service backend python scripts/upgrade_user.py YOUR_EMAIL@example.com ultimate
```
- [ ] **Expected:** "✅ User upgraded successfully!"
- [ ] **Expected:** Shows new tier: ultimate
- [ ] **Expected:** Generations used: 0

### 2.4 Verify Upgrade in UI
- [ ] Refresh Dashboard
- [ ] **Expected:** Shows "[Ultimate Tier] • Unlimited generations"
- [ ] **Expected:** No red banner
- [ ] **Expected:** "New Project" button is enabled
- [ ] Try creating a new project
- [ ] **Expected:** Can generate successfully

---

## 🧪 Test Flow 3: Error Handling

### 3.1 Failed Generation Recovery (If Occurs)
If a generation gets stuck or fails:
- [ ] Check Railway logs for error messages
- [ ] Project status should eventually change to "FAILED"
- [ ] Refresh project detail page
- [ ] **Expected:** See error message
- [ ] **Expected:** See "🔄 Retry Generation" button (if implemented)

### 3.2 Network Errors
- [ ] Turn off internet briefly
- [ ] Try to load Dashboard
- [ ] **Expected:** Toast error or friendly error message
- [ ] Turn internet back on
- [ ] Refresh
- [ ] **Expected:** Loads normally

### 3.3 Invalid Subdomain
- [ ] Try publishing with subdomain "ab" (too short)
- [ ] **Expected:** Error toast: "Subdomain must be at least 3 characters"
- [ ] Try publishing with subdomain that exists
- [ ] **Expected:** Error toast: "Subdomain already taken"

---

## 🧪 Test Flow 4: Multiple Projects

### 4.1 Create Second Project
- [ ] From Dashboard, click "New Project"
- [ ] Create another project with different description
- [ ] Complete generation
- [ ] **Expected:** Both projects appear on Dashboard
- [ ] **Expected:** Can click either project card
- [ ] **Expected:** Each project has own detail page

### 4.2 Publish Multiple (If Not Free Tier)
- [ ] Publish second project with different subdomain
- [ ] **Expected:** Both projects show as PUBLISHED
- [ ] **Expected:** Can visit both subdomains
- [ ] **Expected:** Each subdomain shows correct project

---

## 🧪 Test Flow 5: Dashboard Features

### 5.1 Project Cards
- [ ] Dashboard shows all projects
- [ ] **Expected:** Project name visible
- [ ] **Expected:** Status badge (color-coded)
- [ ] **Expected:** Subdomain shown if published
- [ ] **Expected:** Signup count shown
- [ ] **Expected:** Created date shown
- [ ] Click project card
- [ ] **Expected:** Navigate to project detail page

### 5.2 Empty State
- [ ] Delete all projects (via database or delete button if exists)
- [ ] Refresh Dashboard
- [ ] **Expected:** See "🚀 No projects yet" message
- [ ] **Expected:** See "Create First Project" button

---

## 🧪 Test Flow 6: Edge Cases

### 6.1 Very Long Project Name
- [ ] Create project with 100+ character name
- [ ] **Expected:** Should work or show validation error
- [ ] **Expected:** Name displays correctly (truncated if needed)

### 6.2 Special Characters in Subdomain
- [ ] Try subdomain with spaces: "my test"
- [ ] **Expected:** Error or auto-converted to "my-test"
- [ ] Try subdomain with uppercase: "MyTest"
- [ ] **Expected:** Auto-converted to lowercase "mytest"
- [ ] Try subdomain with symbols: "test@123"
- [ ] **Expected:** Validation error

### 6.3 Multiple Signups Same Email
- [ ] Submit signup form twice with same email
- [ ] **Expected:** Both signups recorded (no unique constraint)
- [ ] **Expected:** Count increments correctly

### 6.4 Direct URL Access
- [ ] Visit `/projects/invalid-id`
- [ ] **Expected:** "Project not found" message
- [ ] Visit another user's project ID (if you can)
- [ ] **Expected:** 403 Forbidden or 404 Not Found

---

## 🧪 Test Flow 7: Performance

### 7.1 Generation Speed
- [ ] Time the generation from click to completion
- [ ] **Expected:** <2 minutes
- [ ] **Target:** ~60 seconds average

### 7.2 Page Load Speed
- [ ] Test Dashboard load
- [ ] **Expected:** <2 seconds
- [ ] Test Project detail load
- [ ] **Expected:** <2 seconds
- [ ] Test Published page load
- [ ] **Expected:** <3 seconds

---

## 🐛 Known Issues to Check

### Issue 1: Generation Stuck Forever
**Symptoms:**
- Status shows "GENERATING" for >5 minutes
- Progress stays at same percentage
- Never completes or fails

**Check:**
- Railway Celery worker logs
- Look for timeout errors or exceptions
- Check if task timed out (5 min limit)

**Fix:**
- Generation should auto-fail after 5 minutes (new timeout)
- Refresh page to see FAILED status
- Retry button should appear

### Issue 2: Images Not Loading
**Symptoms:**
- Published page shows broken image icons
- Images work in preview but not on subdomain

**Check:**
- R2 bucket permissions (must be public)
- R2 URLs in html_content
- CORS settings on R2

### Issue 3: Signup Form Not Appearing
**Symptoms:**
- Published page has no email form
- Can't find "Join Waitlist" section

**Check:**
- Template HTML has CTA section
- HTML assembly didn't fail
- Check html_content in database for {{CTA_HEADLINE}}

### Issue 4: Publish Button Does Nothing
**Symptoms:**
- Click publish, nothing happens
- No loading state, no error

**Check:**
- Browser console for JavaScript errors
- Network tab for failed requests
- Check handlePublish function is called

---

## 📊 Success Metrics

After completing all tests, you should have:

- [ ] ✅ Created account
- [ ] ✅ Generated landing page (60-120 seconds)
- [ ] ✅ Saw generated page preview
- [ ] ✅ Published to subdomain
- [ ] ✅ Visited live subdomain URL
- [ ] ✅ Submitted signup form
- [ ] ✅ Saw signup in dashboard
- [ ] ✅ Exported signups CSV
- [ ] ✅ Unpublished project
- [ ] ✅ Tier limits working correctly
- [ ] ✅ All toasts/loading states working
- [ ] ✅ No console errors
- [ ] ✅ No Railway deployment errors

---

## 🚨 Critical Bugs to Report

If you encounter any of these, **stop testing and report immediately**:

1. **Can't complete signup/login** - Blocks all testing
2. **Generation fails every time** - Core feature broken
3. **Can't publish projects** - Can't test end-to-end flow
4. **Published pages return 404** - Subdomain routing broken
5. **Signup form doesn't work** - Can't capture leads
6. **Data loss** - Projects disappear, signups not saved

---

## 🎯 Next Steps After Testing

### If All Tests Pass:
1. Create 3-5 test projects with real product descriptions
2. Test on different browsers (Chrome, Firefox, Safari)
3. Test on mobile device
4. Share subdomain with friends for real signups
5. Monitor Railway logs for any errors
6. Check costs (LLM + image generation)

### If Tests Fail:
1. Document exact steps to reproduce
2. Copy error messages from:
   - Browser console
   - Railway backend logs
   - Railway Celery worker logs
3. Note which test step failed
4. Share screenshots if helpful
5. Check if it's a known issue (see section above)

---

## 📝 Testing Notes Template

Use this to track your testing session:

```
Date: [DATE]
Tester: [YOUR NAME]
Environment: Railway Production
Browser: [Chrome/Firefox/Safari] [VERSION]

=== TEST RESULTS ===

Flow 1 (User Journey): [ PASS / FAIL ]
- Signup: [ PASS / FAIL ]
- Generation: [ PASS / FAIL ]
- Preview: [ PASS / FAIL ]
- Publish: [ PASS / FAIL ]
- Signup Form: [ PASS / FAIL ]
- View Signups: [ PASS / FAIL ]

Flow 2 (Tier Limits): [ PASS / FAIL ]
Flow 3 (Error Handling): [ PASS / FAIL ]
Flow 4 (Multiple Projects): [ PASS / FAIL ]

=== BUGS FOUND ===

1. [Description]
   Steps: 
   Expected:
   Actual:
   
2. [Description]
   ...

=== PERFORMANCE ===

Generation time: [XX] seconds
Dashboard load: [XX] seconds
Published page load: [XX] seconds

=== NOTES ===

[Any other observations]
```

---

## 🎉 Definition of Done

**MVP is ready when:**
- [ ] Can complete full flow: signup → generate → publish → signup
- [ ] No critical bugs blocking main flows
- [ ] Generation success rate >90%
- [ ] All pages load in <3 seconds
- [ ] Mobile responsive (basic check)
- [ ] Tier limits enforced correctly
- [ ] Published pages accessible via subdomain
- [ ] Signup forms work reliably

**Then ready for:**
- Beta tester invites
- Soft launch
- Feedback collection
- Iteration on UX improvements
