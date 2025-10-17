# Conversational System - Quick Start Guide

## 🚀 Getting Started (5 Minutes)

### Step 1: Install Frontend Dependencies
```bash
cd frontend
npm install
```

This installs:
- `framer-motion` - For smooth animations
- `zustand` - State management (already installed)
- All other dependencies

### Step 2: Run Database Migration
```bash
cd backend
alembic upgrade head
```

This creates:
- `conversations` table
- `conversation_messages` table
- Required enums and indexes

### Step 3: Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
python run.py
```

Backend will run on `http://localhost:8000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

Frontend will run on `http://localhost:3000`

### Step 4: Test the Conversation

1. Visit: `http://localhost:3000/conversation`
2. You should see the dark navy background with neon accents
3. AI will greet you with a welcome message
4. Start typing: "I'm building an AI landing page generator"
5. Watch the conversation flow!

---

## 📋 What to Test

### Happy Path
```
You: "I'm building an AI tool that generates landing pages for solo founders"

AI: [Extracts: problem, audience, solution]
    [Asks contextual follow-up]

You: [Answer naturally]

AI: [Asks about product name]

You: "Launch Loop"

AI: [Shows Problem-First template with reasoning]

You: [Select template]

AI: [Gathers template data conversationally]
    "For the hero section, what's the internal dialogue when 
     someone has this problem?"

You: [Provide answers]

AI: [Once all fields have high confidence]
    "Perfect! Ready to generate your landing page?"
```

