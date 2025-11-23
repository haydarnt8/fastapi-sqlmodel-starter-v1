# Quick Start: Deploy to Railway

**5-minute guide** to deploy FastAPI Supply Chain Management to Railway - **FREE with $5 credit (no card initially)!**

---

## Why Railway?

✅ **$5 FREE credit** - No credit card required to start!
✅ **Easy GitHub deployment** - Deploy in 1 click
✅ **PostgreSQL included** - Free database service
✅ **Excellent performance** - Better than Replit/Render free tiers
✅ **Auto-deploys** - Push to GitHub = automatic deployment
✅ **Custom domains** - FREE HTTPS + custom domain support
❌ **Credit card eventually** - After $5 credit runs out

**Perfect for:** Production apps, testing, demos, portfolios
**Best performance** among free tiers (better CPU/RAM than competitors)

---

## Step 1: Sign Up for Railway (1 minute)

### 1.1 Go to Railway

Open: [https://railway.app](https://railway.app)

### 1.2 Sign Up with GitHub

1. Click **"Login"** or **"Start a New Project"**
2. Click **"Login with GitHub"**
3. Authorize Railway to access your repositories
4. **NO CREDIT CARD NEEDED!** (You get $5 free credit)

### 1.3 Verify Your Email

Check your email and verify your account to activate the $5 credit.

---

## Step 2: Deploy from GitHub (2 minutes)

### 2.1 Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository: `haydarnt8/fastapi-sqlmodel-starter-v1`
4. Select branch: **Supply-Chain**
5. Click **"Deploy Now"**

Railway will automatically:
- Detect it's a Python project
- Install dependencies from `requirements.txt`
- Use the `nixpacks.toml` configuration
- Start building your app

### 2.2 Wait for Initial Build

You'll see build logs. This takes ~2-3 minutes.

---

## Step 3: Add PostgreSQL Database (1 minute)

### 3.1 Add Database Service - DO THIS FIRST

**IMPORTANT:** You must add PostgreSQL BEFORE configuring environment variables!

1. In your project dashboard, click **"+ New"**
2. Select **"Database"**
3. Choose **"Add PostgreSQL"**
4. Railway creates a free PostgreSQL database!
5. Wait for the database to be ready (status: "Active")

### 3.2 Verify Database is Created

You should see two services in your project:

- **fastapi-sqlmodel-starter-v1** (your app)
- **Postgres** (your database)

---

## Step 4: Configure Environment Variables (2 minutes)

### 4.1 Use the Auto-Generator Script (Recommended)

The easiest way to generate all required environment variables:

```bash
# In your local project directory
python generate_env_vars.py
```

This will:

- Generate a secure SECRET_KEY
- Create all required variables
- Save them to `.env.railway` file
- Show you exactly what to paste into Railway

### 4.2 Manual Configuration (Alternative)

If you prefer to add variables manually:

1. Click on your **FastAPI service** (not the database)
2. Go to **"Variables"** tab
3. Click **"Raw Editor"** button (top right)
4. Paste this entire configuration:

```bash
# Database - CRITICAL: Use Railway's template variable
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Application Settings
ENVIRONMENT=production
DEBUG=false
RELOAD=false

# Security - Generate with: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=<paste-generated-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin User - CHANGE THESE!
FIRST_SUPERUSER_EMAIL=admin@example.com
FIRST_SUPERUSER_PASSWORD=YourSecurePassword123!

# Redis - Disabled (no Redis service yet)
REDIS_ENABLED=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# CORS - Update with your frontend URL
BACKEND_CORS_ORIGINS=["https://your-frontend.com"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

Then click **"Update Variables"**

### 4.3 Critical: Verify DATABASE_URL

**IMPORTANT:** Make sure `DATABASE_URL` is set to:
```
${{Postgres.DATABASE_URL}}
```

NOT a hardcoded URL! The `${{...}}` syntax tells Railway to use the database connection string.

### 4.4 Railway Will Redeploy

After saving variables, Railway automatically redeploys your app with the new configuration!

---

## Step 5: Generate Domain & Access API (1 minute)

### 5.1 Generate Public Domain

1. Click on your **FastAPI service**
2. Go to **"Settings"** tab
3. Scroll to **"Networking"** section
4. Click **"Generate Domain"**

Railway will give you a URL like:
```
https://fastapi-supply-chain-production.up.railway.app
```

### 5.2 Wait for Deployment

Check the **"Deployments"** tab to see if deployment is complete.

### 5.3 Test Health Endpoint

Visit:
```
https://your-app.up.railway.app/api/v1/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected",
  "redis": "disabled"
}
```

### 5.4 Access API Documentation

Visit:
```
https://your-app.up.railway.app/docs
```

You should see **Swagger UI** with all your endpoints!

---

## Step 6: Test Admin Login

### Using Swagger UI:

1. Go to `https://your-app.up.railway.app/docs`
2. Find **POST /api/v1/auth/login**
3. Click **"Try it out"**
4. Enter:
   ```json
   {
     "email": "admin@example.com",
     "password": "YourSecurePassword123!"
   }
   ```
