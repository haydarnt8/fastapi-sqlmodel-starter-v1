# Deployment Guide - Render Platform

Complete guide for deploying the FastAPI Supply Chain Management application to Render.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Before You Deploy](#before-you-deploy)
3. [Deployment Steps](#deployment-steps)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Post-Deployment](#post-deployment)
7. [Monitoring and Logs](#monitoring-and-logs)
8. [Troubleshooting](#troubleshooting)
9. [Updating the Application](#updating-the-application)

---

## Prerequisites

### 1. Render Account
- Sign up at [https://render.com](https://render.com)
- Free tier available (with limitations)
- Credit card required for paid plans

### 2. GitHub Repository
- Push your code to GitHub
- Ensure `render.yaml` is in the repository root
- Make sure `.env` is in `.gitignore` (never commit secrets!)

### 3. Local Testing
- Test the application locally first
- Verify all tests pass: `pytest`
- Ensure database migrations work: `alembic upgrade head`

---

## Before You Deploy

### 1. Generate Secure Keys

**SECRET_KEY** - Generate a cryptographically secure key:
```bash
# Option 1: Using OpenSSL
openssl rand -hex 32

# Option 2: Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**Example Output:**
```
a7f3d8e2c9b1a4f6e8d2c7b9a3f5e1d8c6b4a2f7e9d3c8b5a1f4e6d2c9b7a3f5
```

Save this - you'll need it for `SECRET_KEY` environment variable.

### 2. Create Strong Admin Password

**FIRST_SUPERUSER_PASSWORD** - Create a strong password:
```bash
# Generate random password
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(20)))"
```

**Example Output:**
```
Xk9#mP2vL@8nQ5wR$3tY
```

### 3. Update render.yaml

Open `render.yaml` and update:

```yaml
services:
  - type: web
    name: fastapi-supply-chain  # Change to your preferred name
    branch: main  # Or your main branch name (e.g., Supply-Chain)

    envVars:
      - key: BACKEND_CORS_ORIGINS
        value: https://yourdomain.com,https://www.yourdomain.com  # Your frontend URL

      - key: FIRST_SUPERUSER_EMAIL
        value: admin@yourdomain.com  # Your admin email
```

### 4. Review Files to Deploy

Make sure these files are in your repository:
- ✅ `render.yaml` - Render configuration
- ✅ `requirements.txt` - Python dependencies
- ✅ `alembic.ini` - Database migration config
- ✅ `alembic/` directory - Migration scripts
- ✅ `app/` directory - Application code
- ❌ `.env` - Should NOT be in repository (add to .gitignore)
- ❌ `dev.db` - Development database (add to .gitignore)

---

## Deployment Steps

### Step 1: Push to GitHub

```bash
# Add all files
git add .

# Commit changes
git commit -m "Prepare for Render deployment"

# Push to GitHub
git push origin main  # or your branch name
```

### Step 2: Create Render Blueprint

1. **Login to Render Dashboard**
   - Go to [https://dashboard.render.com](https://dashboard.render.com)

2. **Create New Blueprint**
   - Click **"New"** → **"Blueprint"**
   - Connect your GitHub account if not already connected
   - Select your repository
   - Render will automatically detect `render.yaml`

3. **Review Services**
   Render will show:
   - **Web Service**: `fastapi-supply-chain` (your API)
   - **PostgreSQL Database**: `fastapi-supply-chain-db`

4. **Click "Apply"**
   - Render will start provisioning resources

### Step 3: Configure Environment Variables

While services are being created:

1. **Go to Web Service Settings**
   - Click on your web service name
   - Go to **"Environment"** tab

2. **Add Secret Variables**
   These are NOT in `render.yaml` for security:

   ```
   FIRST_SUPERUSER_PASSWORD = your-secure-password-here
   ```

3. **Verify Auto-Generated Variables**
   Render automatically creates:
   - `SECRET_KEY` (auto-generated)
   - `DATABASE_URL` (from PostgreSQL service)

4. **Optional: Add Custom Variables**
   ```
   # If using custom domain
   BACKEND_CORS_ORIGINS = https://yourdomain.com,https://api.yourdomain.com

   # If using SendGrid for emails
   SMTP_HOST = smtp.sendgrid.net
   SMTP_USER = apikey
   SMTP_PASSWORD = your-sendgrid-api-key
   EMAILS_FROM_EMAIL = noreply@yourdomain.com
   ```

### Step 4: Wait for Deployment

Monitor the build logs:
- **Build Phase**: Installing dependencies (~2-3 minutes)
- **Migration Phase**: Running `alembic upgrade head` (~30 seconds)
- **Start Phase**: Starting Gunicorn server (~10 seconds)

**Success Indicators:**
```
==> Starting service with 'alembic upgrade head && gunicorn ...'
INFO  [alembic.runtime.migration] Running upgrade -> abc123def456, initial
INFO  [alembic.runtime.migration] Running upgrade abc123def456 -> def789ghi012, add suppliers
✓ Database initialized
✓ Database seeded with initial data
🚀 Supply Chain Management API is ready!
[2024-11-22 10:00:00 +0000] [1] [INFO] Starting gunicorn 21.2.0
[2024-11-22 10:00:00 +0000] [1] [INFO] Listening at: http://0.0.0.0:10000
[2024-11-22 10:00:00 +0000] [1] [INFO] Using worker: uvicorn.workers.UvicornWorker
```

---

## Environment Variables

### Required Variables

| Variable | Description | Example | Source |
|----------|-------------|---------|--------|
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host/db` | Auto (from database) |
| `SECRET_KEY` | JWT signing key | `a7f3d8e2c9b1a4f6...` | Auto-generated |
| `FIRST_SUPERUSER_PASSWORD` | Admin password | `Xk9#mP2vL@8nQ5wR$3tY` | Manual (secret) |
| `ENVIRONMENT` | Deployment environment | `production` | render.yaml |

### Recommended Variables

| Variable | Default | Production Value |
|----------|---------|------------------|
| `BACKEND_CORS_ORIGINS` | `http://localhost:3000` | `https://yourdomain.com` |
| `FIRST_SUPERUSER_EMAIL` | `admin@example.com` | Your email |
| `LOG_LEVEL` | `INFO` | `INFO` or `WARNING` |
| `REDIS_ENABLED` | `true` | `false` (unless using Redis add-on) |
| `RATE_LIMIT_ENABLED` | `true` | `true` |

### Optional Variables

| Variable | Description | When Needed |
|----------|-------------|-------------|
| `SMTP_HOST` | Email server | Password reset emails |
| `SMTP_USER` | Email username | Email functionality |
| `SMTP_PASSWORD` | Email password | Email functionality |
| `REDIS_URL` | Redis connection | If using Redis add-on |

---

## Database Setup

### Automatic Setup

Render automatically:
1. Creates PostgreSQL database
2. Runs `alembic upgrade head` (creates tables)
3. Seeds initial data (roles, permissions, admin user)

### Manual Database Commands

If you need to run database commands:

1. **Access Shell**
   - Go to your web service
   - Click **"Shell"** tab
   - Opens terminal in your container

2. **Run Alembic Commands**
   ```bash
   # Check current migration version
   alembic current

   # Upgrade to latest
   alembic upgrade head

   # Rollback one version
   alembic downgrade -1

   # View migration history
   alembic history
   ```

3. **Access Database Console**
   - Go to your PostgreSQL service
   - Click **"Connect"** → **"External Connection"**
   - Use provided psql command:
   ```bash
   psql postgresql://user:pass@host:port/database
   ```

### Database Backups

**Automatic Backups:**
- **Free Plan**: No automatic backups
- **Starter Plan ($7/month)**: Daily backups (7-day retention)
- **Standard Plan**: Daily backups (14-day retention)

**Manual Backup:**
```bash
# Download backup using Render dashboard
# Or use pg_dump
pg_dump $DATABASE_URL > backup.sql
```

---

## Post-Deployment

### 1. Verify Deployment

**Check Health Endpoint:**
```bash
curl https://your-app.onrender.com/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected",
  "redis": "disabled",
  "timestamp": "2024-11-22T10:00:00Z"
}
```

### 2. Access API Documentation

Open in browser:
```
https://your-app.onrender.com/docs
```

You should see Swagger UI with all endpoints.

### 3. Test Admin Login

```bash
curl -X POST "https://your-app.onrender.com/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@yourdomain.com",
    "password": "your-admin-password"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4. Create First Restaurant/Supplier

Use the Swagger UI at `/docs` to:
1. Register a new user (`POST /api/v1/auth/register`)
2. Login to get token
3. Create restaurant or supplier
4. Verify with admin account

### 5. Configure Custom Domain (Optional)

1. **Go to Web Service Settings**
   - Click **"Settings"** tab
   - Scroll to **"Custom Domain"**

2. **Add Domain**
   - Enter your domain: `api.yourdomain.com`
   - Render provides DNS records

3. **Update DNS**
   - Add CNAME record in your DNS provider
   - Point to Render's address

4. **Update CORS**
   ```yaml
   BACKEND_CORS_ORIGINS = https://yourdomain.com,https://api.yourdomain.com
   ```

---

## Monitoring and Logs

### View Logs

**Real-time Logs:**
1. Go to your web service
2. Click **"Logs"** tab
3. See live streaming logs

**Search Logs:**
- Use search box to filter logs
- Filter by log level: INFO, WARNING, ERROR

**Example Logs:**
```
2024-11-22 10:00:00 INFO [app.main] Starting Supply Chain Management API v2.0.0
2024-11-22 10:00:00 INFO [app.main] Environment: production
2024-11-22 10:00:00 INFO [app.db.init_db] ✓ Database initialized
2024-11-22 10:00:00 INFO [app.db.init_db] ✓ Database seeded with initial data
```

### Metrics Dashboard

Render provides:
- **CPU Usage**: Monitor server load
- **Memory Usage**: Track RAM consumption
- **Response Times**: API performance
- **HTTP Status Codes**: Success/error rates

**Access Metrics:**
- Go to web service
- Click **"Metrics"** tab

### Health Checks

Render automatically monitors:
- **Health Check Path**: `/api/v1/health`
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds

**Failed Health Check:**
- Render restarts service automatically
- Check logs for errors

### Alerts (Paid Plans)

Set up alerts for:
- Service down
- High CPU usage
- High memory usage
- Failed deployments

---

## Troubleshooting

### Build Failures

**Error: "Failed to install requirements"**
```
Solution:
1. Check requirements.txt syntax
2. Verify package versions exist
3. Check build logs for specific package errors
```

**Error: "alembic: command not found"**
```
Solution:
1. Ensure alembic is in requirements.txt
2. Check buildCommand in render.yaml includes pip install
```

### Database Connection Issues

**Error: "Could not connect to database"**
```
Solution:
1. Check DATABASE_URL is set correctly (auto from database service)
2. Verify database service is running
3. Check database service name matches in render.yaml
```

**Error: "relation 'user' does not exist"**
```
Solution:
1. Migrations didn't run
2. Check logs for alembic errors
3. Manually run: alembic upgrade head in shell
```

### Application Errors

**Error: "SECRET_KEY must be changed from default"**
```
Solution:
1. Generate new SECRET_KEY (see "Before You Deploy")
2. Set in environment variables
3. Redeploy
```

**Error: "CORS policy blocked"**
```
Solution:
1. Add your frontend domain to BACKEND_CORS_ORIGINS
2. Format: https://yourdomain.com,https://www.yourdomain.com
3. Redeploy
```

**Error: "Internal Server Error (500)"**
```
Solution:
1. Check logs for Python traceback
2. Look for database connection issues
3. Verify all environment variables are set
```

### Performance Issues

**Slow Response Times**
```
Solutions:
1. Upgrade Render plan (more CPU/RAM)
2. Enable Redis for caching
3. Add database indexes
4. Increase Gunicorn workers (default: 4)
```

**High Memory Usage**
```
Solutions:
1. Reduce DB_POOL_SIZE (default: 5)
2. Reduce Gunicorn workers
3. Upgrade to larger plan
```

### Deployment Hangs

**Build stuck on "Installing dependencies"**
```
Solution:
1. Cancel and retry deployment
2. Check for network issues
3. Try removing cached dependencies (Environment > Clear build cache)
```

---

## Updating the Application

### Deploy New Version

**Option 1: Automatic (Recommended)**
```bash
# Make changes locally
git add .
git commit -m "Add new feature"
git push origin main

# Render automatically deploys when main branch updates
```

**Option 2: Manual Deploy**
1. Go to web service in Render dashboard
2. Click **"Manual Deploy"** → **"Deploy latest commit"**

### Rollback to Previous Version

1. **Go to Web Service**
2. **Click "Rollback"** tab
3. **Select Previous Deployment**
4. **Click "Rollback to this version"**

### Database Migrations

**Creating New Migration:**
```bash
# Locally
alembic revision --autogenerate -m "Add new table"

# Commit and push
git add alembic/versions/*
git commit -m "Add migration for new table"
git push origin main

# Render will automatically run:
# alembic upgrade head
```

**Reverting Migration:**
```bash
# Access Render shell
alembic downgrade -1

# Or rollback to specific version
alembic downgrade abc123def456
```

---

## Cost Estimate

### Free Tier
- **Web Service**: Free for 90 days, then $7/month
- **PostgreSQL**: Free for 90 days, then $7/month
- **Total**: $0/month (first 90 days), then $14/month

### Starter Plan (Recommended)
- **Web Service**: $7/month (512MB RAM, shared CPU)
- **PostgreSQL**: $7/month (256MB RAM, 1GB storage)
- **Total**: $14/month

### Standard Plan (Production)
- **Web Service**: $25/month (2GB RAM, 0.5 CPU)
- **PostgreSQL**: $25/month (4GB RAM, 10GB storage)
- **Redis**: $10/month (256MB)
- **Total**: $60/month

---

## Security Checklist

Before going live:

- ✅ **SECRET_KEY** changed from default
- ✅ **FIRST_SUPERUSER_PASSWORD** is strong
- ✅ **DEBUG** is False
- ✅ **Database** is PostgreSQL (not SQLite)
- ✅ **CORS origins** are specific (not wildcard)
- ✅ **HTTPS** enabled (automatic with Render)
- ✅ **.env file** is NOT in repository
- ✅ **Database backups** enabled (Starter plan or higher)
- ✅ **Rate limiting** enabled
- ✅ **Environment** set to "production"

---

## Additional Resources

- **Render Docs**: [https://render.com/docs](https://render.com/docs)
- **FastAPI Docs**: [https://fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Alembic Docs**: [https://alembic.sqlalchemy.org](https://alembic.sqlalchemy.org)
- **PostgreSQL Docs**: [https://www.postgresql.org/docs/](https://www.postgresql.org/docs/)

---

## Support

**Render Support:**
- Community: [https://community.render.com](https://community.render.com)
- Status: [https://status.render.com](https://status.render.com)
- Email: support@render.com (Paid plans)

**Application Issues:**
- Check logs first
- Review this troubleshooting guide
- Open GitHub issue if bug found

---

**Last Updated:** 2024-11-22
**Render Version:** Blueprint v2
**Application Version:** 2.0.0
