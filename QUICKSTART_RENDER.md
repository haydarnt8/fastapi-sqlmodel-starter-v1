# Quick Start: Deploy to Render

**5-minute guide** to deploy FastAPI Supply Chain Management to Render.

---

## Prerequisites ✅

- [ ] GitHub account
- [ ] Render account ([sign up free](https://render.com))
- [ ] Code pushed to GitHub repository

---

## Step 1: Generate Secrets (2 minutes)

### 1.1 Generate SECRET_KEY
```bash
openssl rand -hex 32
```
**Copy the output** - you'll need it for Render.

### 1.2 Create Admin Password
```bash
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(20)))"
```
**Save this password** - this is your admin login.

---

## Step 2: Update Configuration (1 minute)

### 2.1 Edit render.yaml

Open `render.yaml` and update line 22:
```yaml
branch: main  # Change to your actual branch name if different
```

Update line 39:
```yaml
value: https://yourdomain.com  # Change to your frontend URL
```

Update line 44:
```yaml
value: admin@yourdomain.com  # Change to your email
```

### 2.2 Commit and Push
```bash
git add render.yaml
git commit -m "Configure Render deployment"
git push origin main
```

---

## Step 3: Deploy on Render (2 minutes)

### 3.1 Create Blueprint

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Select your repository from the list
5. Click **"Apply"** (Render detects `render.yaml` automatically)

### 3.2 Configure Secrets

While deployment is in progress:

1. Click on your **web service** name
2. Go to **"Environment"** tab
3. Add new environment variable:
   - **Key**: `FIRST_SUPERUSER_PASSWORD`
   - **Value**: (paste the password from Step 1.2)
   - Click **"Save Changes"**

**Optional**: If you didn't use `generateValue: true` for SECRET_KEY in render.yaml:
   - **Key**: `SECRET_KEY`
   - **Value**: (paste the key from Step 1.1)
   - Click **"Save Changes"**

---

## Step 4: Verify Deployment (30 seconds)

### 4.1 Check Build Logs

In your web service, click **"Logs"** tab.

**Wait for these messages:**
```
✓ Database initialized
✓ Database seeded with initial data
🚀 Supply Chain Management API is ready!
```

### 4.2 Test Health Endpoint

Your app URL will be: `https://your-app-name.onrender.com`

Open in browser:
```
https://your-app-name.onrender.com/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected"
}
```

### 4.3 Access API Documentation

Open:
```
https://your-app-name.onrender.com/docs
```

You should see **Swagger UI** with all endpoints!

---

## Step 5: Test Admin Login (30 seconds)

### 5.1 Login via Swagger UI

1. Open `/docs` (from Step 4.3)
2. Find **POST /api/v1/auth/login**
3. Click **"Try it out"**
4. Enter:
   ```json
   {
     "email": "admin@yourdomain.com",
     "password": "your-password-from-step-1.2"
   }
   ```
5. Click **"Execute"**

**You should get:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### 5.2 Authorize Swagger

1. Copy the `access_token` value
2. Click **"Authorize"** button (top right)
3. Paste token in format: `Bearer your-token-here`
4. Click **"Authorize"**

Now you can test all protected endpoints! 🎉

---

## That's It! 🚀

Your API is now live at:
```
https://your-app-name.onrender.com
```

**API Documentation:**
```
https://your-app-name.onrender.com/docs
```

---

## Next Steps

### Configure Custom Domain (Optional)

1. Go to web service → **Settings** tab
2. Scroll to **Custom Domain**
3. Add your domain: `api.yourdomain.com`
4. Update DNS with provided CNAME record

### Enable Redis (Optional)

For production, enable Redis for token revocation:

1. Edit `render.yaml` - uncomment Redis service section
2. Update web service environment:
   ```yaml
   - key: REDIS_ENABLED
     value: true
   ```
3. Push changes and redeploy

### Set Up Monitoring

1. Go to web service → **Metrics** tab
2. View CPU, memory, response times
3. Set up alerts (paid plans)

---

## Common Issues

### "Database connection failed"
- **Cause**: Database service not ready
- **Fix**: Wait 30 seconds, database is still starting

### "SECRET_KEY must be changed from default"
- **Cause**: SECRET_KEY not set or using default
- **Fix**: Set SECRET_KEY in environment variables (Step 3.2)

### "CORS policy blocked"
- **Cause**: Frontend URL not in BACKEND_CORS_ORIGINS
- **Fix**: Add your frontend URL to environment variable

### Build fails
- **Cause**: Missing dependencies or syntax error
- **Fix**: Check logs, verify requirements.txt syntax

---

## Costs

### Free Tier
- **Web Service**: Free for 90 days
- **PostgreSQL**: Free for 90 days
- **After 90 days**: $14/month total

### Paid Plans
- **Starter**: $14/month (recommended for production)
- **Standard**: $60/month (high traffic)

---

## Support

**Full Documentation:**
- [Complete Render Deployment Guide](docs/RENDER_DEPLOYMENT.md)
- [API Documentation](docs/AUTHENTICATION.md)
- [Roles and Permissions](docs/ROLES_AND_PERMISSIONS.md)

**Render Help:**
- [Community Forum](https://community.render.com)
- [Status Page](https://status.render.com)

---

**Deployment Time**: ~5 minutes
**First Deploy**: Free for 90 days
**Production Ready**: ✅ Yes