5. Click **"Execute"**
6. Copy the `access_token`
7. Click **"Authorize"** (top right, lock icon)
8. Enter: `Bearer your-token-here`
9. Now you can test all protected endpoints!

---

## That's It! 🎉

Your API is now live at:
```
https://your-app-name.up.railway.app
```

**Features:**
- ✅ $5 FREE credit (lasts 1-3 months for low traffic)
- ✅ PostgreSQL database included
- ✅ Automatic HTTPS
- ✅ Custom domain support (FREE)
- ✅ Auto-deploy on git push
- ✅ Better performance than Replit/Render free tiers
- ✅ No sleep/cold starts
- ✅ More RAM (512MB-1GB vs 256MB on competitors)

---

## Important Notes

### Free Credit & Pricing

**What's Free:**
- $5 credit (no card required initially)
- All features unlocked
- PostgreSQL database included
- Custom domains

**Credit Usage:**
- FastAPI app: ~$3-4/month (low traffic)
- PostgreSQL: ~$1-2/month
- **Total:** ~$5/month = your credit lasts 1 month

**After Free Credit:**
- Add credit card to continue
- Pay only for what you use (~$5/month for low traffic)
- Can add $5-10/month to keep running

**Pro tip:** Use Railway for production, Replit for testing!

### Performance

**Railway Free Tier:**
- 512MB-1GB RAM (vs 256MB on Fly.io, 512MB on Render)
- Shared vCPU (better than Replit)
- No cold starts (vs Render/Replit sleep)
- Fast response times

**Best free tier performance!**

### Auto-Deploy on Git Push

**Railway automatically redeploys when you push to GitHub!**

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin Supply-Chain

# Railway automatically:
# 1. Detects the push
# 2. Builds your app
# 3. Runs migrations
# 4. Deploys new version
# 5. Zero downtime!
```

### Custom Domain (FREE!)

1. Go to your service **"Settings"**
2. Scroll to **"Networking"**
3. Click **"Custom Domain"**
4. Enter your domain: `api.yourdomain.com`
5. Add the CNAME record to your DNS provider:
   ```
   CNAME api.yourdomain.com -> your-app.up.railway.app
   ```
6. Wait for DNS propagation (~5-60 minutes)
7. Railway automatically provisions FREE SSL certificate!

---

## Useful Railway Features

### View Logs

1. Click on your service
2. Go to **"Deployments"** tab
3. Click on latest deployment
4. View real-time logs

### Metrics & Monitoring

1. Click on your service
2. Go to **"Metrics"** tab
3. See CPU, RAM, Network usage

### Database Management

**Using Railway CLI:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Connect to your project
railway link

# Access PostgreSQL
railway run psql $DATABASE_URL
```

**Using pgAdmin or DBeaver:**
1. Get database credentials from Railway:
   - Click on **PostgreSQL** service
   - Go to **"Connect"** tab
   - Copy connection details
2. Use those credentials in pgAdmin/DBeaver

### Restart Service

1. Go to service **"Settings"**
2. Scroll to **"Service"** section
3. Click **"Restart"**

