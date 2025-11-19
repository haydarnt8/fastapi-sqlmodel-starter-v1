# Implementation Roadmap: Restaurant Supply Chain System

**Project:** Restaurant Supply Chain Ordering Platform for Iraq
**Timeline:** 12 weeks to MVP
**Team:** Backend (2), Frontend (2), Mobile (2), QA (1), DevOps (1)

---

## Quick Links

- **[Product Requirements Document](./PRD_RESTAURANT_SUPPLY_CHAIN.md)** - Complete product vision and requirements
- **[Feature Mapping](./FEATURE_MAPPING.md)** - Existing features vs new requirements
- **[Database Schema](./DATABASE_SCHEMA_SUPPLY_CHAIN.md)** - Complete database design

---

## Executive Summary

**What We're Building:**
A mobile-first B2B marketplace connecting restaurants with food suppliers in Iraq, replacing WhatsApp-based ordering with a modern digital platform.

**Why We Can Build This Fast:**
The existing FastAPI SQLModel Starter provides ~60% of required infrastructure:
- ✅ Authentication & JWT tokens
- ✅ RBAC with permissions
- ✅ Audit logging
- ✅ Database layer (async SQLModel)
- ✅ Security features (rate limiting, OWASP headers)
- ✅ i18n support (Arabic/English)

**What We Need to Add:**
- Restaurant & supplier management
- Product catalog with search
- Order placement & tracking
- Delivery management
- Payment integration
- Notifications (SMS, push, email)
- Mobile apps (iOS/Android)

---

## Sprint Breakdown (12 Weeks)

### Sprint 1-2: Foundation (Weeks 1-2)

**Goal:** Extend existing system for supply chain domain

#### Week 1: Database & Models

**Tasks:**
1. **Extend User Model** (2 days)
   - Add `phone_number`, `phone_verified`, `language_preference`
   - Add `restaurant_id`, `supplier_id` foreign keys
   - Create migration
   - Update user registration endpoint

2. **Create Core Models** (3 days)
   - `Restaurant` model + schemas
   - `Supplier` model + schemas
   - Create migrations
   - Add indexes

**Deliverables:**
- [ ] Migration: `001_extend_user_model.py`
- [ ] Migration: `002_create_restaurant_supplier.py`
- [ ] Models: `app/models/restaurant.py`
- [ ] Models: `app/models/supplier.py`
- [ ] Schemas: `app/schemas/restaurant.py`
- [ ] Schemas: `app/schemas/supplier.py`

---

#### Week 2: RBAC & Authentication

**Tasks:**
1. **Extend RBAC System** (2 days)
   - Add new roles (restaurant_owner, supplier_admin, driver)
   - Add new permissions (restaurant:*, supplier:*, product:*, order:*)
   - Update seed data
   - Create migration

2. **Phone Verification** (2 days)
   - Integrate Twilio SMS
   - Create OTP generation/verification
   - Add `/auth/verify-phone` endpoint
   - Update registration flow

3. **Testing** (1 day)
   - Unit tests for new models
   - Integration tests for auth flow
   - Test phone verification

**Deliverables:**
- [ ] Migration: `003_add_supply_chain_roles_permissions.py`
- [ ] Service: `app/services/sms.py` (Twilio integration)
- [ ] Endpoint: `app/api/v1/auth.py` (extend with phone verification)
- [ ] Tests: `tests/core/test_sms.py`
- [ ] Tests: `tests/api/v1/test_phone_verification.py`

**Environment Variables:**
```env
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_PHONE_NUMBER=+964xxxxxxxxx
```

---

### Sprint 3-4: Restaurant & Supplier Management (Weeks 3-4)

#### Week 3: Restaurant Module

**Tasks:**
1. **Restaurant CRUD** (3 days)
   - Create CRUD class: `app/crud/restaurant.py`
   - Implement endpoints: `app/api/v1/restaurants.py`
     - POST `/restaurants` - Create restaurant
     - GET `/restaurants` - List restaurants (admin)
     - GET `/restaurants/{id}` - Get restaurant details
     - PUT `/restaurants/{id}` - Update restaurant
     - DELETE `/restaurants/{id}` - Soft delete
   - Add team management:
     - POST `/restaurants/{id}/staff` - Add staff member
     - DELETE `/restaurants/{id}/staff/{user_id}` - Remove staff

