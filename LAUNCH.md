# Synco Launch Checklist

## Pre-Launch (Before Going Live)

### Infrastructure
- [ ] Railway deployment working (health check green)
- [ ] Custom domain configured in Railway dashboard
- [ ] HTTPS/SSL active on custom domain
- [ ] Environment variables set in Railway:
  - [ ] SUPABASE_URL, SUPABASE_KEY
  - [ ] GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
  - [ ] STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET
  - [ ] STRIPE_PRO_PRICE_ID, STRIPE_PRO_ANNUAL_PRICE_ID
  - [ ] STRIPE_FAMILY_PLUS_PRICE_ID, STRIPE_FAMILY_PLUS_ANNUAL_PRICE_ID
  - [ ] STRIPE_SELF_HOSTED_PRICE_ID
  - [ ] SENTRY_DSN
  - [ ] ENVIRONMENT=production
  - [ ] ALLOWED_ORIGINS (production domain)

### Stripe
- [ ] Stripe account activated (not test mode)
- [ ] Products created: Pro Monthly, Pro Annual, Family Plus Monthly, Family Plus Annual, Self-Hosted License
- [ ] Price IDs copied to Railway env vars
- [ ] Webhook endpoint configured: https://yourdomain.com/api/billing/webhook
- [ ] Webhook events enabled: checkout.session.completed, customer.subscription.updated, customer.subscription.deleted, invoice.payment_failed
- [ ] Customer Portal configured (cancellation, plan changes)
- [ ] Test checkout flow end-to-end with Stripe test cards

### Google OAuth
- [ ] Google Cloud Console project configured for production
- [ ] OAuth consent screen submitted for verification (if >100 users)
- [ ] Redirect URI updated to production domain

### Content
- [ ] Landing page loads at / (unauthenticated)
- [ ] Pricing page loads at /pricing
- [ ] Legal pages load: /terms, /privacy, /refund
- [ ] All pages work in Polish and English
- [ ] Footer links present on all authenticated pages

### Self-Hosted
- [ ] Docker image published to GHCR (`docker pull ghcr.io/OWNER/synco:latest`)
- [ ] License key generation tested
- [ ] Self-hosted docker-compose.yml works with GHCR image
- [ ] Setup guide accurate and tested

### Testing
- [ ] All automated tests passing (`pytest tests/ -x`)
- [ ] Manual smoke test: sign up → create event → sync → budget → shopping list
- [ ] Mobile responsive check on phone
- [ ] PWA install works (manifest + service worker)

## Day 1 Actions

- [ ] Push production tag (e.g., `git tag v4.0.0 && git push --tags`)
- [ ] Verify Docker image published to GHCR
- [ ] Monitor Sentry for errors (first 24 hours)
- [ ] Monitor Stripe webhook delivery in Stripe Dashboard
- [ ] Check Railway logs for any startup errors
- [ ] Test signup flow from landing page to dashboard
- [ ] Test checkout flow for Pro plan

## 30-Day Success Criteria

| Metric | Target | How to Measure |
|--------|--------|---------------|
| Paying subscriber | ≥ 1 | Stripe Dashboard → Subscriptions |
| Self-hosted purchase | ≥ 1 | Stripe Dashboard → Payments (one-time) |
| Critical bugs | 0 | Sentry error count (critical/fatal) |
| PWA installable | Yes | Test on Android Chrome + Desktop Chrome |
| Uptime | > 99% | Railway metrics / health endpoint monitoring |

## Post-Launch Monitoring

### Daily (First Week)
- Check Sentry for new errors
- Check Stripe webhook delivery status
- Review Railway deployment logs

### Weekly (First Month)
- Review Stripe MRR and subscriber count
- Check Google OAuth quota usage
- Review error trends in Sentry

### Monthly (Ongoing)
- Review churn rate in Stripe
- Update dependencies (security patches)
- Review and respond to user feedback