### Visual Quality Checks
- [ ] Dark navy background (#0A0E27) renders
- [ ] Neon cyan accents visible (#00D9FF)
- [ ] User messages have purple-to-blue gradient
- [ ] AI messages have glassmorphism (backdrop blur + border)
- [ ] Messages fade in and slide up smoothly
- [ ] Quick reply buttons have spring animation
- [ ] Scrollbar is custom styled (cyan on hover)
- [ ] Input floats with shadow

### Conversation Quality Checks
- [ ] AI asks contextual questions (references what you said)
- [ ] No visible phase transitions
- [ ] Questions don't feel like a form
- [ ] AI matches your communication style
- [ ] No generic questions like "What is your target audience?"
- [ ] Streaming text has typing effect (smooth, not jumpy)

---

## 🔍 Troubleshooting

### Issue: "Cannot find module 'framer-motion'"
**Fix:** Run `npm install` in the frontend directory

### Issue: "Table 'conversations' doesn't exist"
**Fix:** Run `alembic upgrade head` in the backend directory

### Issue: CORS errors in console
**Fix:** Check `backend/.env`:
```
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
```

### Issue: AI not responding
**Check:**
1. `ANTHROPIC_API_KEY` is set in `backend/.env`
2. Backend terminal shows no errors
3. Browser console for network errors
4. Backend logs for Claude API errors

### Issue: Streaming looks jumpy
**This is normal** - SSE with 50ms chunks. On production with faster network, it's smoother.

---

## 📁 Key Files

### Backend
```
backend/app/
├── api/conversations.py           # SSE streaming endpoints
├── models/conversation.py         # Database models
├── services/
│   ├── conversation.py            # Core logic (confidence scoring)
│   ├── conversation_ai.py         # AI prompt system
│   └── template_service.py        # Template management
└── alembic/versions/
    └── b9c4e7f3a2d6_*.py          # Migration
```

### Frontend
```
frontend/
├── pages/conversation/index.tsx   # Main page
├── components/conversation/
│   ├── ChatMessage.tsx            # Glassmorphism bubbles
│   ├── QuickReplies.tsx           # Animated buttons
│   ├── TemplateCard.tsx           # 3D tilt cards
│   └── ThinkingIndicator.tsx      # Animated dots
├── store/conversationStore.ts     # Zustand state
└── tailwind.config.js             # Custom colors
```

---

## 🎨 Customizing Colors

Edit `frontend/tailwind.config.js`:

```javascript
colors: {
  'dark-navy': '#0A0E27',        // Background
  'neon-cyan': '#00D9FF',        // Primary accent
  'electric-blue': '#4D7CFF',    // Secondary accent
  'neon-purple': '#B794F6',      // Tertiary accent
}
```

---

## 🧪 Testing Different User Types

### The Rusher
```
You: "Just make me a page"

Expected: AI acknowledges urgency, asks minimal high-value questions
```

### The Over-Explainer
```
You: [Paste a huge paragraph or document]

Expected: AI shows it read it, only asks about gaps
```

### The Wanderer
```
You: "I'm building X"
[AI asks follow-up]
You: "Actually, what about pricing?"

Expected: AI acknowledges tangent, gently redirects
```

### The Uncertain
```
You: "I don't know"

Expected: AI offers frameworks or examples
```

---

## 📊 How It Works

### Confidence Scoring
Every piece of data has a confidence score (0.0-1.0):
- **0.8+:** HIGH - Can proceed
- **0.5-0.7:** MEDIUM - Need more clarity
- **<0.5:** LOW - Missing or vague

### Phase Progression
System tracks internal phases but NEVER shows them to user:
1. IDEA_SATURATION - Understanding product
2. NAME_DISCUSSION - Getting/suggesting name
3. TEMPLATE_SELECTION - Showing template options
4. DATA_GATHERING - Collecting template data
5. GENERATION - Creating page

**Transitions are invisible** - user just experiences continuous conversation.

### Adaptive AI
```python
# User gives brief answers (< 50 chars)
engagement_level = LOW
AI responds concisely

# User writes paragraphs (> 200 chars)
engagement_level = HIGH
AI can be more expansive
```

---

## 🚢 Deploying to Production

### 1. Backend (Railway/Heroku)
```bash
# Already deployed if you pushed
# Migration will run automatically if RUN_MIGRATIONS=True in run.py
```

### 2. Frontend (Vercel/Netlify)
```bash
cd frontend
npm run build

# Set environment variable:
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

### 3. Test Production
1. Visit your deployed frontend
2. Go to `/conversation`
3. Test full flow
4. Check for CORS issues (common issue)

---

## 💡 Tips for Best Results

### 1. Natural Language Works Best
```
✅ "I'm building a tool that helps solo founders create landing pages 
    without spending hours in Figma"

❌ "Product: Landing page generator
    Target: Founders
    Problem: Time"
```

### 2. Be Specific
```
✅ "Our target audience is non-technical SaaS founders with less than 
    $10k MRR who need to move fast"

❌ "Small businesses"
```

### 3. Context Helps
```
✅ "We're in beta with 10 users who are loving the speed but want 
    more customization options"

❌ "It's in beta"
```

---

## 📈 Next Steps

After testing locally:

### Phase 1: Core Testing (Today)
- [ ] Test happy path
- [ ] Test edge cases (rusher, wanderer, etc.)
- [ ] Verify visual quality
- [ ] Check conversation feels natural
- [ ] Test on mobile (responsive design)

### Phase 2: Real Users (This Week)
- [ ] Deploy to production
- [ ] Test with 3-5 real founders
- [ ] Gather feedback on:
  - Conversation quality
  - Visual appeal
  - Question clarity
  - Time to complete

### Phase 3: Iteration (Next Week)
- [ ] Refine prompts based on feedback
- [ ] Add more templates
- [ ] Improve confidence scoring
- [ ] Add voice input (optional)
- [ ] Add real-time suggestions

---

## 🐛 Known Issues & Workarounds

### 1. First Message Delay
**Issue:** First AI response may be slow (5-10 seconds)  
**Why:** Cold start on Claude API  
**Workaround:** Normal after first message

### 2. Streaming on Slow Networks
**Issue:** Typing effect may be choppy  
**Why:** SSE with network latency  
**Workaround:** Works better on production with CDN

### 3. Long User Messages
**Issue:** AI may take longer to respond  
**Why:** More tokens to process  
**Workaround:** Normal behavior, show thinking indicator

---

## 📞 Need Help?

### Check Logs
**Backend:**
```bash
# Terminal where backend is running
# Look for errors in Claude API calls
# Check confidence scores in logs
```

**Frontend:**
```bash
# Browser DevTools → Console
# Look for SSE connection errors
# Check network tab for failed requests
```

### Common Log Messages
```
✅ "Claude copy generation complete" - Good
✅ "Conversation phase transitioned" - Normal
⚠️  "Copy validation failed" - Retry in progress
❌ "Claude API error" - Check API key
```

---

## 🎯 Success Criteria

You'll know it's working when:

1. **Visual Quality:** Users say "Wow, this looks professional"
2. **Conversation Quality:** Users don't realize they're in different "phases"
3. **Question Quality:** Users find questions helpful, not annoying
4. **Completion Rate:** Users complete the flow without confusion
5. **Time to Value:** Users get a generated page in 2-3 minutes

---

## 📝 Quick Reference

### Environment Variables
```bash
# Backend (.env)
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...
FRONTEND_URL=http://localhost:3000

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Endpoints
```
POST   /api/v1/conversations              # Start conversation
POST   /api/v1/conversations/{id}/messages # Send message
GET    /api/v1/conversations/{id}/stream   # SSE streaming
GET    /api/v1/conversations/{id}          # Get state
DELETE /api/v1/conversations/{id}          # Delete
```

### Database Tables
```sql
-- conversations
id, user_id, project_id, phase, extracted_data, 
template_data, user_engagement_level, message_count

-- conversation_messages
id, conversation_id, sender, content, message_type,
quick_replies, templates, thinking_status
```

---

**You're ready to test the conversational system!** 

Start with `http://localhost:3000/conversation` and experience the premium AI conversation flow.
