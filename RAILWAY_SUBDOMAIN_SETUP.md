# Railway Wildcard Subdomain Setup

## Problem
Published landing pages on subdomains (e.g., `test-saas.thelaunchloop.com`) return "Not Found" errors because Railway doesn't automatically handle wildcard subdomains.

## Solution

### Option 1: Railway Custom Domains (Recommended)

Railway doesn't support wildcard domains directly on their free tier, but you can add custom domains manually.

**For each published project:**
1. Go to Railway Dashboard → Your Service → Settings → Domains
2. Click "Custom Domain"
3. Add: `projectsubdomain.thelaunchloop.com`
4. Railway will provide DNS records
5. Add the CNAME record to your DNS provider

**This works but doesn't scale** - you'd need to add each subdomain manually.

---

### Option 2: Use Cloudflare for Wildcard Routing (Production Solution)

This is what you should use for production:

#### Step 1: Set up Cloudflare
1. Add `thelaunchloop.com` to Cloudflare
2. Point your domain's nameservers to Cloudflare

#### Step 2: Configure DNS
Add these DNS records in Cloudflare:

```
Type    Name    Content                         Proxy
----    ----    -------                         -----
A       @       Your Railway IP                 Yes (Orange)
CNAME   *       thelaunchloop.com               Yes (Orange)
CNAME   www     thelaunchloop.com               Yes (Orange)
```

#### Step 3: Configure Cloudflare Workers (Optional but Recommended)
Create a Cloudflare Worker to route wildcard subdomains:

```javascript
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const hostname = url.hostname
  
  // Main domain - route to frontend
  if (hostname === 'thelaunchloop.com' || hostname === 'www.thelaunchloop.com') {
    return fetch(request)
  }
  
  // API subdomain - route to backend
  if (hostname === 'api.thelaunchloop.com') {
    return fetch(request)
  }
  
  // All other subdomains - route to backend for landing pages
  // Backend will handle the subdomain routing
  const backendUrl = 'https://api.thelaunchloop.com'
  const newUrl = new URL(request.url)
  newUrl.host = new URL(backendUrl).host
  
  // Preserve original Host header so backend knows which subdomain
  const modifiedRequest = new Request(newUrl, {
    method: request.method,
    headers: request.headers,
    body: request.body
  })
  
  return fetch(modifiedRequest)
}
```

#### Step 4: Railway Configuration
In Railway, set these environment variables:

```bash
MAIN_DOMAIN=thelaunchloop.com
FRONTEND_URL=https://thelaunchloop.com
BACKEND_URL=https://api.thelaunchloop.com
```

---

### Option 3: Development/Testing Workaround

For local testing or quick staging deployment:

#### Use Railway's Built-in Domain
Railway gives you a domain like: `launch-loop-backend-production.up.railway.app`

**Modify your seed data to use Railway domains:**

In `backend/scripts/seed.py`, change:
```python
subdomain="test-saas"
```

To:
```python
subdomain=None  # Don't use subdomain
custom_domain="test-saas-staging.up.railway.app"  # Use Railway domain
```

Then manually add each domain in Railway settings.

---

## Recommended Production Setup

1. **Frontend**: Deploy to Vercel (better for Next.js)
   - Set custom domain: `thelaunchloop.com`
   - Vercel handles `www` automatically

2. **Backend**: Keep on Railway
   - Set custom domain: `api.thelaunchloop.com`
   - This handles API + subdomain landing pages

3. **Cloudflare**: Route wildcard subdomains
   - `*.thelaunchloop.com` → Railway backend
   - Backend's subdomain middleware handles routing
   - Cloudflare caches landing pages

### DNS Setup (Cloudflare)
```
Type    Name    Content                              Proxy
----    ----    -------                              -----
A       @       Vercel IP (from Vercel dashboard)    Yes
CNAME   *       api.thelaunchloop.com                Yes
CNAME   www     thelaunchloop.com                    Yes
CNAME   api     launch-loop.up.railway.app           Yes
```

---

## Current Status

Right now, your setup is:
- ✅ Backend on Railway
- ✅ Frontend on Railway (?)
- ❌ No wildcard domain configured

**To make test-saas.thelaunchloop.com work RIGHT NOW:**

### Quick Fix for Testing
1. Go to Railway Dashboard
2. Select your backend service
3. Go to Settings → Domains
4. Click "Custom Domain"
5. Add: `test-saas.thelaunchloop.com`
6. Railway gives you a CNAME record
7. Add to your DNS:
   ```
   CNAME  test-saas  your-backend.up.railway.app
   ```

Repeat for each test subdomain you want to use.

---

## Why This Happens

Your backend code is correct:
```python
# Middleware checks subdomain and serves HTML
if subdomain == "test-saas":
    return HTMLResponse(content=project.html_content)
```

But Railway doesn't know to route `test-saas.thelaunchloop.com` to your service by default. You need to either:
1. Add each subdomain manually (tedious)
2. Use Cloudflare Workers (scalable)
3. Use a reverse proxy

---

## Environment Variables to Set

Make sure Railway has these:

```bash
# Railway Environment Variables
ENV=production
MAIN_DOMAIN=thelaunchloop.com
FRONTEND_URL=https://thelaunchloop.com
BACKEND_URL=https://api.thelaunchloop.com

# Or for staging
ENV=staging
MAIN_DOMAIN=staging.thelaunchloop.com
FRONTEND_URL=https://staging.thelaunchloop.com
BACKEND_URL=https://api.staging.thelaunchloop.com
```

---

## Testing Locally

To test subdomain routing locally:

1. Edit your `/etc/hosts` file (Mac/Linux) or `C:\Windows\System32\drivers\etc\hosts` (Windows):
   ```
   127.0.0.1  test-saas.localhost
   127.0.0.1  demo.localhost
   ```

2. Start backend: `python backend/run.py`

3. Visit: `http://test-saas.localhost:8000`

Your middleware will detect the subdomain and serve the landing page.

---

## Next Steps

1. **Immediate**: Add `test-saas.thelaunchloop.com` manually in Railway
2. **Short-term**: Set up Cloudflare for wildcard routing
3. **Long-term**: Move frontend to Vercel, use Cloudflare Workers for routing
