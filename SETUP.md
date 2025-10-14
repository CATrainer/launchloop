# Launch Loop - Railway Deployment Setup

## Step-by-Step Setup Guide

This guide walks you through deploying Launch Loop to Railway from scratch. **No local development setup required.**

---

## Prerequisites (Sign Up for These Services)

Before starting, create accounts for:

1. **Railway** - https://railway.app (main hosting)
2. **GitHub** - https://github.com (code repository)
3. **Cloudflare** - https://cloudflare.com (DNS + R2 storage)
4. **Stripe** - https://stripe.com (payments - use test mode)
5. **Anthropic** - https://console.anthropic.com (Claude API)
6. **OpenAI** - https://platform.openai.com (DALL-E API)
7. **Resend** - https://resend.com (transactional emails)
8. **Sentry** (optional) - https://sentry.io (error tracking)

---

## Part 1: Code Repository Setup

### 1.1 Create GitHub Repository

1. Go to https://github.com/new
2. Create new repository (e.g., "launch-loop")
3. Set to Private
4. Don't initialize with README (we have our own)
5. Click "Create repository"

### 1.2 Initialize Git and Push Code

```bash
# Navigate to your launch-loop directory
cd /path/to/launch-loop

# Initialize git
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - Launch Loop MVP"

# Add your GitHub remote (replace with your URL)
git remote add origin https://github.com/yourusername/launch-loop.git

# Push to GitHub
git branch -M main
git push -u origin main
```

---

## Part 2: Cloudflare Setup

### 2.1 Create R2 Bucket

1. Log into Cloudflare dashboard
2. Go to R2 → Create bucket
3. Name: `launch-loop-assets`
4. Location: Automatic
5. Click "Create bucket"

### 2.2 Generate R2 API Token

1. In R2, go to "Manage R2 API Tokens"
2. Click "Create API token"
3. Name: "Launch Loop Backend"
4. Permissions: "Object Read & Write"
5. Copy and save:
   - Access Key ID
   - Secret Access Key
   - Account ID (from R2 dashboard URL)

### 2.3 Configure DNS (Do this after Railway deployment)

We'll come back to this after we have Railway URLs.

---

## Part 3: External API Keys

### 3.1 Anthropic API Key

1. Go to https://console.anthropic.com
2. Navigate to API Keys
3. Create new key
4. Copy and save key (starts with `sk-ant-api03-`)

### 3.2 OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy and save key (starts with `sk-`)

### 3.3 Resend API Key

1. Go to https://resend.com/api-keys
2. Create API key
3. Copy and save key (starts with `re_`)
4. Verify sending domain (optional for testing)

### 3.4 Stripe Setup (Test Mode)

1. Go to https://dashboard.stripe.com/test
2. Make sure you're in **Test mode** (toggle in top right)

**Create Products:**

3. Go to Products → Add product
4. Create "Pro Monthly":
   - Name: "Launch Loop Pro"
   - Description: "5 generations/month, unlimited revisions, 1 published project"
   - Pricing: $15/month recurring
   - Save and copy the **Price ID** (starts with `price_`)

5. Create "Ultimate Monthly":
   - Name: "Launch Loop Ultimate"
   - Description: "Unlimited generations, revisions, and published projects"
   - Pricing: $100/month recurring
   - Save and copy the **Price ID**

6. Get API Keys:
   - Go to Developers → API keys
   - Copy **Publishable key** (starts with `pk_test_`)
   - Copy **Secret key** (starts with `sk_test_`)

**Webhook Setup (do after Railway deployment):**
We'll set this up once we have the backend URL.

---

## Part 4: Railway Deployment

### 4.1 Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Authorize Railway to access your GitHub
5. Select your `launch-loop` repository
6. Railway will start analyzing your project

### 4.2 Configure Backend Service

Railway should auto-detect the backend. Configure it:

1. Click on the backend service
2. **Settings:**
   - Service Name: `backend`
   - Root Directory: `backend`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Variables:** Click "Variables" tab and add:

```bash
ENV=staging
DEBUG=false
API_V1_PREFIX=/api/v1
APP_NAME=Launch Loop

# Generate this with: openssl rand -hex 32
JWT_SECRET=<paste-your-generated-secret>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=10080

# Anthropic
ANTHROPIC_API_KEY=<paste-your-anthropic-key>

# OpenAI
OPENAI_API_KEY=<paste-your-openai-key>

# Cloudflare R2
R2_ACCOUNT_ID=<paste-your-r2-account-id>
R2_ACCESS_KEY_ID=<paste-your-r2-access-key-id>
R2_SECRET_ACCESS_KEY=<paste-your-r2-secret-access-key>
R2_BUCKET_NAME=launch-loop-assets
R2_ENDPOINT=https://<your-account-id>.r2.cloudflarestorage.com

# Stripe (test mode)
STRIPE_SECRET_KEY=<paste-stripe-secret-key>
STRIPE_PUBLISHABLE_KEY=<paste-stripe-publishable-key>
STRIPE_PRICE_ID_PRO=<paste-pro-price-id>
STRIPE_PRICE_ID_ULTIMATE=<paste-ultimate-price-id>

# Resend
RESEND_API_KEY=<paste-resend-key>
RESEND_FROM_EMAIL=noreply@yourdomain.com

# We'll add these after other services are created
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
FRONTEND_URL=<will-add-after-frontend-deployed>
API_URL=<will-add-after-backend-deployed>
CORS_ORIGINS=<will-add-after-frontend-deployed>
```

4. **Domain:** Click "Settings" → "Generate Domain"
   - Save this URL (e.g., `backend-production-xxxx.up.railway.app`)
   - This is your `API_URL`

### 4.3 Add Database (PostgreSQL)

1. In your Railway project, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Wait for provisioning (30-60 seconds)
4. PostgreSQL will automatically add `DATABASE_URL` variable

### 4.4 Add Redis

1. Click "+ New" again
2. Select "Database" → "Redis"
3. Wait for provisioning
4. Redis will automatically add `REDIS_URL` variable

### 4.5 Configure Frontend Service

1. Click on the frontend service (or create new service if not auto-detected)
2. **Settings:**
   - Service Name: `frontend`
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Start Command: `npm start`

3. **Variables:**

```bash
NEXT_PUBLIC_ENV=staging
NEXT_PUBLIC_API_URL=<paste-your-backend-url>/api/v1
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=<paste-stripe-publishable-key>
```

4. **Domain:** Generate domain
   - Save this URL (e.g., `frontend-production-xxxx.up.railway.app`)
   - This is your `FRONTEND_URL`

### 4.6 Add Celery Worker Service

1. Click "+ New" → "Empty Service"
2. Link to same GitHub repo
3. **Settings:**
   - Service Name: `worker`
   - Root Directory: `backend`
   - Start Command: `celery -A app.tasks worker --loglevel=info`

4. **Connect Services:** (IMPORTANT - Worker needs access to Redis and Postgres)
   - In the worker service, click "Variables" tab
   - Click "+ New Variable" → "Add Reference"
   - Add `DATABASE_URL` → Reference → Select "Postgres" service
   - Add `REDIS_URL` → Reference → Select "Redis" service
   