### Rollback Deployment

1. Go to **"Deployments"** tab
2. Find a previous successful deployment
3. Click **"⋮"** (three dots)
4. Click **"Redeploy"**

---

## Troubleshooting

### "Module not found" Error

**Check build logs:**
1. Go to **"Deployments"** tab
2. Click on failed deployment
3. Check if `pip install` succeeded

**Fix:**
```bash
# Ensure requirements.txt is correct
# Push changes to trigger rebuild
git add requirements.txt
git commit -m "Fix dependencies"
git push origin Supply-Chain
```

### "Database connection failed"

**Check DATABASE_URL format:**
1. Go to **"Variables"** tab
2. Ensure `DATABASE_URL` starts with `postgresql://` not `postgres://`

**Fix:**
```
# Change variable to:
DATABASE_URL = postgresql://${{Postgres.POSTGRES_USER}}:${{Postgres.POSTGRES_PASSWORD}}@${{Postgres.POSTGRES_HOST}}:${{Postgres.POSTGRES_PORT}}/${{Postgres.POSTGRES_DB}}
```

**Or simpler:**
```
DATABASE_URL = postgresql+asyncpg://${{Postgres.POSTGRES_USER}}:${{Postgres.POSTGRES_PASSWORD}}@${{Postgres.POSTGRES_HOST}}:${{Postgres.POSTGRES_PORT}}/${{Postgres.POSTGRES_DB}}
```

### "Alembic migration failed"

**Check deployment logs:**
1. Migrations run automatically via `railway.json` start command
2. Check logs for specific error

**Manual fix:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link project
railway login
railway link

# Run migrations manually
railway run alembic upgrade head
```

### App Crashes After Deploy

**Check logs:**
1. Go to **"Deployments"** → Click latest → View logs
2. Look for errors

**Common issues:**
- Missing environment variables
- Database connection issues
- Port binding (ensure using `$PORT`)

**Verify PORT usage:**
Check that your app binds to `$PORT` (already configured in `railway.json`)

### Out of Credit

**Check usage:**
1. Go to Railway dashboard
2. Check **"Usage"** section
3. See current credit balance

**Options:**
1. Add credit card to continue (~$5/month)
2. Switch to Replit (free but slower)
3. Optimize usage (reduce resources)

---

## Upgrading Your App

### Automatic (Recommended):

**Just push to GitHub:**
```bash
git add .
git commit -m "Add new feature"
git push origin Supply-Chain
```

Railway automatically rebuilds and deploys!

### Manual Redeploy:

1. Go to **"Deployments"** tab
2. Click **"Deploy"** button
3. Select branch: **Supply-Chain**
4. Click **"Deploy"**

---

## Monitoring & Alerts

### Built-in Monitoring:

- **Metrics tab**: CPU, RAM, Network usage
- **Logs tab**: Real-time application logs
- **Deployments tab**: Build and deploy history

### External Monitoring (Optional):

**Free options:**
- [UptimeRobot](https://uptimerobot.com) - Ping every 5 min, email alerts
- [Freshping](https://www.freshworks.com/website-monitoring/) - Free monitoring
- [Better Uptime](https://betteruptime.com) - Free tier with status page

**Setup:**
1. Add your Railway URL: `https://your-app.up.railway.app/api/v1/health`
2. Set check interval: 5 minutes
3. Add email for alerts

---

## Cost Breakdown

### Free Tier (First Month):

| Service | Cost/Month | Your $5 Credit |
|---------|-----------|----------------|
| FastAPI App | ~$3-4 | Covered |
| PostgreSQL | ~$1-2 | Covered |
| **Total** | **~$5** | **1 month FREE** |

### After Credit Runs Out:

**Low Traffic (~1000 requests/day):**
- FastAPI: $3-4/month
- PostgreSQL: $1-2/month
- **Total: ~$5/month**

**Medium Traffic (~10k requests/day):**
- FastAPI: $5-8/month
- PostgreSQL: $2-3/month
- **Total: ~$8-11/month**

