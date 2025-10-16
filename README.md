# Launch Loop - Complete Setup Guide

## Overview

Launch Loop is an AI-powered landing page platform for solo founders. This guide covers deployment to Railway (no local setup required).

## Quick Start

1. **Clone Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy to Railway** (see detailed instructions below)

3. **Configure Environment Variables** (see Environment Variables section)

4. **Run Database Migrations** (via Railway CLI)

5. **Create Admin User** (via Railway CLI)

6. **Configure Cloudflare DNS**

7. **Test & Launch**

---

## Railway Deployment

### Prerequisites

- GitHub account with repository
- Railway account (https://railway.app)
- Stripe account (test mode initially)
- Cloudflare account for DNS
- Anthropic API key
- OpenAI API key
- Resend account for emails

### Step 1: Create Railway Project

1. Go to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway and select your repo
5. Railway will detect the project structure

### Step 2: Configure Services

Railway should auto-detect the following services:

**Backend Service (FastAPI)**
- **Root Directory:** `backend`
- **Build Command:** (auto-detected)
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port:** 8000

**Frontend Service (Next.js)**
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Start Command:** `npm start`
- **Port:** 3000

**PostgreSQL Database**
- Add from Railway services
- Automatically provisioned

**Redis**
- Add from Railway services  
- Automatically provisioned

**Celery Worker**
- **Root Directory:** `backend`
- **Start Command:** `celery -A app.tasks worker --loglevel=info`
- No exposed port needed

### Step 3: Environment Variables

#### Backend Service Variables

```bash
# App Config
ENV=staging
DEBUG=false
API_V1_PREFIX=/api/v1
APP_NAME=Launch Loop

# URLs
FRONTEND_URL=https://your-frontend.railway.app
BACKEND_URL=https://your-backend.railway.app

# CORS - Additional allowed origins (comma-separated, optional)
# Use this if you have multiple frontend domains (staging, production, etc.)
CORS_ORIGINS=https://app.yourdomain.com,https://staging.yourdomain.com

# Database (Railway provides automatically)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (Railway provides automatically)  
REDIS_URL=${{Redis.REDIS_URL}}

# JWT
JWT_SECRET=<generate-random-string-64-chars>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080

# Anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...

# OpenAI
OPENAI_API_KEY=sk-...

# Cloudflare R2
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=launch-loop-assets
R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com

# Stripe (test mode initially)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...
STRIPE_PRICE_ID_ULTIMATE=price_...

# Resend
RESEND_API_KEY=re_...

# Sentry (optional)
SENTRY_DSN=https://...
```

#### Frontend Service Variables

```bash
# API Connection
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1

# Stripe
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...

# Environment
NEXT_PUBLIC_ENV=staging
```

#### Celery Worker Variables
(Same as Backend - Railway can share env vars)

### Step 4: Generate Secrets

```bash
# Generate JWT secret (64 chars)
openssl rand -hex 32

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Step 5: Database Migrations

After services are deployed:

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Link to your project:
   ```bash
   railway link
   ```

4. Run migrations on backend service:
   ```bash
   railway run --service backend alembic upgrade head
   ```

### Step 6: Create Admin User

After migrations:

```bash
railway run --service backend python scripts/create_admin.py your-email@example.com
```

### Step 7: Seed Test Data (Optional)

```bash
railway run --service backend python scripts/seed.py
```

This creates test accounts:
- `admin@example.com` - Admin account
- `pro@example.com` - Pro tier account  
- `ultimate@example.com` - Ultimate tier account
- `free@example.com` - Free tier account

All test accounts have password: `password123`

---

## Cloudflare Setup

### DNS Configuration

1. **Main Domain:**
   ```
   A     thelaunchloop.com              → Railway Backend IP
   A     staging.thelaunchloop.com      → Railway Backend IP
   ```

2. **Wildcard Subdomains:**
   ```
   CNAME *.thelaunchloop.com            → thelaunchloop.com
   CNAME *.staging.thelaunchloop.com    → staging.thelaunchloop.com
   ```

3. **Frontend:**
   ```
   CNAME app.thelaunchloop.com          → Railway Frontend URL
   ```

### SSL Configuration

1. SSL/TLS → Overview → Full (strict)
2. Edge Certificates → Always Use HTTPS → On
3. Edge Certificates → Automatic HTTPS Rewrites → On

### R2 Storage Setup

1. Go to R2 in Cloudflare dashboard
2. Create bucket: `launch-loop-assets`
3. Create API token with R2 Read & Write permissions
4. Add credentials to Railway env vars

---

## Stripe Setup

### Test Mode Configuration

1. **Create Products:**
   - Go to Stripe Dashboard → Products
   - Create "Pro Monthly" - $15/month
   - Create "Ultimate Monthly" - $100/month
   - Save price IDs to env vars

2. **Webhook Setup:**
   - Go to Developers → Webhooks
   - Add endpoint: `https://your-backend.railway.app/api/v1/webhooks/stripe`
   - Select events:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`
   - Save webhook secret to env vars

3. **Test Webhooks:**
   ```bash
   # Install Stripe CLI
   stripe listen --forward-to https://your-backend.railway.app/api/v1/webhooks/stripe
   ```

---

## Verification Checklist

After deployment, verify:

- [ ] Backend health check: `https://your-backend.railway.app/health`
- [ ] Frontend loads: `https://your-frontend.railway.app`
- [ ] Can create account
- [ ] Can login
- [ ] Can create project
- [ ] Can generate landing page
- [ ] Subdomain routing works
- [ ] Admin dashboard accessible
- [ ] Stripe checkout works
- [ ] Webhooks process correctly

---

## Common Issues

### Database Connection Errors
- **Issue:** Can't connect to database
- **Fix:** Check `DATABASE_URL` environment variable is set correctly

### Celery Worker Not Processing
- **Issue:** Generations stuck in "pending"
- **Fix:** Check Celery worker service is running, verify Redis connection

### Subdomain Routing Not Working
- **Issue:** Subdomains return 404
- **Fix:** Verify wildcard DNS is configured, check middleware is active

### Stripe Webhooks Failing
- **Issue:** Subscriptions not updating
- **Fix:** Verify webhook secret matches, check Railway logs for errors

### CORS/Login Issues (400 Bad Request on OPTIONS)
- **Issue:** Login fails with 400 Bad Request on OPTIONS requests
- **Fix:** 
  1. Ensure `FRONTEND_URL` environment variable is set to your deployed frontend domain
  2. Add additional domains to `CORS_ORIGINS` if you have multiple frontends (comma-separated)
  3. Redeploy backend after updating environment variables

---

## Architecture

```
Frontend (Next.js)
    ↓
Backend API (FastAPI)
    ↓
    ├── PostgreSQL (data)
    ├── Redis (queue)
    ├── Celery (background jobs)
    ├── Anthropic API (copy generation)
    ├── OpenAI API (image generation)
    ├── Cloudflare R2 (image storage)
    ├── Stripe (payments)
    └── Resend (emails)
```

---

## Tech Stack

**Backend:**
- FastAPI (Python 3.11+)
- SQLAlchemy + Alembic
- PostgreSQL
- Redis + Celery
- JWT Authentication

**Frontend:**
- Next.js 14 (Pages Router)
- React 18 + TypeScript
- Tailwind CSS
- React Query

**Infrastructure:**
- Railway (hosting)
- Cloudflare (DNS + R2 storage)
- Stripe (payments)
- Sentry (error tracking)

---

## Security Notes

1. **Never commit secrets** to git
2. **Use strong JWT_SECRET** (64+ chars)
3. **Enable HTTPS** everywhere via Cloudflare
4. **Use test mode** for Stripe initially
5. **Monitor logs** for suspicious activity
6. **Rate limit** authentication endpoints
7. **Validate webhook signatures** from Stripe

---

## Support

For issues or questions:
- Check Railway logs: `railway logs --service <service-name>`
- Check GitHub issues
- Review architecture documentation in `/docs`

---

## Next Steps

After successful deployment:

1. **Test thoroughly** with test accounts
2. **Monitor** error rates and generation success
3. **Gather feedback** from beta users
4. **Switch to production** Stripe keys when ready
5. **Add custom domain** for professional appearance
6. **Scale** Railway resources as needed

---

## Production Checklist

Before going to production:

- [ ] Switch to Stripe live mode
- [ ] Configure production domain
- [ ] Set up Sentry for error tracking
- [ ] Enable rate limiting
- [ ] Configure email notifications
- [ ] Set up monitoring/alerting
- [ ] Create backup strategy
- [ ] Document runbooks
- [ ] Load test critical paths
- [ ] Security audit

---

## Database Schema

See `backend/app/models/` for complete schema.

Key tables:
- `users` - User accounts and subscriptions
- `projects` - Landing page projects
- `generations` - Generation attempts and results
- `signups` - Email captures from published pages

---

## Monitoring

Key metrics to track:

- Generation success rate (target: >95%)
- API response time (target: p95 <1s)
- Webhook delivery rate (target: >95%)
- Error rate (target: <1%)
- Active users
- Revenue (MRR)

Access logs:
```bash
railway logs --service backend
railway logs --service frontend
railway logs --service worker
```

---

## Scaling

Railway auto-scales based on usage. For high traffic:

1. **Database:** Upgrade PostgreSQL plan
2. **Redis:** Upgrade Redis plan  
3. **Workers:** Add more Celery worker instances
4. **CDN:** Cloudflare already provides CDN for assets

---

## Backup & Recovery

1. **Database backups:** Railway automatic (daily)
2. **Manual backup:**
   ```bash
   railway run --service postgres pg_dump > backup.sql
   ```
3. **Restore:**
   ```bash
   railway run --service postgres psql < backup.sql
   ```

---

## Troubleshooting Commands

```bash
# View logs
railway logs --service backend

# Access database
railway run --service backend psql $DATABASE_URL

# Run migrations
railway run --service backend alembic upgrade head

# Create admin
railway run --service backend python scripts/create_admin.py email@example.com

# Seed test data
railway run --service backend python scripts/seed.py

# Check service status
railway status
```

---

## License

Proprietary - All rights reserved
