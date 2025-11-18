# Production Deployment Guide

This guide covers deploying the FastAPI Starter Template to production environments.

## Table of Contents

- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Environment Configuration](#environment-configuration)
- [Database Setup](#database-setup)
- [Redis Setup](#redis-setup)
- [Deployment Options](#deployment-options)
  - [Docker Deployment](#docker-deployment)
  - [Kubernetes Deployment](#kubernetes-deployment)
  - [Traditional Server Deployment](#traditional-server-deployment)
- [Security Hardening](#security-hardening)
- [Monitoring & Logging](#monitoring--logging)
- [Backup Strategy](#backup-strategy)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

Before deploying to production, ensure you complete ALL items:

### Critical Security Items

- [ ] **Change SECRET_KEY** to a cryptographically secure random value
  ```bash
  # Generate a secure key
  openssl rand -hex 32
  ```
- [ ] **Update default admin credentials** (FIRST_SUPERUSER_EMAIL and FIRST_SUPERUSER_PASSWORD)
- [ ] **Set ENVIRONMENT=production** in your .env file
- [ ] **Disable DEBUG mode** (DEBUG=false)
- [ ] **Disable auto-reload** (RELOAD=false)
- [ ] **Review CORS origins** - only allow trusted frontend URLs
- [ ] **Enable HTTPS/TLS** for all traffic
- [ ] **Review rate limit settings** for your expected traffic

### Infrastructure Items

- [ ] **Configure production database** (PostgreSQL recommended)
- [ ] **Set up Redis** for caching and token revocation
- [ ] **Configure log aggregation** (ELK, Datadog, CloudWatch, etc.)
- [ ] **Set up monitoring** (Prometheus, Grafana, etc.)
- [ ] **Configure backup strategy** for database and Redis
- [ ] **Set up CI/CD pipeline** for automated deployments
- [ ] **Configure SSL certificates** (Let's Encrypt, etc.)
- [ ] **Set up load balancer** (if running multiple instances)

### Application Items

- [ ] **Run database migrations** (if using Alembic)
- [ ] **Test all endpoints** in staging environment
- [ ] **Review audit logging** configuration
- [ ] **Configure email service** (if using password reset)
- [ ] **Review security headers** for your use case
- [ ] **Test token revocation** works with Redis
- [ ] **Verify rate limiting** works correctly

---

## Environment Configuration

### Production Environment Variables

Create a `.env` file with production values:

```bash
# ==============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION
# ==============================================================================

# Application
ENVIRONMENT=production
APP_NAME="Your App Name"
APP_VERSION="1.0.0"
DEBUG=false
RELOAD=false

# Server
HOST=0.0.0.0
PORT=8000

# Database - PostgreSQL (Recommended)
DATABASE_URL=postgresql+asyncpg://user:password@db-host:5432/production_db
DB_ECHO=false
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Security - CRITICAL: Change these!
SECRET_KEY=<your-generated-secret-key-here>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis - REQUIRED for production
REDIS_ENABLED=true
REDIS_HOST=redis-host
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<your-redis-password>

# CORS - Only allow trusted origins
BACKEND_CORS_ORIGINS=https://your-frontend.com,https://www.your-frontend.com

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# Admin User
FIRST_SUPERUSER_EMAIL=admin@yourcompany.com
FIRST_SUPERUSER_PASSWORD=<secure-password>
FIRST_SUPERUSER_FULLNAME=System Administrator

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API
API_V1_PREFIX=/api/v1
PROJECT_NAME="Your App Name"
```

### Secrets Management

**Never commit secrets to version control!**

Use a secrets manager:

- **AWS**: AWS Secrets Manager or Systems Manager Parameter Store
- **GCP**: Secret Manager
- **Azure**: Key Vault
- **Kubernetes**: Kubernetes Secrets
- **HashiCorp**: Vault
- **Docker**: Docker Secrets

Example with AWS Secrets Manager:

```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# In your config
secrets = get_secret('production/fastapi-app')
SECRET_KEY = secrets['SECRET_KEY']
DATABASE_URL = secrets['DATABASE_URL']
```

---

## Database Setup

### PostgreSQL Setup (Recommended)

1. **Install PostgreSQL** (version 13+)

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Or use managed service:
# - AWS RDS
# - Google Cloud SQL
# - Azure Database for PostgreSQL
# - DigitalOcean Managed Databases
```

2. **Create Database and User**

```sql
-- Connect as postgres user
sudo -u postgres psql

-- Create database
CREATE DATABASE production_db;

-- Create user
CREATE USER app_user WITH PASSWORD 'secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE production_db TO app_user;

-- Exit
\q
```

3. **Configure Connection**

```bash
# In .env
DATABASE_URL=postgresql+asyncpg://app_user:secure_password@localhost:5432/production_db
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

4. **Run Migrations**

```bash
# If using Alembic
alembic upgrade head

# The app will auto-create tables on first run
# But migrations are recommended for production
```

### Database Performance Tuning

```sql
-- Add indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
```

---

## Redis Setup

### Redis Installation

1. **Install Redis** (version 6+)

```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Or use managed service:
# - AWS ElastiCache
# - Google Cloud Memorystore
# - Azure Cache for Redis
# - Redis Cloud
```

2. **Configure Redis for Production**

Edit `/etc/redis/redis.conf`:

```conf
# Security
bind 127.0.0.1
requirepass <strong-password>

# Persistence (for token blacklist durability)
save 900 1
save 300 10
save 60 10000

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

3. **Enable and Start Redis**

```bash
sudo systemctl enable redis-server
sudo systemctl start redis-server
sudo systemctl status redis-server
```

4. **Configure Application**

```bash
# In .env
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<your-redis-password>
```

### Redis Monitoring

```bash
# Monitor Redis performance
redis-cli --stat

# Check memory usage
redis-cli INFO memory

# Monitor commands
redis-cli MONITOR
```

---

## Deployment Options

### Docker Deployment

#### 1. Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://app_user:password@db:5432/production_db
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    env_file:
      - .env
    depends_on:
      - db
      - redis
    restart: unless-stopped
    networks:
      - app-network

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=app_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=production_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass your-redis-password
    volumes:
      - redis-data:/data
    restart: unless-stopped
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - app-network

volumes:
  postgres-data:
  redis-data:

networks:
  app-network:
    driver: bridge
```

#### 3. Build and Run

```bash
# Build image
docker build -t fastapi-app:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Kubernetes Deployment

#### 1. Create Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-app
  labels:
    app: fastapi-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fastapi-app
  template:
    metadata:
      labels:
        app: fastapi-app
    spec:
      containers:
      - name: fastapi-app
        image: your-registry/fastapi-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: redis-password
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  selector:
    app: fastapi-app
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
stringData:
  database-url: "postgresql+asyncpg://user:password@postgres:5432/db"
  secret-key: "your-secret-key-here"
  redis-password: "your-redis-password"
```

#### 2. Deploy to Kubernetes

```bash
# Create secrets
kubectl apply -f k8s/secrets.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/fastapi-app

# Scale deployment
kubectl scale deployment/fastapi-app --replicas=5
```

### Traditional Server Deployment

#### 1. Install Dependencies

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11+
sudo apt-get install python3.11 python3.11-venv python3-pip

# Install PostgreSQL and Redis
sudo apt-get install postgresql redis-server

# Install Nginx
sudo apt-get install nginx
```

#### 2. Set Up Application

```bash
# Create app user
sudo useradd -m -s /bin/bash appuser

# Create app directory
sudo mkdir -p /opt/fastapi-app
sudo chown appuser:appuser /opt/fastapi-app

# Switch to app user
sudo su - appuser

# Clone repository
cd /opt/fastapi-app
git clone <your-repo> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with production values
```

#### 3. Configure Systemd Service

Create `/etc/systemd/system/fastapi.service`:

```ini
[Unit]
Description=FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=appuser
Group=appuser
WorkingDirectory=/opt/fastapi-app
Environment="PATH=/opt/fastapi-app/venv/bin"
ExecStart=/opt/fastapi-app/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi
sudo systemctl start fastapi
sudo systemctl status fastapi
```

#### 4. Configure Nginx

Create `/etc/nginx/sites-available/fastapi`:

```nginx
upstream fastapi {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Proxy to FastAPI
    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Client max body size
    client_max_body_size 10M;
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/fastapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Security Hardening

### SSL/TLS Configuration

Use Let's Encrypt for free SSL certificates:

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

### Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check status
sudo ufw status
```

### Application Security

1. **Review CORS Settings**

```python
# Only allow trusted origins
BACKEND_CORS_ORIGINS=https://your-frontend.com
```

2. **Enable Rate Limiting**

```python
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

3. **Regular Updates**

```bash
# Update dependencies regularly
pip install --upgrade -r requirements.txt

# Monitor security advisories
pip-audit
```

---

## Monitoring & Logging

### Application Logging

Configure structured JSON logging:

```python
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Log Aggregation

**Option 1: ELK Stack**

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: elasticsearch:8.5.0
    environment:
      - discovery.type=single-node
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data

  logstash:
    image: logstash:8.5.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:8.5.0
    ports:
      - "5601:5601"
```

**Option 2: Cloud Services**

- AWS CloudWatch Logs
- Google Cloud Logging
- Azure Monitor
- Datadog
- New Relic

### Health Checks

Add health check endpoint:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
```

Monitor with:

```bash
# Simple check
curl http://localhost:8000/health

# Kubernetes liveness probe
# Docker health check
# Load balancer health check
```

---

## Backup Strategy

### Database Backups

**Automated PostgreSQL Backups**

Create `/opt/scripts/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="production_db"

# Create backup
pg_dump -U app_user -h localhost $DB_NAME | gzip > "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# Upload to S3 (optional)
aws s3 cp "$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz" s3://your-bucket/backups/
```

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * /opt/scripts/backup_db.sh
```

### Redis Backups

Redis automatically saves to disk (RDB/AOF). Configure in `redis.conf`:

```conf
# Snapshots
save 900 1
save 300 10
save 60 10000

# Append-only file
appendonly yes
appendfsync everysec
```

---

## Performance Optimization

### Application Performance

1. **Use Multiple Workers**

```bash
# Systemd service or Docker
uvicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

2. **Database Connection Pooling**

```python
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

3. **Enable Redis Caching**

```python
REDIS_ENABLED=true
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@test.com';

-- Regular vacuum
VACUUM ANALYZE;
```

### Load Balancing

Use Nginx or cloud load balancers to distribute traffic across multiple instances.

---

## Troubleshooting

### Common Issues

**1. Database Connection Errors**

```bash
# Check database is running
sudo systemctl status postgresql

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL
```

**2. Redis Connection Errors**

```bash
# Check Redis is running
sudo systemctl status redis-server

# Test connection
redis-cli -h localhost -p 6379 -a your-password ping
```

**3. Application Not Starting**

```bash
# Check logs
journalctl -u fastapi -f

# Check permissions
ls -la /opt/fastapi-app

# Check Python environment
source venv/bin/activate
python --version
```

**4. High Memory Usage**

```bash
# Check application memory
ps aux | grep uvicorn

# Reduce workers
uvicorn app.main:app --workers 2

# Check database connections
SELECT count(*) FROM pg_stat_activity;
```

### Debug Mode

For troubleshooting only (NEVER in production):

```bash
# Enable debug logging
LOG_LEVEL=DEBUG

# Check specific component
tail -f /var/log/fastapi/app.log | grep ERROR
```

---

## Performance Benchmarks

Expected performance (4 workers, 2 CPU cores, 4GB RAM):

- **Simple GET requests**: 1000-2000 req/s
- **Authenticated endpoints**: 500-1000 req/s
- **Database queries**: 200-500 req/s
- **Average latency**: <50ms

Run your own benchmarks:

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test endpoint
ab -n 10000 -c 100 http://localhost:8000/health
```

---

## Support

For deployment issues:

1. Check application logs: `journalctl -u fastapi -f`
2. Check database logs: `tail -f /var/log/postgresql/postgresql-15-main.log`
3. Check Redis logs: `tail -f /var/log/redis/redis-server.log`
4. Check Nginx logs: `tail -f /var/log/nginx/error.log`

---

**Happy Deploying!** 🚀