5. **Copy Other Variables:**
   - Method 1: Click "RAW Editor" and copy all variables from backend service (except DATABASE_URL and REDIS_URL which you just added as references)
   - Method 2: Manually copy each variable from backend service:
     - `ENV`, `DEBUG`, `API_V1_PREFIX`, `APP_NAME`
     - `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRATION_MINUTES`
     - `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
     - `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET_NAME`, `R2_ENDPOINT`
     - `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, etc.
     - `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
     - `FRONTEND_URL`, `API_URL`, `CORS_ORIGINS` (will update these in section 4.7)

> **Why this matters:** The worker runs background tasks like AI generation and needs access to the same database, Redis, and APIs as the backend.

### 4.7 Update Cross-Service Variables

Now that all services are deployed, update these variables:

**Backend Service:**
```bash
FRONTEND_URL=https://<your-frontend-url>.up.railway.app
API_URL=https://<your-backend-url>.up.railway.app
CORS_ORIGINS=https://<your-frontend-url>.up.railway.app
```

**Worker Service:**
```bash
FRONTEND_URL=https://<your-frontend-url>.up.railway.app
API_URL=https://<your-backend-url>.up.railway.app
CORS_ORIGINS=https://<your-frontend-url>.up.railway.app
```

> **Note:** The worker needs these URLs to send emails with correct links and handle callbacks.

**After saving, Railway will automatically redeploy affected services.**

---

## Part 5: Database Setup

### 5.1 Install Railway CLI

```bash
npm install -g @railway/cli
```

### 5.2 Login and Link

```bash
# Login to Railway
railway login

# Link to your project (select from list)
railway link
```

### 5.3 Run Migrations

```bash
# Run database migrations
railway run --service backend alembic upgrade head
```

You should see output like:
```
INFO  [alembic.runtime.migration] Running upgrade -> abc123, Initial schema
INFO  [alembic.runtime.migration] Running upgrade abc123 -> def456, Add projects
...
```

### 5.4 Create Admin User

```bash
# Create your admin account
railway run --service backend python scripts/create_admin.py your-email@example.com
```

Output:
```
✅ User is now an admin: your-email@example.com
```

### 5.5 Seed Test Data (Optional)

```bash
# Add test accounts for testing
railway run --service backend python scripts/seed.py
```

This creates test accounts:
- `admin@example.com` / `password123` (admin)
- `pro@example.com` / `password123` (pro tier)
- `ultimate@example.com` / `password123` (ultimate tier)
- `free@example.com` / `password123` (free tier)

---

## Part 6: Stripe Webhook Setup

### 6.1 Create Webhook Endpoint

1. Go to Stripe Dashboard → Developers → Webhooks
2. Click "Add endpoint"
3. **Endpoint URL:** `https://<your-backend-url>.up.railway.app/api/v1/webhooks/stripe`
4. **Events to send:** Select these events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Click "Add endpoint"

### 6.2 Get Webhook Secret

1. Click on your newly created webhook
2. Under "Signing secret", click "Reveal"
3. Copy the secret (starts with `whsec_`)
4. Add to Railway backend variables:
   ```bash
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

### 6.3 Test Webhooks

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to your Railway backend
stripe listen --forward-to https://<your-backend-url>.up.railway.app/api/v1/webhooks/stripe
```

Keep this running and test creating a subscription. You should see webhook events in the console.

---

## Part 7: Cloudflare DNS Configuration

### 7.1 Add Your Domain (if you have one)

1. Go to Cloudflare → Add a site
2. Enter your domain
3. Follow instructions to update nameservers

### 7.2 Configure DNS Records

Add these records:

```
Type    Name                        Target
----    ----                        ------
CNAME   app                         <your-frontend-url>.up.railway.app
CNAME   api                         <your-backend-url>.up.railway.app
CNAME   *                           @
```

The wildcard (*) record enables subdomain routing for published landing pages.

### 7.3 Update Railway Variables

Update in both backend and frontend:

```bash
# Backend
FRONTEND_URL=https://app.yourdomain.com
API_URL=https://api.yourdomain.com
CORS_ORIGINS=https://app.yourdomain.com

# Frontend
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

---

## Part 8: Verification & Testing

### 8.1 Health Checks

Test these URLs in your browser:

1. **Backend Health:**
   ```
   https://<your-backend-url>.up.railway.app/health
   ```
   Should return: `{"status": "healthy"}`

2. **Frontend:**
   ```
   https://<your-frontend-url>.up.railway.app
   ```
   Should show the landing page

### 8.2 Create Test Account

1. Go to frontend URL
2. Click "Sign Up"
3. Create account with your email
4. Login
5. Test creating a project

### 8.3 Test Generation Flow

1. Create new project
2. Fill in product details
3. Click "Generate"
4. Watch progress indicator
5. Verify landing page is generated
6. Test publishing (if you have a paid account)

### 8.4 Test Admin Access

1. Logout
2. Login with admin account
3. Visit `<frontend-url>/admin`
4. Verify you can access admin dashboard

### 8.5 Test Payments (Optional)

1. Use Stripe test card: `4242 4242 4242 4242`
2. Any future expiry date
3. Any 3-digit CVC
4. Attempt upgrade to Pro tier
5. Verify subscription created in Stripe dashboard
6. Check user tier updated in admin dashboard

---

## Part 9: Monitoring & Logs

### 9.1 View Logs

```bash
# Backend logs
railway logs --service backend

# Frontend logs
railway logs --service frontend

# Worker logs
railway logs --service worker

# Follow logs in real-time
railway logs --service backend --follow
```

### 9.2 Monitor Metrics

In Railway dashboard:
- CPU usage
- Memory usage
- Network traffic
- Build times
- Deploy frequency

Set up alerts for:
- High error rates
- Service downtime
- Resource limits

---

## Part 10: Going to Production

### 10.1 Create Production Environment

1. In Railway, create new environment: "production"
2. Duplicate all services from staging
3. Update environment variables for production:
   - Use production Stripe keys
   - Update domain names
   - Configure production Sentry DSN

### 10.2 Switch Stripe to Live Mode

1. Go to Stripe dashboard
2. Toggle from "Test mode" to "Live mode"
3. Recreate products with production prices
4. Update Railway production variables with live keys
5. Recreate webhook endpoint with production URL

### 10.3 Production Checklist

- [ ] All environment variables configured
- [ ] Database migrations run
- [ ] Admin account created
- [ ] DNS configured correctly
- [ ] SSL certificates active
- [ ] Stripe live mode configured
- [ ] Webhooks tested
- [ ] Error tracking (Sentry) active
- [ ] Backups enabled
- [ ] Monitoring alerts configured

---

## Troubleshooting

### Service Won't Start

**Check logs:**
```bash
railway logs --service <service-name>
```

**Common issues:**
- Missing environment variables
- Database connection failed
- Port already in use
- Build failed

### Database Migrations Failed

```bash
# Check current migration status
railway run --service backend alembic current

# Try running migrations again
railway run --service backend alembic upgrade head

# If stuck, check what migrations exist
railway run --service backend alembic history
```

### Celery Worker Not Processing Jobs

**Check worker is running:**
```bash
railway logs --service worker --follow
```

**Verify Redis connection:**
```bash
railway run --service backend python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
```

### Webhooks Not Working

1. Check webhook secret is correct
2. Verify endpoint URL is accessible
3. Check Railway logs for webhook errors
4. Use Stripe CLI to test: `stripe listen --forward-to <url>`

### Frontend Can't Connect to Backend

1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check CORS settings in backend
3. Test backend health endpoint directly
4. Check browser console for errors

---

## Support

**Railway Documentation:** https://docs.railway.app
**Stripe Documentation:** https://stripe.com/docs
**FastAPI Documentation:** https://fastapi.tiangolo.com
**Next.js Documentation:** https://nextjs.org/docs

**Logs:**
```bash
railway logs --service <service-name> --follow
```

**Database Access:**
```bash
railway run --service backend psql $DATABASE_URL
```

---

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure all services
3. ✅ Test thoroughly
4. 📈 Monitor performance
5. 🚀 Launch to beta users
6. 💰 Switch to live Stripe mode
7. 📊 Scale as needed

Congratulations! Your Launch Loop platform is now deployed and ready to use. 🎉