2. **Verification Workflow** (1 day)
   - Admin approval endpoint
   - Email notification on approval
   - Status tracking

3. **Testing** (1 day)
   - CRUD operation tests
   - Permission tests
   - Verification flow tests

**Deliverables:**
- [ ] CRUD: `app/crud/restaurant.py`
- [ ] API: `app/api/v1/restaurants.py`
- [ ] Tests: `tests/api/v1/test_restaurants.py`

---

#### Week 4: Supplier Module

**Tasks:**
1. **Supplier CRUD** (3 days)
   - Create CRUD class: `app/crud/supplier.py`
   - Implement endpoints: `app/api/v1/suppliers.py`
     - POST `/suppliers` - Create supplier
     - GET `/suppliers` - List suppliers (with filters)
     - GET `/suppliers/search` - Search by name/category
     - GET `/suppliers/{id}` - Get supplier details
     - PUT `/suppliers/{id}` - Update supplier
     - DELETE `/suppliers/{id}` - Soft delete

2. **Supplier Dashboard** (1 day)
   - GET `/suppliers/{id}/stats` - Basic metrics

3. **Testing** (1 day)
   - CRUD tests
   - Search functionality tests

**Deliverables:**
- [ ] CRUD: `app/crud/supplier.py`
- [ ] API: `app/api/v1/suppliers.py`
- [ ] Tests: `tests/api/v1/test_suppliers.py`

---

### Sprint 5-6: Product Catalog (Weeks 5-6)

#### Week 5: Categories & Products

**Tasks:**
1. **Category System** (1 day)
   - Create `Category` model
   - Hierarchical category support
   - CRUD endpoints: `app/api/v1/categories.py`

2. **Product Model** (2 days)
   - Create `Product` model + schemas
   - Migration
   - CRUD class: `app/crud/product.py`

3. **Product Endpoints** (2 days)
   - POST `/products` - Create product (supplier only)
   - GET `/products` - List all products (with filters)
   - GET `/products/search` - Full-text search (Arabic/English)
   - GET `/products/{id}` - Product details
   - PUT `/products/{id}` - Update product
   - DELETE `/products/{id}` - Soft delete
   - GET `/suppliers/{id}/products` - Supplier's catalog

**Deliverables:**
- [ ] Migration: `004_create_categories_products.py`
- [ ] Models: `app/models/category.py`, `app/models/product.py`
- [ ] CRUD: `app/crud/product.py`
- [ ] API: `app/api/v1/categories.py`, `app/api/v1/products.py`
- [ ] Tests: `tests/api/v1/test_products.py`

---

#### Week 6: Product Features

**Tasks:**
1. **Image Upload** (2 days)
   - AWS S3 integration
   - Service: `app/services/storage.py`
   - Endpoint: POST `/upload/image`
   - Image resize/optimization (Pillow)

2. **Stock Management** (1 day)
   - Stock update endpoint
   - Low stock alerts (background job)

3. **Search Optimization** (1 day)
   - PostgreSQL full-text search (Arabic + English)
   - Search ranking/relevance
   - Filter by category, price, supplier

4. **Testing** (1 day)
   - Image upload tests
   - Search tests
   - Stock management tests

**Deliverables:**
- [ ] Service: `app/services/storage.py`
- [ ] API: `app/api/v1/upload.py`
- [ ] Background Task: `app/tasks/inventory.py`
- [ ] Tests: `tests/services/test_storage.py`

**Environment Variables:**
```env
AWS_ACCESS_KEY_ID=xxxxx
AWS_SECRET_ACCESS_KEY=xxxxx
AWS_S3_BUCKET=supply-chain-images
AWS_REGION=me-south-1  # Bahrain (closest to Iraq)
```

---

### Sprint 7-8: Order Management (Weeks 7-8)

#### Week 7: Order Creation

**Tasks:**
1. **Order Models** (1 day)
   - Create `Order` and `OrderItem` models
   - Migration

