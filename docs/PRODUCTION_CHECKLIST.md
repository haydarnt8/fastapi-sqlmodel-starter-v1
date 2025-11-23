# 🚀 Production Deployment Checklist

**Application:** Al-Fatih API
**Version:** 2.0.1
**Date:** 2025-01-15

---

## ✅ Pre-Deployment Checklist

### 🔐 **1. Security Configuration** (CRITICAL)

- [ ] **Change SECRET_KEY**
  ```bash
  # Generate a secure secret key (min 32 characters)
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  # Set in .env:
  SECRET_KEY="your-generated-secret-here"
  ```

- [ ] **Change Admin Password**
  ```bash
  # In .env, change from default:
  FIRST_SUPERUSER_PASSWORD="YourSecurePassword123!"
  # NOT: changeme123, admin, or password
  ```

- [ ] **Disable DEBUG Mode**
  ```bash
  DEBUG=false
  ```

- [ ] **Configure CORS Origins**
  ```bash
  # NOT wildcard! Specify your domains:
  BACKEND_CORS_ORIGINS='["https://yourdomain.com", "https://www.yourdomain.com"]'
  ```

---

### 🗄️ **2. Database Configuration** (CRITICAL)

- [ ] **Use PostgreSQL** (NOT SQLite)
  ```bash
  DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/dbname"
  ```

- [ ] **Run Database Migrations**
  ```bash
  .venv/bin/alembic upgrade head
  ```

- [ ] **Verify Database Connection**
  ```bash
  # Test connection before deployment
  .venv/bin/python -c "from app.db.session import AsyncSessionLocal; import asyncio; asyncio.run(AsyncSessionLocal().__anext__())"
  ```

- [ ] **Configure Database Backups**
  - Set up automated daily backups
  - Test backup restoration process
  - Document backup retention policy

---

### 🔴 **3. Redis Configuration** (IMPORTANT)

- [ ] **Enable Redis** (for token blacklisting)
  ```bash
  REDIS_ENABLED=true
  REDIS_HOST=localhost
  REDIS_PORT=6379
  REDIS_PASSWORD="your-redis-password"
  REDIS_DB=0
  ```

- [ ] **Test Redis Connection**
  ```bash
  redis-cli ping
  # Should return: PONG
  ```

> **Note:** If Redis is disabled, token revocation (logout) won't work properly.

---

### 🌐 **4. Environment Variables** (REQUIRED)

Create `.env` file with these settings:

```bash
# Application
ENVIRONMENT=production
APP_NAME="Al-Fatih API"
APP_VERSION="2.0.1"
DEBUG=false

# Security
SECRET_KEY="your-secure-secret-key-min-32-chars"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL="postgresql+asyncpg://user:password@host:5432/dbname"

# Redis
REDIS_ENABLED=true
REDIS_HOST="localhost"
REDIS_PORT=6379
REDIS_PASSWORD="your-redis-password"
REDIS_DB=0

# CORS
BACKEND_CORS_ORIGINS='["https://yourdomain.com"]'

# Admin User
FIRST_SUPERUSER_EMAIL="admin@yourdomain.com"
FIRST_SUPERUSER_PASSWORD="SecurePassword123!"
FIRST_SUPERUSER_FULLNAME="Admin User"

# Server
HOST="0.0.0.0"
PORT=8000
```

---

### 📊 **5. Monitoring & Logging** (IMPORTANT)

- [ ] **Configure Log Aggregation**
  - Set up centralized logging (ELK, CloudWatch, Datadog, etc.)
  - Logs are in JSON format for easy parsing

- [ ] **Set Up Health Check Monitoring**
  ```bash
  # Monitor this endpoint:
  GET https://your-api.com/health

  # Should return:
  {
    "status": "healthy",
    "database": "connected",
    "redis": "connected",
    ...
  }
  ```

- [ ] **Configure Alerts**
  - Alert on `status != "healthy"`
  - Alert on 5xx error rate > 1%
  - Alert on slow response times (>2s)

- [ ] **Error Tracking** (Optional but recommended)
  - Set up Sentry, Rollbar, or similar
  - Configure error notifications

---

### 🧪 **6. Testing** (BEFORE DEPLOYMENT)

- [ ] **Run All Tests**
  ```bash
  .venv/bin/pytest -v
  ```

- [ ] **Test Health Endpoint**
  ```bash
  curl https://your-staging-api.com/health | jq
  ```

- [ ] **Test Authentication Flow**
  ```bash
  # Register
  curl -X POST https://your-api.com/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"Test123!","full_name":"Test User"}'

  # Login
  curl -X POST https://your-api.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"Test123!"}'
  ```

- [ ] **Load Testing** (Optional)
  ```bash
  # Use tools like: locust, k6, or ab
  ab -n 1000 -c 10 https://your-api.com/health
  ```

---

### 🐳 **7. Docker Deployment** (If using Docker)

- [ ] **Build Docker Image**
  ```bash
  docker build -t al-fatih-api:2.0.1 .
  ```

- [ ] **Test Docker Container Locally**
  ```bash
  docker-compose up
  # Access: http://localhost:8000/health
  ```

- [ ] **Configure Docker Secrets**
  - Don't hardcode secrets in docker-compose.yml
  - Use Docker secrets or environment files

