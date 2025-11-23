# Quick Start: Deploy to Fly.io

**10-minute guide** to deploy FastAPI Supply Chain Management to Fly.io - **FREE forever!**

---

## Why Fly.io?

✅ **Truly FREE** - No credit card required  
✅ **No time limit** - Free forever (not a trial)  
✅ **256MB RAM** - Enough for small to medium apps  
✅ **PostgreSQL** included free  
✅ **No auto-sleep** - Always responsive (unlike Render free tier)  
✅ **Global CDN** - Fast from anywhere  

---

## Prerequisites ✅

- [x] Fly.io account ([sign up free](https://fly.io/app/sign-up))
- [x] `flyctl` CLI installed (already done! ✅)
- [x] Code ready to deploy

---

## Step 1: Login to Fly.io (1 minute)

```bash
# Add flyctl to PATH for this session
export PATH="/Users/macbook/.fly/bin:$PATH"

# Login to Fly.io
flyctl auth login
```

This will:
1. Open browser for authentication
2. Login with email (no card required!)
3. Return to terminal when done

---

## Step 2: Create PostgreSQL Database (2 minutes)

```bash
# Create PostgreSQL database (FREE tier)
flyctl postgres create \
  --name fastapi-supply-chain-db \
  --region iad \
  --initial-cluster-size 1 \
  --vm-size shared-cpu-1x \
  --volume-size 1
```

**Output you'll see:**
```
? Select Organization: (your organization)
? Choose a name for your Postgres cluster: fastapi-supply-chain-db
? Region: Washington D.C. (iad)
Creating postgres cluster...
Postgres cluster created!
```

**Save the connection string shown** - you'll need it!

---

## Step 3: Create and Configure App (3 minutes)

### 3.1 Initialize Fly App

```bash
# Launch app (this reads fly.toml)
flyctl launch --no-deploy
```

**When prompted:**
- ✅ App name: `fastapi-supply-chain` (or your preferred name)
- ✅ Organization: Select your organization
- ✅ Region: `iad` (Washington D.C.) - **must match database!**
- ❌ PostgreSQL: **No** (we already created it)
- ❌ Redis: **No** (not needed for free tier)
- ❌ Deploy now: **No** (we need to set secrets first)

### 3.2 Attach Database

```bash
# Attach the database we created
flyctl postgres attach fastapi-supply-chain-db
```

This automatically creates `DATABASE_URL` environment variable.

### 3.3 Set Secrets

```bash
# Generate and set SECRET_KEY
flyctl secrets set SECRET_KEY=$(openssl rand -hex 32)

# Set admin password
flyctl secrets set FIRST_SUPERUSER_PASSWORD="G0Wypnk5PeCdlpsrjV0t"

# Set admin email
flyctl secrets set FIRST_SUPERUSER_EMAIL="admin@example.com"

# Set CORS origins (update with your frontend URL)
flyctl secrets set BACKEND_CORS_ORIGINS="http://localhost:3000,https://yourdomain.com"
```

---

## Step 4: Deploy! (3 minutes)

```bash
# Deploy the application
flyctl deploy
```

**What happens:**
1. Builds Docker image (~2 min)
2. Pushes to Fly.io registry (~30 sec)
3. Runs database migrations (`alembic upgrade head`)
4. Starts application
5. Runs health checks

**Success output:**
```
==> Building image
==> Pushing image
==> Deploying
  --> v0 deployed successfully
==> Monitoring deployment
  1 desired, 1 placed, 1 healthy, 0 unhealthy

Visit your app at: https://fastapi-supply-chain.fly.dev
```

---

## Step 5: Verify Deployment (1 minute)

### 5.1 Check App Status

```bash
# View app info
flyctl status

# View logs
flyctl logs
```

### 5.2 Test Health Endpoint

```bash
# Open in browser or curl
curl https://fastapi-supply-chain.fly.dev/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected",
  "redis": "disabled",
  "timestamp": "2024-11-23T10:00:00Z"
}
```

### 5.3 Access API Documentation

Open in browser:
```
https://fastapi-supply-chain.fly.dev/docs
```

You should see **Swagger UI** with all endpoints!

---

## Step 6: Test Admin Login (1 minute)

### Option 1: Using Swagger UI

1. Go to `/docs`
2. Find **POST /api/v1/auth/login**
3. Click **"Try it out"**
4. Enter:
   ```json
   {
     "email": "admin@example.com",
     "password": "G0Wypnk5PeCdlpsrjV0t"
   }
   ```
5. Click **"Execute"**
6. Copy the `access_token`
7. Click **"Authorize"** (top right)
8. Paste: `Bearer your-token-here`

### Option 2: Using cURL

```bash
curl -X POST "https://fastapi-supply-chain.fly.dev/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "G0Wypnk5PeCdlpsrjV0t"
  }'
```

---

## That's It! 🎉

Your API is now live at:
```
https://fastapi-supply-chain.fly.dev
```

**Features:**
- ✅ Free forever (no credit card!)
- ✅ PostgreSQL database included
- ✅ Automatic HTTPS
- ✅ No auto-sleep (always responsive)
- ✅ Global CDN
- ✅ Automatic deployments on `git push`

---

## Useful Commands

### View App Info
```bash
# App status
flyctl status

# Live logs
flyctl logs

# SSH into container
flyctl ssh console

# Open app in browser
flyctl open

# Open /docs in browser
flyctl open /docs
```

### Database Management
```bash
# Connect to PostgreSQL
flyctl postgres connect -a fastapi-supply-chain-db

# Run migrations manually
flyctl ssh console -C "alembic upgrade head"

# Check migration status
flyctl ssh console -C "alembic current"
```

### Update App
```bash
# Make changes locally
git add .
git commit -m "Update feature"

# Deploy updates
flyctl deploy

# Rollback to previous version
flyctl releases rollback
```

### Scaling
```bash
# Check current resources
flyctl scale show

# Scale up RAM (costs money)
flyctl scale memory 512

# Scale up to 2 VMs (costs money)
flyctl scale count 2
```

---

## Cost Breakdown

### Free Tier (What You Get)
- **VMs**: 3x shared-cpu, 256MB RAM each = **FREE**
- **PostgreSQL**: 1x shared-cpu, 256MB RAM, 1GB storage = **FREE**
- **Bandwidth**: 160GB/month = **FREE**
- **SSL/HTTPS**: Automatic = **FREE**

**Your Usage:**
- 1 VM for FastAPI app = **FREE** ✅
- 1 PostgreSQL database = **FREE** ✅
- **Total: $0/month forever!**

### If You Need More (Optional)
- Upgrade to 512MB RAM: **$1.94/month**
- Upgrade to 1GB RAM: **$5.70/month**
- Add Redis: **$1/month**
- Extra bandwidth: **$0.02/GB**

---

## Troubleshooting

### Build Fails

**Error: "Cannot find requirements.txt"**
```bash
# Make sure you're in project directory
cd /Users/macbook/Documents/Coding/PY/fastapi-sqlmodel-starter-v1
flyctl deploy
```

**Error: "Build failed"**
```bash
# Check build logs
flyctl logs

# Try rebuilding
flyctl deploy --no-cache
```

### Database Connection Fails

**Error: "Could not connect to database"**
```bash
# Check database status
flyctl postgres list

# Check database is attached
flyctl postgres db list -a fastapi-supply-chain-db

# Re-attach database
flyctl postgres attach fastapi-supply-chain-db
```

### Health Check Fails

**Error: "Health check failed"**
```bash
# Check logs
flyctl logs

# Check app is running
flyctl status

# SSH into container
flyctl ssh console
```

### Deployment Hangs

**Stuck on "Monitoring deployment"**
```bash
# Cancel with Ctrl+C
# Check logs
flyctl logs

# Check if deployment completed
flyctl status
```

---

## Automatic Deployments (Optional)

### Deploy on Git Push

1. **Create Fly.io API Token:**
   ```bash
   flyctl auth token
   ```
   Copy the token

2. **Add to GitHub Secrets:**
   - Go to your repo → Settings → Secrets → Actions
   - Add secret: `FLY_API_TOKEN` = your token

3. **Create GitHub Action** (`.github/workflows/fly.yml`):
   ```yaml
   name: Deploy to Fly.io
   on:
     push:
       branches: [Supply-Chain, main]
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: superfly/flyctl-actions/setup-flyctl@master
         - run: flyctl deploy --remote-only
           env:
             FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
   ```

Now every push to `Supply-Chain` branch auto-deploys!

---

## Custom Domain (Optional)

```bash
# Add custom domain
flyctl certs add api.yourdomain.com

# Follow DNS instructions
flyctl certs show api.yourdomain.com

# Update CORS
flyctl secrets set BACKEND_CORS_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"
```

---

## Support

**Fly.io Docs:**
- [Documentation](https://fly.io/docs/)
- [Community Forum](https://community.fly.io)
- [Status Page](https://status.flyio.net)

**App Issues:**
- Check logs: `flyctl logs`
- Check status: `flyctl status`
- SSH console: `flyctl ssh console`

---

## Summary

✅ **Deployment Time**: ~10 minutes  
✅ **Cost**: **FREE forever**  
✅ **Credit Card**: **Not required**  
✅ **Auto-sleep**: **No** (always responsive)  
✅ **SSL/HTTPS**: **Automatic**  
✅ **Database**: **PostgreSQL included**  
✅ **Scaling**: **Easy** (`flyctl scale`)  

**Your app is live at:**
```
https://fastapi-supply-chain.fly.dev
```

Enjoy your free, production-ready API! 🚀
