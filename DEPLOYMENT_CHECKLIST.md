# Deployment Checklist - Fix CORS 400 Error

## Current Status
✅ Code changes made and staged
⏳ Waiting for deployment to Railway
⏳ Waiting for environment variable configuration

## Steps to Fix

### Step 1: Commit & Push Changes
```bash
git commit -m "Fix CORS preflight request handling for production domains"
git push origin main
```

### Step 2: Update Railway Environment Variables

Go to Railway → Your Backend Service → Variables tab

**Add/Update these variables:**

```bash
# Your actual production frontend URL
FRONTEND_URL=https://your-actual-frontend-domain.com

# Additional frontend domains (comma-separated, NO SPACES)
CORS_ORIGINS=https://app.yourdomain.com,https://staging.yourdomain.com
```

**❗ IMPORTANT:**
- Include `https://` or `http://`
- NO trailing slashes
- NO spaces in the comma-separated list
- If you only have one frontend, just set `FRONTEND_URL`

**Example for Railway:**
```bash
FRONTEND_URL=https://launch-loop-frontend-production.up.railway.app
CORS_ORIGINS=https://app.thelaunchloop.com,https://staging.thelaunchloop.com
```

### Step 3: Check Deployment Logs

After Railway auto-deploys, check the logs:

```bash
railway logs --service backend
```

Look for this line at startup:
```
🔒 CORS Configuration:
   Allowed Origins: ['https://your-frontend.com', 'https://app.yourdomain.com']
```

This confirms your origins are being loaded correctly.

### Step 4: Test Login Again

Try logging in from your frontend. Check the browser Network tab:
- OPTIONS request should return **200 OK** (not 400)
- POST request should follow and return **200 OK**

## Troubleshooting

### Still Getting 400?

**Check 1: Is the code deployed?**
```bash
railway logs --service backend | grep "CORS Configuration"
```
You should see your domains listed.

**Check 2: Are environment variables set?**
Go to Railway → Backend Service → Variables
Verify `FRONTEND_URL` and `CORS_ORIGINS` are there.

**Check 3: What's the Origin header?**
In browser DevTools → Network → OPTIONS request → Headers
Check what `Origin:` is being sent. This MUST be in your allowed origins list.

**Check 4: Railway deployment succeeded?**
Go to Railway dashboard and verify backend service is running (green status).

### Common Mistakes

❌ **Wrong:** `CORS_ORIGINS=https://app.com, https://staging.com` (spaces)
✅ **Correct:** `CORS_ORIGINS=https://app.com,https://staging.com`

❌ **Wrong:** `CORS_ORIGINS=https://app.com/` (trailing slash)
✅ **Correct:** `CORS_ORIGINS=https://app.com`

❌ **Wrong:** `CORS_ORIGINS=app.com` (missing protocol)
✅ **Correct:** `CORS_ORIGINS=https://app.com`

## Quick Test

Once deployed, test the endpoint directly:

```bash
curl -X OPTIONS https://your-backend.railway.app/api/v1/auth/login \
  -H "Origin: https://your-frontend.com" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

You should see:
- Response: **200 OK** (or 204)
- Header: `Access-Control-Allow-Origin: https://your-frontend.com`
- Header: `Access-Control-Allow-Methods: *`

## Next Steps After Fix

1. ✅ Verify login works
2. ✅ Test signup flow
3. ✅ Check all authenticated endpoints
4. ✅ Test from all configured frontend domains