- [ ] **Set Up Docker Health Checks**
  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
  ```

---

### 🔒 **8. SSL/TLS Configuration** (CRITICAL)

- [ ] **Enable HTTPS**
  - Configure reverse proxy (Nginx, Caddy, etc.)
  - Obtain SSL certificate (Let's Encrypt, etc.)

- [ ] **Verify HSTS Header**
  ```bash
  curl -I https://your-api.com/health | grep "Strict-Transport-Security"
  # Should see: Strict-Transport-Security header
  ```

- [ ] **Test SSL Configuration**
  - Use: https://www.ssllabs.com/ssltest/
  - Aim for A+ rating

---

### 📝 **9. Documentation** (RECOMMENDED)

- [ ] **Document API Endpoints**
  - Swagger UI available at: `/docs`
  - ReDoc available at: `/redoc`

- [ ] **Create Runbook**
  - Common issues and solutions
  - Rollback procedures
  - Contact information

- [ ] **Document Environment Variables**
  - Required vs optional
  - Default values
  - Examples

---

### 🚨 **10. Rollback Plan** (CRITICAL)

- [ ] **Document Rollback Steps**
  ```bash
  # 1. Stop new deployment
  # 2. Revert to previous version
  # 3. Run database migration rollback (if needed):
  .venv/bin/alembic downgrade -1
  ```

- [ ] **Keep Previous Version Available**
  - Tag Docker images
  - Keep previous deployment artifacts

- [ ] **Test Rollback Procedure**
  - Practice rollback in staging

---

## 🎯 Post-Deployment Verification

### Immediately After Deployment

1. **✅ Check Health Endpoint**
   ```bash
   curl https://your-api.com/health
   # Expect: {"status": "healthy", ...}
   ```

2. **✅ Verify Database Connection**
   - Check health endpoint shows `"database": "connected"`

3. **✅ Verify Redis Connection** (if enabled)
   - Check health endpoint shows `"redis": "connected"`

4. **✅ Test Authentication**
   - Login as admin
   - Create test user
   - Test token refresh

5. **✅ Check Logs**
   ```bash
   # Look for errors or warnings
   tail -f /path/to/logs/app.log
   ```

6. **✅ Monitor Error Rates**
   - Check for spike in 5xx errors
   - Monitor response times

---

### First 24 Hours

- [ ] **Monitor CPU/Memory Usage**
- [ ] **Check Database Connection Pool**
- [ ] **Verify Redis is Working** (test logout/token revocation)
- [ ] **Review Application Logs**
- [ ] **Check for Memory Leaks**
- [ ] **Monitor API Response Times**

---

### First Week

- [ ] **Review Error Logs**
- [ ] **Analyze Performance Metrics**
- [ ] **Check Database Query Performance**
- [ ] **Review Security Logs**
- [ ] **Gather User Feedback**

---

## 🔧 Common Issues & Solutions

### Issue: Application Won't Start

**Symptom:** App crashes on startup
```
RuntimeError: Production validation failed
```

**Solution:** Check environment variables
```bash
# Review startup logs for specific validation errors
# Fix the reported configuration issues
```

---

### Issue: Database Connection Failed

**Symptom:** Health endpoint shows `"database": "disconnected"`

**Solutions:**
1. Verify DATABASE_URL is correct
2. Check database server is running
3. Verify firewall rules allow connection
4. Check database credentials

---

### Issue: Redis Connection Failed

**Symptom:** Health endpoint shows `"redis": "disconnected"`

**Solutions:**
1. Verify Redis is running: `redis-cli ping`
2. Check REDIS_HOST and REDIS_PORT
3. Verify REDIS_PASSWORD (if set)
4. Check firewall rules

---

### Issue: High Response Times

**Symptom:** X-Process-Time header > 1s

**Solutions:**
1. Check database query performance
2. Review N+1 query issues
3. Add database indexes
4. Enable Redis caching
5. Scale horizontally (add more instances)

---

## 📊 Performance Benchmarks

### Expected Performance (Single Instance)

| Metric | Target | Acceptable |
|--------|--------|------------|
| Health check | < 50ms | < 100ms |
| Login | < 200ms | < 500ms |
| User CRUD | < 150ms | < 300ms |
| Role assignment | < 200ms | < 400ms |

### Resource Usage (Single Instance)

| Resource | Expected | Max |
|----------|----------|-----|
| CPU | 10-30% | 80% |
| Memory | 200-500MB | 1GB |
| DB Connections | 5-20 | 100 |

---

## 🔐 Security Checklist

- [x] SECRET_KEY changed from default
- [x] Admin password changed from default
- [x] DEBUG mode disabled
- [x] CORS configured (not wildcard)
- [x] HTTPS enabled
- [x] Security headers configured
- [x] Rate limiting enabled
- [x] SQL injection protection (SQLAlchemy ORM)
- [ ] DDoS protection (Cloudflare, etc.)
- [ ] WAF configured (optional)
- [ ] Penetration testing completed (optional)

---

## 📞 Support & Contacts

### Development Team
- **Primary:** [Your Team]
- **On-Call:** [Phone/Email]

### Infrastructure
- **Database Admin:** [Contact]
- **DevOps:** [Contact]

### Emergency Procedures
1. Check #incidents Slack channel
2. Page on-call engineer
3. Follow runbook procedures

---

## ✅ Sign-Off

- [ ] **Developer:** All code changes reviewed and tested
- [ ] **QA:** All tests passing, manual testing complete
- [ ] **DevOps:** Infrastructure ready, monitoring configured
- [ ] **Security:** Security review complete, secrets secured
- [ ] **Manager:** Approved for production deployment

---

**Deployment Approved By:** ________________
**Date:** ________________
**Version Deployed:** ________________

---

## 🎉 You're Ready to Deploy!

Once all checkboxes are complete and sign-offs obtained, proceed with deployment.

**Good luck! 🚀**
