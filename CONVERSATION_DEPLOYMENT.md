# Conversational System - Deployment Guide

## 🎯 Pre-Deployment Checklist

### Backend

- [ ] **Environment Variables Set**
  ```bash
  ANTHROPIC_API_KEY=sk-ant-...
  DATABASE_URL=postgresql://...
  FRONTEND_URL=https://your-frontend.vercel.app
  CORS_ORIGINS=https://your-frontend.vercel.app
  ```

- [ ] **Database Migration Run**
  ```bash
  alembic upgrade head
  # Should create conversations and conversation_messages tables
  ```

- [ ] **API Endpoints Working**
  ```bash
  curl http://localhost:8000/health
  # Should return {"status": "healthy"}
  ```

- [ ] **Conversation Routes Registered**
  - Check `/api/v1/conversations` exists
  - Check SSE endpoint `/api/v1/conversations/{id}/stream` works

### Frontend

- [ ] **Dependencies Installed**
  ```bash
  cd frontend
  npm install
  # framer-motion should be in package.json
  ```

- [ ] **Environment Variables Set**
  ```
  NEXT_PUBLIC_API_URL=https://your-backend.railway.app
  ```

- [ ] **Build Successful**
  ```bash
  npm run build
  # Should complete without errors
  ```

- [ ] **Conversation Page Exists**
  - `/pages/conversation/index.tsx` present
  - All components in `/components/conversation/` present

### Testing

- [ ] **Run Backend Tests**
  ```bash
  cd backend
  python test_conversation.py
  # All tests should pass
  ```

- [ ] **Manual Test Locally**
  - Start backend: `python run.py`
  - Start frontend: `npm run dev`
  - Visit `http://localhost:3000/conversation`
  - Complete full conversation flow

---

## 🚀 Deployment Steps

### Step 1: Backend Deployment (Railway)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add conversational system"
   git push origin main
   ```

2. **Railway Auto-Deploy**
   - Railway will detect changes and redeploy
   - Check build logs for errors
   - Migration should run automatically if `RUN_MIGRATIONS=True`

3. **Verify Deployment**
   ```bash
   curl https://your-backend.railway.app/health
   ```

4. **Check Conversation Endpoints**
   ```bash
   # Should return 401 (expected, needs auth)
   curl https://your-backend.railway.app/api/v1/conversations
   ```

### Step 2: Frontend Deployment (Vercel)

1. **Set Environment Variable**
   - Go to Vercel dashboard
   - Settings → Environment Variables
   - Add: `NEXT_PUBLIC_API_URL=https://your-backend.railway.app`

2. **Deploy**
   ```bash
   vercel --prod
   # Or push to main branch (auto-deploy)
   ```

3. **Verify Build**
   - Check Vercel build logs
   - Ensure no TypeScript errors
   - Ensure framer-motion is installed

### Step 3: Test Production

1. **Visit Conversation Page**
   ```
   https://your-frontend.vercel.app/conversation
   ```

2. **Test Full Flow**
   - Should see dark navy background
   - Should see neon cyan accents
   - AI should respond with streaming
   - Conversation should complete successfully

3. **Check Browser Console**
   - No CORS errors
   - No 404 errors
   - SSE connection successful

---

## 🐛 Common Deployment Issues

### Issue 1: CORS Errors

**Symptoms:**
```
Access to XMLHttpRequest blocked by CORS policy
```

**Fix:**
1. Check `backend/.env`:
   ```
   FRONTEND_URL=https://your-frontend.vercel.app
   CORS_ORIGINS=https://your-frontend.vercel.app
   ```

2. Restart backend or redeploy

**Verify:**
```bash
curl -H "Origin: https://your-frontend.vercel.app" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     https://your-backend.railway.app/api/v1/conversations
```

### Issue 2: SSE Connection Fails

**Symptoms:**
```
EventSource failed to connect
```

**Fix:**
1. Check Railway/backend logs for errors
2. Verify `/api/v1/conversations/{id}/stream` endpoint exists
3. Check if Claude API key is valid

**Test SSE locally:**
```bash
# Start a conversation, then:
curl -N https://your-backend.railway.app/api/v1/conversations/{id}/stream
```

### Issue 3: Database Tables Missing

**Symptoms:**
```
Table 'conversations' doesn't exist
```

**Fix:**
```bash
# SSH into Railway or run locally
alembic upgrade head
```

Or set `RUN_MIGRATIONS=True` in `backend/run.py` and redeploy.

### Issue 4: Claude API Errors

**Symptoms:**
```
Claude API error: 401 Unauthorized
```

**Fix:**
1. Verify `ANTHROPIC_API_KEY` in Railway environment variables
2. Check API key is valid: https://console.anthropic.com/
3. Check API usage limits

### Issue 5: Animations Not Working