2. **Order Endpoints** (3 days)
   - POST `/orders` - Create order
     - Validate products exist
     - Check stock availability
     - Calculate totals
     - Deduct stock
   - GET `/orders` - List orders (filtered by role)
     - Restaurant: own orders
     - Supplier: orders to fulfill
     - Driver: assigned deliveries
   - GET `/orders/{id}` - Order details
   - PUT `/orders/{id}/status` - Update status
   - POST `/orders/{id}/cancel` - Cancel order

3. **Order Number Generation** (1 day)
   - Generate unique order numbers: `ORD-20250119-0001`
   - Redis counter for sequence

**Deliverables:**
- [ ] Migration: `005_create_orders.py`
- [ ] Models: `app/models/order.py`
- [ ] CRUD: `app/crud/order.py`
- [ ] API: `app/api/v1/orders.py`
- [ ] Service: `app/services/order.py`
- [ ] Tests: `tests/api/v1/test_orders.py`

---

#### Week 8: Order Workflow

**Tasks:**
1. **Order Status Workflow** (2 days)
   - State machine implementation
   - Status transitions:
     - `pending → confirmed → preparing → out_for_delivery → delivered`
   - Validation rules (who can update to what status)
   - Audit log integration

2. **Supplier Order Management** (1 day)
   - POST `/orders/{id}/confirm` - Accept order
   - POST `/orders/{id}/reject` - Reject order
   - Supplier dashboard endpoint

3. **Reorder Functionality** (1 day)
   - POST `/orders/{id}/reorder` - Clone past order

4. **Testing** (1 day)
   - Order creation tests
   - Status workflow tests
   - Stock deduction tests
   - Concurrent order tests (race conditions)

**Deliverables:**
- [ ] Service: `app/services/order_workflow.py`
- [ ] Tests: `tests/services/test_order_workflow.py`
- [ ] Tests: `tests/api/v1/test_order_status.py`

---

### Sprint 9-10: Delivery & Payments (Weeks 9-10)

#### Week 9: Delivery Module

**Tasks:**
1. **Delivery Model** (1 day)
   - Create `Delivery` model
   - Migration

2. **Delivery Endpoints** (2 days)
   - POST `/deliveries` - Assign delivery to driver
   - GET `/deliveries` - List deliveries (driver view)
   - GET `/deliveries/{id}` - Delivery details
   - PUT `/deliveries/{id}/status` - Update delivery status
   - POST `/deliveries/{id}/proof` - Upload proof of delivery

3. **Google Maps Integration** (1 day)
   - Geocoding addresses
   - Distance calculation
   - Route optimization (for multiple deliveries)

4. **Testing** (1 day)
   - Delivery assignment tests
   - Proof of delivery tests

**Deliverables:**
- [ ] Migration: `006_create_deliveries.py`
- [ ] Models: `app/models/delivery.py`
- [ ] API: `app/api/v1/deliveries.py`
- [ ] Service: `app/services/maps.py`
- [ ] Tests: `tests/api/v1/test_deliveries.py`

**Environment Variables:**
```env
GOOGLE_MAPS_API_KEY=xxxxx
```

---

#### Week 10: Payments

**Tasks:**
1. **Payment Model** (1 day)
   - Create `Payment` model
   - Migration

2. **Cash on Delivery** (1 day)
   - POST `/payments` - Record payment
   - Update order payment status
   - Driver payment collection

3. **Bank Transfer** (1 day)
   - Upload receipt functionality
   - Admin verification workflow

4. **Invoice Generation** (2 days)
   - PDF generation (ReportLab)
   - Arabic/English invoices
   - Upload to S3
   - Email invoice to customer

**Deliverables:**
- [ ] Migration: `007_create_payments.py`
- [ ] Models: `app/models/payment.py`
- [ ] API: `app/api/v1/payments.py`
- [ ] Service: `app/services/invoice.py`
- [ ] Tests: `tests/services/test_invoice.py`

**Dependencies:**
```bash
pip install reportlab
pip install arabic-reshaper python-bidi  # For Arabic PDF support
```

---

### Sprint 11: Notifications & Reviews (Week 11)

#### Week 11: Multi-Channel Notifications

