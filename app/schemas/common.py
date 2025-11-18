"""
Common Schemas

This module contains reusable schemas used across the application:
- Pagination
- Generic responses
- Error responses
- Filter/Sort parameters

Why separate common schemas?
- DRY principle (Don't Repeat Yourself)
- Consistent API responses
- Easier to maintain
- Reusable across all endpoints
"""

from typing import Generic, TypeVar, Optional, List, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict

# Generic type variable for pagination
T = TypeVar("T")

# Base config for all schemas (snake_case - Python standard)
base_config = ConfigDict(
    from_attributes=True,  # Allow conversion from ORM models
)

class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints.

    Query Parameters:
    - skip_count: Number of records to skip (offset)
    - max_count: Maximum number of records to return

    Example:
        GET /students?skip_count=20&max_count=10
        # Returns students 21-30
    """
    model_config = base_config

    skip_count: int = Field(
        default=0,
        ge=0,
        description="Number of records to skip",
        examples=[0, 20, 40],
    )
    max_count: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of records to return",
        examples=[10, 20, 50],
    )

    @property
    def skip(self) -> int:
        """Alias for skip_count (for backward compatibility)."""
        return self.skip_count

    @property
    def limit(self) -> int:
        """Alias for max_count (for backward compatibility)."""
        return self.max_count

    @property
    def offset(self) -> int:
        """Alias for skip_count (more SQL-like)."""
        return self.skip_count

    @property
    def page(self) -> int:
        """Calculate current page number (1-indexed)."""
        return (self.skip_count // self.max_count) + 1

class SortParams(BaseModel):
    """
    Sorting parameters for list endpoints.

    Query Parameters:
    - sort_by: Field name to sort by
    - sort_order: "asc" or "desc"

    Example:
        GET /students?sort_by=full_name&sort_order=asc
    """
    model_config = base_config

    sort_by: Optional[str] = Field(
        default="created_at",
        description="Field name to sort by",
        examples=["created_at", "id", "full_name"],
    )
    sort_order: str = Field(
        default="asc",
        description="Sort order: 'asc' or 'desc'",
        examples=["asc", "desc"],
    )

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, v: str) -> str:
        """Validate sort order."""
        v = v.lower()
        if v not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return v

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response.

    Contains:
    - items: List of results
    - total: Total count of all records
    - skip: Current offset
    - limit: Current page size
    - page: Current page number
    - pages: Total number of pages

    Example:
        {
            "items": [...],
            "total": 100,
            "skip": 20,
            "limit": 10,
            "page": 3,
            "pages": 10
        }
    """
    model_config = base_config

    items: List[T] = Field(description="List of items")
    total: int = Field(description="Total count of all items")
    skip: int = Field(description="Number of items skipped")
    limit: int = Field(description="Maximum items per page")
    page: int = Field(description="Current page number (1-indexed)")
    pages: int = Field(description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        skip: int,
        limit: int,
    ) -> "PaginatedResponse[T]":
        """
        Create a paginated response.

        Args:
            items: List of items for current page
            total: Total count of all items
            skip: Number of items skipped
            limit: Page size

        Returns:
            PaginatedResponse with calculated pagination info
        """
        pages = (total + limit - 1) // limit  # Ceiling division
        page = (skip // limit) + 1

        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            page=page,
            pages=pages,
        )

class MessageResponse(BaseModel):
    """
    Simple message response.

    Used for success messages, confirmations, etc.

    Example:
        {"message": "Student created successfully"}
    """
    model_config = base_config

    message: str = Field(description="Response message")

class ErrorDetail(BaseModel):
    """
    Error detail structure.

    Contains:
    - field: Field name (if validation error)
    - message: Error message
    - code: Error code (optional)
    """
    model_config = base_config

    field: Optional[str] = Field(
        default=None,
        description="Field name that caused the error",
    )
    message: str = Field(description="Error message")
    code: Optional[str] = Field(
        default=None,
        description="Error code for programmatic handling",
    )

class ErrorResponse(BaseModel):
    """
    Error response structure.

    Consistent error format across the API.

    Example:
        {
            "message": "Validation failed",
            "details": [
                {
                    "field": "email",
                    "message": "Invalid email format",
                    "code": "INVALID_EMAIL"
                }
            ]
        }
    """

    model_config = base_config

    message: str = Field(description="Main error message")
    details: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="Detailed error information",
    )

class IDResponse(BaseModel):
    """
    Response containing just an ID.

    Used when creating resources.

    Example:
        {"id": 123}
    """

    model_config = base_config

    id: UUID = Field(description="Resource ID")

class StatusResponse(BaseModel):
    """
    Status response with additional data.

    Example:
        {
            "status": "success",
            "message": "Operation completed",
            "data": {...}
        }
    """

    model_config = base_config

    status: str = Field(description="Status: success, error, pending")
    message: str = Field(description="Status message")
    data: Optional[Any] = Field(default=None, description="Additional data")

class HealthResponse(BaseModel):
    """
    Health check response.

    Example:
        {
            "status": "healthy",
            "version": "2.0.0",
            "database": "connected",
            "redis": "connected",
            "timestamp": "2024-01-01T12:00:00Z"
        }
    """

    model_config = base_config

    status: str = Field(description="Health status: healthy, unhealthy, degraded")
    version: str = Field(description="API version")
    database: str = Field(description="Database status: connected, disconnected")
    redis: Optional[str] = Field(
        default=None,
        description="Redis status: connected, disconnected, disabled"
    )
    timestamp: str = Field(description="Current server timestamp")

class BulkOperationResponse(BaseModel):
    """
    Response for bulk operations.

    Example:
        {
            "successful": 45,
            "failed": 5,
            "total": 50,
            "errors": [...]
        }
    """

    model_config = base_config

    successful: int = Field(description="Number of successful operations")
    failed: int = Field(description="Number of failed operations")
    total: int = Field(description="Total number of operations")
    errors: Optional[List[ErrorDetail]] = Field(
        default=None,
        description="List of errors (if any)",
    )

class FilterParams(BaseModel):
    """
    Common filter parameters.

    Can be extended by specific endpoints.

    Example:
        GET /students?search=John&is_active=true
    """

    model_config = base_config

    search: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Search query (searches across multiple fields)",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Filter by active status",
    )
    created_after: Optional[str] = Field(
        default=None,
        description="Filter by creation date (YYYY-MM-DD)",
    )
    created_before: Optional[str] = Field(
        default=None,
        description="Filter by creation date (YYYY-MM-DD)",
    )

# Type aliases for common response types
SuccessResponse = MessageResponse
CreatedResponse = IDResponse

# Export base_config for use in other schema files
__all__ = [
    "base_config",
    "PaginationParams",
    "SortParams",
    "PaginatedResponse",
    "MessageResponse",
    "ErrorDetail",
    "ErrorResponse",
    "IDResponse",
    "StatusResponse",
    "HealthResponse",
    "BulkOperationResponse",
    "FilterParams",
    "SuccessResponse",
    "CreatedResponse",
]