**Symptoms:**
- No smooth fade-ins
- Messages appear instantly

**Fix:**
1. Check `framer-motion` is in `package.json`
2. Rebuild frontend: `npm run build`
3. Check browser console for errors

---

## 📊 Monitoring & Logs

### Backend Logs (Railway)

```bash
# Via Railway CLI
railway logs

# What to look for:
✅ "Conversation created"
✅ "Claude copy generation complete"
⚠️  "Copy validation failed" (retries are normal)
❌ "Claude API error" (check API key)
```

### Frontend Logs (Vercel)

```bash
# Via Vercel CLI
vercel logs

# Or browser DevTools Console
# What to look for:
✅ SSE connected
✅ Messages updating
❌ CORS errors (fix backend CORS)
❌ 404 errors (check API URL)
```

### Database Queries

```sql
-- Check conversations
SELECT id, phase, message_count, created_at 
FROM conversations 
ORDER BY created_at DESC 
LIMIT 10;

-- Check messages
SELECT cm.id, cm.sender, cm.message_type, cm.created_at
FROM conversation_messages cm
JOIN conversations c ON cm.conversation_id = c.id
WHERE c.id = 'conversation_id_here'
ORDER BY cm.created_at;

-- Check confidence scores
SELECT id, extracted_data->'problem_statement'->>'confidence' as problem_confidence,
       extracted_data->'target_audience'->>'confidence' as audience_confidence
FROM conversations
WHERE extracted_data IS NOT NULL;
```

---

## 🔒 Security Checklist

- [ ] **ANTHROPIC_API_KEY not exposed**
  - Not in frontend code
  - Not in logs
  - Secure in Railway environment

- [ ] **CORS configured properly**
  - Only allows your frontend domain
  - Not wildcard `*` in production

- [ ] **Authentication working**
  - `/conversation` requires login
  - API endpoints check user authentication

- [ ] **Rate limiting in place**
  - Claude API rate limits respected
  - User rate limits enforced

---

## 📈 Success Metrics

### Technical Metrics

- [ ] **Uptime:** Backend and frontend both >99.5%
- [ ] **Response Time:** AI response starts streaming within 5 seconds
- [ ] **Error Rate:** <1% of conversations fail
- [ ] **Completion Rate:** >80% of conversations complete successfully

### User Experience Metrics

- [ ] **Time to Generate:** Average 2-3 minutes from start to generated page
- [ ] **User Satisfaction:** "This feels natural" feedback
- [ ] **Visual Appeal:** "This looks professional" feedback
- [ ] **Confusion Rate:** <5% of users report confusion

---

## 🎉 Post-Deployment

### Immediate Actions (Day 1)

1. **Monitor Logs**
   - Watch for errors in first 24 hours
   - Check Claude API usage
   - Monitor database growth

2. **Test with Real Users**
   - Ask 3-5 users to try it
   - Watch them use it (screen share)
   - Gather immediate feedback

3. **Quick Fixes**
   - Fix any critical bugs
   - Adjust prompts if conversations feel off
   - Tweak confidence thresholds if needed

### Week 1 Actions

1. **Analyze Metrics**
   ```sql
   -- Completion rate
   SELECT 
     phase,
     COUNT(*) as count,
     AVG(message_count) as avg_messages
   FROM conversations
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY phase;
   ```

2. **Gather Feedback**
   - Survey users
   - Read conversation transcripts
   - Identify patterns in failures

3. **Iterate**
   - Refine AI prompts
   - Adjust confidence thresholds
   - Fix common pain points

### Month 1 Actions

1. **Scale Testing**
   - Test with 50-100 users
   - Monitor performance under load
   - Check database size growth

2. **Feature Additions**
   - Add more templates (if needed)
   - Improve edge case handling
   - Add voice input (optional)

3. **Optimization**
   - Reduce AI response time
   - Optimize database queries
   - Add caching where appropriate

---

## 📞 Support

### If Something Breaks

1. **Check Logs First**
   - Railway backend logs
   - Vercel frontend logs
   - Browser console

2. **Common Quick Fixes**
   - Restart backend (Railway CLI: `railway up`)
   - Clear browser cache
   - Check environment variables

3. **Rollback if Needed**
   ```bash
   # Backend
   git revert HEAD
   git push origin main
   
   # Frontend
   vercel rollback
   ```

---

## ✅ Deployment Complete!

When you see:
- ✅ Dark navy background with neon accents
- ✅ AI responding with smooth streaming
- ✅ Conversation feels natural
- ✅ No errors in logs
- ✅ Users completing flow successfully

**You're live! 🎉**

Monitor for 24 hours, gather feedback, iterate.

---

**Last Updated:** Oct 17, 2025  
**System Version:** Conversational Rebuild v1.0
