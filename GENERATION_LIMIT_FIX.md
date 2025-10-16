# Generation Limit (403 Forbidden) - Quick Fix

## Problem

You're getting **403 Forbidden** when clicking "Generate Landing Page" because you've reached your tier's monthly generation limit.

## Tier Limits

- **Free Tier:** 1 generation/month, 10 revisions/month
- **Pro Tier:** 5 generations/month, unlimited revisions
- **Ultimate Tier:** Unlimited generations and revisions

## Solution

### Option 1: Upgrade Your Account Tier (Recommended for Testing)

Run this command in Railway to upgrade your account to Pro tier:

```bash
railway run --service backend python scripts/upgrade_user.py YOUR_EMAIL@example.com pro
```

This will:
- ✅ Upgrade you to Pro tier (5 generations/month)
- ✅ Reset your generation counter to 0
- ✅ Reset your revision counter to 0
- ✅ Set next reset date

**For unlimited generations (testing):**
```bash
railway run --service backend python scripts/upgrade_user.py YOUR_EMAIL@example.com ultimate
```

### Option 2: Check Your Current Status

To see your current tier and usage:

```bash
railway run --service backend python scripts/check_user.py YOUR_EMAIL@example.com
```

This shows:
- Current tier
- Generations used this month
- Revisions used this month
- When usage resets
- Payment status

### Option 3: Wait for Monthly Reset

Usage resets automatically on the 1st of each month at 00:00 UTC.

## After Upgrading

1. The changes take effect immediately
2. Refresh your frontend
3. Try generating again
4. Check Railway logs to confirm (you'll see usage counter at 0)

## Verify in Logs

After deploying the latest code, Railway logs will show detailed info when generation is blocked:

```
❌ Generation blocked for user abc-123 (tier: free)
   Reason: Monthly generation limit reached (1)
   Generations used: 1
   Revisions used: 0
```

## For Production

In production, users would:
1. Click "Upgrade" button in frontend
2. Complete Stripe checkout
3. Webhook automatically upgrades their tier
4. They can generate immediately

For now during testing/development, use the scripts above to manually manage tiers.

## Summary

**Quick fix:**
```bash
railway run --service backend python scripts/upgrade_user.py YOUR_EMAIL ultimate
```

This gives you unlimited generations for testing!