**Tasks:**
1. **Notification Model** (1 day)
   - Create `Notification` model
   - Migration
   - CRUD endpoints

2. **Celery Setup** (1 day)
   - Install Celery + Redis
   - Configure task queue
   - Create base tasks

3. **SMS Notifications** (1 day)
   - Order confirmation SMS
   - Delivery updates SMS
   - Task: `app/tasks/notifications.py`

4. **Push Notifications** (1 day)
   - Firebase Cloud Messaging setup
   - Send push on order updates
   - Service: `app/services/push.py`

5. **Email Notifications** (1 day)
   - SendGrid/AWS SES integration
   - Email templates
   - Invoice email

**Deliverables:**
- [ ] Migration: `008_create_notifications.py`
- [ ] Models: `app/models/notification.py`
- [ ] Service: `app/services/push.py`
- [ ] Service: `app/services/email.py`
- [ ] Tasks: `app/tasks/notifications.py`
- [ ] API: `app/api/v1/notifications.py`

**Dependencies:**
```bash
pip install celery
pip install firebase-admin
pip install sendgrid
```

**Environment Variables:**
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
SENDGRID_API_KEY=xxxxx
```

---

#### Week 11 (continued): Reviews

**Tasks:**
1. **Review Model** (1 day)
   - Create `Review` model
   - Migration

2. **Review Endpoints** (1 day)
   - POST `/reviews` - Create review (verified purchase only)
   - GET `/reviews` - List reviews
   - GET `/suppliers/{id}/reviews` - Supplier reviews
   - PUT `/reviews/{id}/response` - Supplier response

3. **Rating Aggregation** (half day)
   - Trigger to update supplier/product ratings
   - Background job to recalculate ratings

**Deliverables:**
- [ ] Migration: `009_create_reviews.py`
- [ ] Models: `app/models/review.py`
- [ ] API: `app/api/v1/reviews.py`
- [ ] Tasks: `app/tasks/ratings.py`

---

### Sprint 12: Analytics, Testing & Launch (Week 12)

#### Week 12: Analytics & Polish

**Tasks:**
1. **Analytics Endpoints** (2 days)
   - GET `/analytics/restaurant/{id}` - Restaurant dashboard
     - Total spend (daily/weekly/monthly)
     - Top suppliers
     - Most ordered products
   - GET `/analytics/supplier/{id}` - Supplier dashboard
     - Total revenue
     - Top customers
     - Best-selling products
   - GET `/analytics/admin` - Admin dashboard
     - Platform GMV
     - Active users
     - Order volume trends

2. **WebSocket Setup** (1 day)
   - Real-time order updates
   - WS `/ws/orders/{order_id}`
   - Redis pub/sub for broadcasting

3. **Final Testing** (1 day)
   - End-to-end tests
   - Load testing (Locust)
   - Security audit

4. **Documentation** (1 day)
   - API documentation (update `docs/API.md`)
   - Deployment guide
   - User guides (Arabic/English)

**Deliverables:**
- [ ] API: `app/api/v1/analytics.py`
- [ ] WebSocket: `app/api/v1/websockets.py`
- [ ] Tests: `tests/e2e/test_order_flow.py`
- [ ] Docs: Updated API documentation
- [ ] Docs: Deployment guide

---

## Mobile App Development (Parallel Track)

**Platform:** React Native (iOS + Android)

### Weeks 1-4: Setup & Authentication
- React Native project setup (Expo)
- Navigation (React Navigation)
- Authentication screens (login, register, phone verification)
- JWT token management
- Language switcher (Arabic RTL / English)

### Weeks 5-8: Core Features
- Restaurant App:
  - Browse products
  - Search & filter
  - Shopping cart
  - Checkout
  - Order tracking
- Supplier App:
  - Order dashboard
  - Product management
  - Order status updates

### Weeks 9-12: Advanced Features
- Push notifications (Firebase)
- Real-time updates (Socket.io)
- Offline mode
- Image upload (camera/gallery)
- Maps integration (delivery tracking)
- PDF invoice viewer

### Week 12: Testing & Deployment
- Beta testing (TestFlight, Google Play Beta)
- Bug fixes
- App store submission

---

## Infrastructure & DevOps

### Cloud Setup (AWS/DigitalOcean)

**Week 1:**
- [ ] Provision servers (Bahrain region - closest to Iraq)
- [ ] Setup PostgreSQL (RDS or managed database)
- [ ] Setup Redis (ElastiCache or managed Redis)
- [ ] Setup S3 bucket (images, invoices)

**Week 4:**
- [ ] Docker containerization
- [ ] Docker Compose for local dev
- [ ] CI/CD pipeline (GitHub Actions)

**Week 8:**
- [ ] Staging environment
- [ ] Load balancer setup
- [ ] SSL certificates

**Week 12:**
- [ ] Production deployment
- [ ] Monitoring (Sentry, DataDog)
- [ ] Backup automation

---

## Database Migrations Plan

```bash
# Week 1
alembic revision --autogenerate -m "001: Extend user model with phone and language"
alembic revision --autogenerate -m "002: Create restaurant and supplier tables"

