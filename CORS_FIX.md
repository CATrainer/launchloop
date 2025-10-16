# CORS Fix for Railway Deployment

## Problem
You're getting 400 Bad Request errors on OPTIONS requests to `/api/v1/auth/login` because:
1. The subdomain middleware was interfering with CORS preflight requests
2. Your `FRONTEND_URL` environment variable likely doesn't include your deployed domain

## What Was Fixed

### 1. Subdomain Middleware (`backend/app/middleware/subdomain.py`)
- Now skips processing OPTIONS requests
- Allows CORS middleware to handle preflight requests properly

### 2. CORS Configuration (`backend/app/main.py`)
- Now supports multiple frontend origins
- Reads from `FRONTEND_URL` and `CORS_ORIGINS` environment variables

### 3. Configuration (`backend/app/config.py`)
- Added `CORS_ORIGINS` setting for multiple frontend domains

## What You Need To Do in Railway

### Step 1: Update Backend Environment Variables

Go to your Railway backend service and add/update these environment variables:

```bash
# Primary frontend URL (REQUIRED)
FRONTEND_URL=https://your-actual-frontend-domain.com

# Additional origins if you have multiple (OPTIONAL)
# Comma-separated, no spaces
CORS_ORIGINS=https://app.yourdomain.com,http://localhost:3000
```

**Examples:**
- If using Railway default: `FRONTEND_URL=https://your-frontend-xyz.up.railway.app`
- If using custom domain: `FRONTEND_URL=https://app.yourdomain.com`
- Multiple domains: `CORS_ORIGINS=https://staging.yourdomain.com,http://localhost:3000`

### Step 2: Redeploy Backend

After updating environment variables:
1. Commit and push these code changes to trigger a redeploy
2. Or manually redeploy from Railway dashboard

### Step 3: Verify

Test login again. The OPTIONS requests should now return 200 OK instead of 400 Bad Request.

## Why This Happened

When a browser makes a cross-origin request (like from your frontend to backend API), it first sends an OPTIONS "preflight" request to check if the request is allowed. 

Your CORS configuration was only allowing `localhost:3000`, so requests from your deployed domain were being rejected.

## Additional Notes

- Always include `http://` or `https://` in the URLs
- Don't add trailing slashes
- For development, you can keep `http://localhost:3000` in `ALLOWED_ORIGINS`
- The middleware order matters: CORS must handle OPTIONS before subdomain logic

## Debugging CORS Issues

Check Railway logs to see which origins are being allowed:
```bash
railway logs --service backend
```

You should see the allowed origins list when the server starts.
