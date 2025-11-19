"""
API v1 Router

Combines all v1 endpoints into a single router.
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, roles, audit, restaurants, suppliers

# Create API v1 router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(roles.router)
api_router.include_router(audit.router)

# Supply Chain routers
api_router.include_router(restaurants.router)
api_router.include_router(suppliers.router)

# Add your custom domain-specific routers here:
# from app.api.v1 import products
# api_router.include_router(products.router)