# Week 2
alembic revision --autogenerate -m "003: Add supply chain roles and permissions"

# Week 5
alembic revision --autogenerate -m "004: Create categories and products tables"

# Week 7
alembic revision --autogenerate -m "005: Create orders and order_items tables"

# Week 9
alembic revision --autogenerate -m "006: Create deliveries table"

# Week 10
alembic revision --autogenerate -m "007: Create payments table"

# Week 11
alembic revision --autogenerate -m "008: Create notifications table"
alembic revision --autogenerate -m "009: Create reviews table"
```

---

## Testing Strategy

### Unit Tests
- All CRUD operations
- Business logic (order calculations, stock management)
- Utilities (phone formatting, price calculations)

**Target:** 80%+ code coverage

### Integration Tests
- API endpoints (all routes)
- Database operations
- External services (mocked: Twilio, AWS S3)

### E2E Tests
- Complete order flow (browse → order → delivery → payment)
- User registration → verification → profile update
- Supplier onboarding → product creation → order fulfillment

### Load Tests
- 100 concurrent users
- 1,000 orders/hour
- Response time < 200ms (p95)

**Tools:**
- pytest
- pytest-asyncio
- pytest-cov
- Locust (load testing)

---

## Success Metrics (MVP Launch)

### Technical Metrics
- [ ] API response time < 200ms (p95)
- [ ] 99.9% uptime
- [ ] Zero critical security vulnerabilities
- [ ] 80%+ test coverage
- [ ] < 1% error rate

### Business Metrics (Month 1 Post-Launch)
- [ ] 20+ restaurants onboarded
- [ ] 5+ suppliers onboarded
- [ ] 100+ products in catalog
- [ ] 50+ orders placed
- [ ] < 5% order cancellation rate
- [ ] 4.0+ average app rating

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Supplier adoption low | Medium | High | White-glove onboarding, free trial, dedicated support |
| SMS delivery issues | Low | Medium | Fallback to email, use reliable provider (Twilio) |
| Payment fraud | Low | High | Start with COD only, manual verification |
| Database performance | Low | Medium | Proper indexing, caching, connection pooling |
| API downtime | Low | High | Load balancer, auto-scaling, health checks |
| Mobile app crashes | Medium | High | Comprehensive testing, error tracking (Sentry) |

---

## Team Responsibilities

### Backend Team (2 devs)
- Extend existing models
- Implement new APIs
- Background tasks (Celery)
- Database migrations
- Integration testing

### Frontend/Mobile Team (2 devs)
- React Native apps
- UI/UX implementation
- API integration
- Push notifications
- Offline mode

### QA Engineer (1)
- Test plan creation
- Manual testing
- Automated E2E tests
- Load testing
- Bug reporting

### DevOps Engineer (1)
- Infrastructure setup
- CI/CD pipelines
- Monitoring & alerts
- Database backups
- Production deployment

---

## Dependencies & Prerequisites

### Before Starting Development

**Backend:**
- [x] Python 3.11+ installed
- [x] PostgreSQL 15+ installed
- [x] Redis 7+ installed
- [ ] Twilio account (SMS)
- [ ] AWS account (S3, RDS)
- [ ] Firebase project (push notifications)
- [ ] SendGrid account (email)

**Mobile:**
- [ ] Node.js 18+ installed
- [ ] React Native CLI
- [ ] Xcode (for iOS)
- [ ] Android Studio (for Android)
- [ ] Expo account

**Tools:**
- [ ] GitHub repository
- [ ] Sentry account (error tracking)
- [ ] Postman workspace (API testing)

---

## Quick Start Commands

### Backend Setup
```bash
# Clone repo
cd fastapi-sqlmodel-starter-v1

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials

# Run migrations
alembic upgrade head

# Seed database
python scripts/seed_supply_chain_data.py

# Start server
uvicorn app.main:app --reload

# Start Celery worker (separate terminal)
celery -A app.tasks worker --loglevel=info
```

### Mobile Setup
```bash
# Create React Native project
npx create-expo-app SupplyChainApp
cd SupplyChainApp

# Install dependencies
npm install @react-navigation/native
npm install axios
npm install @react-native-firebase/messaging

# Start development
npx expo start
```

---

## Weekly Checklist Template

**Week X:**

- [ ] Sprint planning meeting (Monday)
- [ ] Daily standups (15 min)
- [ ] Code reviews (ongoing)
- [ ] Deploy to staging (Thursday)
- [ ] Sprint demo (Friday)
- [ ] Sprint retrospective (Friday)
- [ ] Update roadmap (Friday)

---

## Launch Checklist (Week 12)

### Technical
- [ ] All tests passing (unit, integration, E2E)
- [ ] Code review completed
- [ ] Security audit passed
- [ ] Load testing passed (1000 orders/hour)
- [ ] Database backups configured
- [ ] Monitoring & alerts configured
- [ ] SSL certificates installed
- [ ] Domain configured
- [ ] Email sending verified
- [ ] SMS sending verified
- [ ] Push notifications tested

### Content
- [ ] 20+ restaurants onboarded (test users)
- [ ] 5+ suppliers onboarded (test users)
- [ ] 100+ products in catalog
- [ ] Categories populated
- [ ] Privacy policy published
- [ ] Terms of service published
- [ ] User guides written (Arabic/English)

### Mobile Apps
- [ ] iOS app submitted to App Store
- [ ] Android app submitted to Google Play
- [ ] App screenshots prepared
- [ ] App descriptions written (Arabic/English)

### Business
- [ ] Customer support email setup
- [ ] Support team trained
- [ ] Pricing/commission finalized
- [ ] Legal compliance verified
- [ ] Bank account setup (for payouts)

---

## Post-Launch (Month 2-3)

### Priorities
1. Monitor error rates & performance
2. Gather user feedback
3. Fix critical bugs
4. Iterate on UI/UX
5. Onboard more suppliers/restaurants
6. Add payment gateways (Qi Card, ZainCash)
7. Implement inventory management features
8. Build analytics dashboards

---

## Resources

### Documentation
- [Product Requirements Document](./PRD_RESTAURANT_SUPPLY_CHAIN.md)
- [Feature Mapping](./FEATURE_MAPPING.md)
- [Database Schema](./DATABASE_SCHEMA_SUPPLY_CHAIN.md)
- [API Documentation](./API.md)
- [Development Guide](./DEVELOPMENT.md)
- [Deployment Guide](./DEPLOYMENT.md)

### External APIs
- [Twilio SMS API](https://www.twilio.com/docs/sms)
- [Google Maps API](https://developers.google.com/maps)
- [Firebase Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [SendGrid Email API](https://sendgrid.com/docs/api-reference/)

### Libraries & Frameworks
- [FastAPI](https://fastapi.tiangolo.com)
- [SQLModel](https://sqlmodel.tiangolo.com)
- [Celery](https://docs.celeryproject.org)
- [React Native](https://reactnative.dev)

---

## Contact & Support

**Project Lead:** [Your Name]
**Backend Lead:** [Name]
**Mobile Lead:** [Name]
**DevOps Lead:** [Name]

**Slack Channel:** #supply-chain-project
**GitHub Repo:** https://github.com/yourorg/supply-chain-backend
**Jira Board:** https://yourorg.atlassian.net/supply-chain

---

**Let's build something amazing! 🚀**

*Last Updated: January 2025*
