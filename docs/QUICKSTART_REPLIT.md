# Quick Start: Deploy to Replit

**5-minute guide** to deploy FastAPI Supply Chain Management to Replit - **100% FREE, NO CREDIT CARD!**

---

## Why Replit?

✅ **Completely FREE** - No credit card ever!  
✅ **Easy setup** - Import from GitHub in 1 click  
✅ **PostgreSQL included** - Via Neon integration  
✅ **No configuration** - Works out of the box  
❌ **Sleeps after inactivity** - Takes ~10 seconds to wake  
❌ **Lower performance** - Shared resources  

**Perfect for:** Testing, demos, learning, portfolios  
**Not ideal for:** High-traffic production apps  

---

## Step 1: Import from GitHub (1 minute)

### 1.1 Go to Replit

Open: [https://replit.com](https://replit.com)

### 1.2 Create Account (if needed)

- Click **"Sign up"**
- Use GitHub, Google, or email
- **NO CREDIT CARD REQUIRED!**

### 1.3 Import Repository

1. Click **"+ Create Repl"**
2. Select **"Import from GitHub"**
3. Paste your repository URL:
   ```
   https://github.com/haydarnt8/fastapi-sqlmodel-starter-v1
   ```
4. Select branch: **Supply-Chain**
5. Click **"Import from GitHub"**

Replit will automatically detect Python and configure everything!

---

## Step 2: Set Up PostgreSQL Database (2 minutes)

### 2.1 Install Neon PostgreSQL

1. In your Repl, click **"Tools"** (left sidebar)
2. Search for **"PostgreSQL"** or **"Neon"**
3. Click **"PostgreSQL by Neon"**
4. Click **"Add to Repl"**
5. Click **"Create database"**

**Neon will create a free PostgreSQL database for you!**

### 2.2 Get Database URL

After database is created:
1. Click on the PostgreSQL tool
2. Copy the **"Connection String"**
3. It looks like: `postgres://user:pass@host/database`

---

## Step 3: Configure Environment Variables (1 minute)

### 3.1 Open Secrets

1. Click **"Tools"** → **"Secrets"** (lock icon)
2. Or click the lock icon in left sidebar

### 3.2 Add Required Secrets

Add these environment variables (click "+ New secret" for each):

**DATABASE_URL:**
```
paste-your-neon-connection-string-here
```

**SECRET_KEY:**
```bash
# Generate with this command in Shell tab:
python -c "import secrets; print(secrets.token_hex(32))"
```

**FIRST_SUPERUSER_EMAIL:**
```
admin@example.com
```

**FIRST_SUPERUSER_PASSWORD:**
```
YourSecurePassword123!
```

**ENVIRONMENT:**
```
production
```

**REDIS_ENABLED:**
```
false
```

### 3.3 Optional Secrets

**BACKEND_CORS_ORIGINS** (if you have a frontend):
```
["https://yourdomain.com"]
```

---

## Step 4: Run the Application (30 seconds)

### 4.1 Install Dependencies

Replit should auto-install, but if not:
1. Click **"Shell"** tab
2. Run:
   ```bash
   pip install -r requirements.txt
   ```

### 4.2 Run Migrations

In Shell tab:
```bash
alembic upgrade head
```

This creates all database tables and seeds initial data.

### 4.3 Start the App

Click the big green **"Run"** button at the top!

**Replit will:**
1. Start your FastAPI app
2. Show it in the webview
3. Give you a public URL

---

## Step 5: Access Your API (30 seconds)

### 5.1 Get Your URL

After clicking "Run", you'll see:
```
https://fastapi-supply-chain-yourname.replit.app
```

### 5.2 Test Health Endpoint

Click **"Open in new tab"** or visit:
```
https://your-repl-url.replit.app/api/v1/health
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

### 5.3 Access API Documentation

Visit:
```
https://your-repl-url.replit.app/docs
```

You should see **Swagger UI** with all your endpoints!

---

## Step 6: Test Admin Login

### Using Swagger UI:

1. Go to `/docs`
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
https://your-repl-name.replit.app
```

**Features:**
- ✅ 100% FREE forever
- ✅ NO credit card needed
- ✅ PostgreSQL database included
- ✅ Automatic HTTPS
- ✅ Public URL
- ✅ Easy updates (just click "Run" again)

---

## Important Notes

### App Sleeps After Inactivity

**Problem:** App sleeps after ~1 hour of no requests  
**Solution:** First request after sleep takes ~10 seconds  
**Keep Alive:** Use a free service like [UptimeRobot](https://uptimerobot.com) to ping every 5 minutes

### Performance Limitations

- **Shared CPU** - Slower than dedicated servers
- **Limited RAM** - May restart under heavy load
- **Not for production** - Use for testing/demos only

### Making Changes

**To update your app:**
1. Make changes in Replit editor
2. Click **"Run"** button again
3. App automatically redeploys!

**Or sync from GitHub:**
1. Push changes to GitHub
2. In Repl Shell: `git pull origin Supply-Chain`
3. Click **"Run"**

---

## Useful Replit Features

### Shell Commands

Access Shell tab to run commands:

```bash
# View logs
# (automatically shown in Console tab)

# Run migrations
alembic upgrade head

# Check database
alembic current

# Create new admin user
python -c "from app.db.init_db import create_first_superuser; import asyncio; asyncio.run(create_first_superuser())"

# Test database connection
python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('your-db-url'))"
```

### Database Management

**View data in Neon:**
1. Go to [neon.tech](https://neon.tech)
2. Login (same account as Replit)
3. Select your database
4. Use SQL Editor

**Or use pgAdmin:**
- Install [pgAdmin](https://www.pgadmin.org/)
- Connect using your Neon connection string

### Secrets Management

**View/Edit secrets:**
1. Click lock icon (Secrets)
2. Edit any value
3. Click "Run" to apply changes

**DON'T:**
- Commit secrets to GitHub
- Share your Repl publicly with secrets exposed

---

## Troubleshooting

### "Module not found" Error

**Solution:**
```bash
# In Shell tab
pip install -r requirements.txt
# Then click Run
```

### "Database connection failed"

**Check:**
1. DATABASE_URL secret is set correctly
2. Neon database is running (check neon.tech)
3. Connection string format: `postgres://user:pass@host/db`

**Fix:**
```bash
# Test connection in Shell
python -c "import os; print(os.environ.get('DATABASE_URL'))"
```

### "Alembic migration failed"

**Solution:**
```bash
# Reset migrations (Shell tab)
alembic downgrade base
alembic upgrade head
```

### "App won't start"

**Check Console tab for errors**

Common fixes:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.11

# Restart Repl
# Stop (Ctrl+C in Console) then Run again
```

### App is Very Slow

**This is normal for free tier!**

**Reasons:**
- Shared resources
- Cold starts after sleep
- Limited CPU

**Alternatives if speed matters:**
- Use Fly.io/Render (requires card, better performance)
- Upgrade Replit (paid plans available)

---

## Upgrading Your App

### From GitHub:

```bash
# In Shell tab
git pull origin Supply-Chain
# Then click Run
```

### Direct in Replit:

1. Edit files in Replit editor
2. Click "Run"
3. Changes apply immediately!

---

## Custom Domain (Optional)

**Replit allows custom domains on paid plans only**

**Free alternative:**
- Use the provided `.replit.app` URL
- Or use a URL shortener (bit.ly, tinyurl.com)

---

## Monitoring

### Built-in Monitoring:

- **Console tab**: Live logs
- **Resources tab**: CPU/RAM usage  
- **Always On**: Upgrade feature (paid)

### External Monitoring:

**Free options:**
- [UptimeRobot](https://uptimerobot.com) - Ping every 5 min
- [Freshping](https://www.freshworks.com/website-monitoring/) - Free monitoring
- [StatusCake](https://www.statuscake.com/) - Free tier

---

## Cost

**Forever FREE:**
- ✅ Unlimited public Repls
- ✅ PostgreSQL via Neon
- ✅ 1GB storage
- ✅ Community support

**Paid Plans (optional):**
- **Hacker** ($7/month): More CPU, Always On
- **Pro** ($20/month): Private Repls, better performance

---

## Comparison

| Feature | Replit Free | Fly.io Free | Render Free |
|---------|-------------|-------------|-------------|
| **Credit Card** | ❌ Not needed | ✅ Required | ✅ Required |
| **Cost** | FREE forever | FREE forever | FREE 90 days |
| **RAM** | ~512MB | 256MB | 512MB |
| **PostgreSQL** | ✅ Via Neon | ✅ Included | ✅ Included |
| **Auto-sleep** | Yes (1 hour) | No | Yes (15 min) |
| **Performance** | Low | Medium | Medium-High |
| **Best for** | Learning/Demos | Production | Production |

---

## Next Steps

1. ✅ **Test all endpoints** in `/docs`
2. ✅ **Create your first restaurant/supplier**
3. ✅ **Set up UptimeRobot** to prevent sleep
4. ✅ **Share your API** with the `.replit.app` URL
5. ✅ **Monitor logs** in Console tab

---

## Support

**Replit Help:**
- [Documentation](https://docs.replit.com)
- [Community](https://ask.replit.com)
- [Discord](https://replit.com/discord)

**Neon Help:**
- [Docs](https://neon.tech/docs)
- [Discord](https://discord.gg/neon)

**App Issues:**
- Check Console tab for errors
- Review this troubleshooting guide

---

**Your app is live and FREE!** 🎉

**URL:** `https://your-repl.replit.app/docs`

Enjoy your free FastAPI deployment!