**High Traffic (~100k requests/day):**
- FastAPI: $15-25/month
- PostgreSQL: $5-10/month
- **Total: ~$20-35/month**

**Still cheaper than most hosting!**

---

## Comparison

| Feature | Railway | Replit Free | Render Free |
|---------|---------|-------------|-------------|
| **Credit Card** | ❌ Not initially | ❌ Not needed | ✅ Required |
| **Free Credit** | $5 | Unlimited | 90 days |
| **RAM** | 512MB-1GB | ~512MB | 512MB |
| **CPU** | Shared (good) | Shared (slow) | Shared (medium) |
| **PostgreSQL** | ✅ Included | ✅ Via Neon | ✅ Included |
| **Auto-sleep** | ❌ No | ✅ Yes (1h) | ✅ Yes (15min) |
| **Cold Start** | ❌ None | ~10s | ~30-60s |
| **Performance** | ⭐⭐⭐⭐⭐ High | ⭐⭐ Low | ⭐⭐⭐ Medium |
| **Custom Domain** | ✅ FREE | ❌ Paid only | ✅ FREE |
| **Auto-Deploy** | ✅ GitHub | ✅ Git pull | ✅ GitHub |
| **Best for** | **Production** | Learning/Demos | Small projects |

**🏆 Railway wins for production apps!**

---

## Railway CLI (Optional)

### Install:

```bash
# Using npm
npm i -g @railway/cli

# Or using brew (macOS)
brew install railway
```

### Login:

```bash
railway login
```

### Link Your Project:

```bash
# Navigate to your project directory
cd /path/to/fastapi-sqlmodel-starter-v1

# Link to Railway project
railway link
```

### Useful Commands:

```bash
# View logs
railway logs

# Run commands in Railway environment
railway run alembic current

# Connect to database
railway run psql $DATABASE_URL

# Deploy manually
railway up

# Open project in browser
railway open

# Get environment variables
railway variables

# Add new variable
railway variables set SECRET_KEY=your-secret-key
```

---

## Best Practices

### 1. Use Environment Variables for Secrets

❌ **Don't:**
```python
SECRET_KEY = "hardcoded-secret"
```

✅ **Do:**
```python
SECRET_KEY = os.getenv("SECRET_KEY")
```

### 2. Enable Auto-Deploy

Railway auto-deploys by default when you push to GitHub!

### 3. Monitor Your Usage

Check Railway dashboard regularly to monitor:
- Credit usage
- RAM/CPU usage
- Database size

### 4. Set Up Monitoring

Add UptimeRobot to:
- Monitor uptime
- Get alerts on downtime
- Track response times

### 5. Use Database Backups

**Railway PostgreSQL includes automatic backups!**

But you can also:
```bash
# Manual backup
railway run pg_dump $DATABASE_URL > backup.sql

# Restore
railway run psql $DATABASE_URL < backup.sql
```

### 6. Optimize Performance

```python
# Use connection pooling (already configured in app/db/session.py)
# Set appropriate worker count in railway.json
# Enable gzip compression in FastAPI
```

---

## Next Steps

1. ✅ **Test all endpoints** in `/docs`
2. ✅ **Set up custom domain** (optional)
3. ✅ **Add monitoring** with UptimeRobot
4. ✅ **Configure CORS** for your frontend
5. ✅ **Set up database backups**
6. ✅ **Monitor credit usage**

---

## Support

**Railway Help:**
- [Documentation](https://docs.railway.app)
- [Discord](https://discord.gg/railway)
- [GitHub](https://github.com/railwayapp/railway)

**App Issues:**
- Check deployment logs in Railway
- Review this troubleshooting guide
- Check [docs/](../docs/) folder for app-specific help

---

**Your app is live on Railway!** 🎉

**URL:** `https://your-app.up.railway.app/docs`

**Features:**
- 🚀 Production-ready performance
- 🔒 Automatic HTTPS
- 🗄️ PostgreSQL database
- 🔄 Auto-deploy on git push
- 📊 Monitoring & metrics
- 🌐 Custom domain support (FREE)

Enjoy your Railway deployment!
