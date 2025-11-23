#!/usr/bin/env python3
"""
Generate environment variables for Railway deployment.

This script generates secure values for production deployment and outputs
them in a format ready to paste into Railway's environment variables section.
"""

import secrets
import sys


def generate_secret_key(length: int = 32) -> str:
    """Generate a cryptographically secure secret key."""
    return secrets.token_hex(length)


def generate_railway_env_vars():
    """Generate all required environment variables for Railway."""

    secret_key = generate_secret_key()

    print("=" * 80)
    print("RAILWAY ENVIRONMENT VARIABLES")
    print("=" * 80)
    print()
    print("Copy and paste these into Railway's Variables section:")
    print("(Go to: Your Service → Variables → Raw Editor)")
    print()
    print("-" * 80)
    print()

    env_vars = f"""# ==============================================================================
# PRODUCTION ENVIRONMENT CONFIGURATION FOR RAILWAY
# ==============================================================================

# Database - PostgreSQL (Auto-populated by Railway)
DATABASE_URL=${{{{Postgres.DATABASE_URL}}}}

# Application Settings
ENVIRONMENT=production
APP_NAME=FastAPI Supply Chain
DEBUG=false
RELOAD=false

# Security - CRITICAL: Generated secure key
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Admin User - CHANGE THESE!
FIRST_SUPERUSER_EMAIL=admin@example.com
FIRST_SUPERUSER_PASSWORD=ChangeThisSecurePassword123!
FIRST_SUPERUSER_FULLNAME=System Administrator

# Redis - Disabled (enable if you add Redis service)
REDIS_ENABLED=false

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# CORS - Update with your frontend URL
BACKEND_CORS_ORIGINS=["https://your-frontend.com"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# API Configuration
API_V1_PREFIX=/api/v1
PROJECT_NAME=FastAPI Supply Chain Management
"""

    print(env_vars)
    print()
    print("-" * 80)
    print()
    print("IMPORTANT NOTES:")
    print()
    print("1. ✅ SECRET_KEY has been generated securely")
    print(f"   Generated key: {secret_key}")
    print()
    print("2. ⚠️  CHANGE the FIRST_SUPERUSER_PASSWORD before deploying!")
    print("   Current: ChangeThisSecurePassword123!")
    print()
    print("3. 📦 Make sure you've added PostgreSQL service in Railway:")
    print("   Railway Dashboard → + New → Database → PostgreSQL")
    print()
    print("4. 🔗 DATABASE_URL uses Railway's template variable:")
    print("   ${{Postgres.DATABASE_URL}} will be auto-populated")
    print()
    print("5. 🌐 Update BACKEND_CORS_ORIGINS with your actual frontend URL")
    print()
    print("6. 💾 To add these to Railway:")
    print("   a. Go to your service → Variables tab")
    print("   b. Click 'Raw Editor' button")
    print("   c. Paste the entire configuration above")
    print("   d. Click 'Update Variables'")
    print()
    print("=" * 80)
    print()

    # Also save to file
    with open(".env.railway", "w") as f:
        f.write(env_vars)

    print("✅ Configuration also saved to: .env.railway")
    print("   (DO NOT commit this file to git!)")
    print()


if __name__ == "__main__":
    try:
        generate_railway_env_vars()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
