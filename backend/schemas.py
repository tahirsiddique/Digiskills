"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import UserRole, TicketPriority, TicketStatus, SLAPriority


# User Schemas
class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    """Schema for user creation."""
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Authentication Schemas
class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    user_id: Optional[int] = None
    username: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


# Category Schemas
class CategoryBase(BaseModel):
    """Base category schema."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    """Schema for category creation."""
    pass


class CategoryResponse(CategoryBase):
    """Schema for category response."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Ticket Schemas
class TicketBase(BaseModel):
    """Base ticket schema."""
    title: str = Field(..., max_length=200)
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category_id: Optional[int] = None


class TicketCreate(TicketBase):
    """Schema for ticket creation."""
    pass


class TicketUpdate(BaseModel):
    """Schema for ticket updates."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    category_id: Optional[int] = None
    assigned_to: Optional[int] = None


class TicketResponse(TicketBase):
    """Schema for ticket response."""
    id: int
    ticket_number: str
    status: TicketStatus
    created_by: int
    assigned_to: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    creator: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


# Comment Schemas
class CommentBase(BaseModel):
    """Base comment schema."""
    comment_text: str
    is_internal: bool = False


class CommentCreate(CommentBase):
    """Schema for comment creation."""
    ticket_id: int


class CommentResponse(CommentBase):
    """Schema for comment response."""
    id: int
    ticket_id: int
    user_id: int
    created_at: datetime
    user: Optional[UserResponse] = None

    model_config = ConfigDict(from_attributes=True)


# Attachment Schemas
class AttachmentResponse(BaseModel):
    """Schema for attachment response."""
    id: int
    ticket_id: int
    file_name: str
    file_size: int
    mime_type: str
    uploaded_by: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


# API Response Schemas
class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorDetail(BaseModel):
    """Error detail schema."""
    field: Optional[str] = None
    message: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    error: dict


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Paginated response schema."""
    success: bool = True
    data: List
    metadata: PaginationMeta


# Template Schemas
class TemplateBase(BaseModel):
    """Base template schema."""
    name: str = Field(..., max_length=100)
    title: str = Field(..., max_length=200)
    description: str
    priority: TicketPriority = TicketPriority.MEDIUM
    category_id: Optional[int] = None


class TemplateCreate(TemplateBase):
    """Schema for template creation."""
    pass


class TemplateUpdate(BaseModel):
    """Schema for template updates."""
    name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[TicketPriority] = None
    category_id: Optional[int] = None


class TemplateResponse(TemplateBase):
    """Schema for template response."""
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    category: Optional[CategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)


# SLA Policy Schemas
class SLAPolicyBase(BaseModel):
    """Base SLA policy schema."""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    priority: SLAPriority
    response_time_hours: float = Field(..., gt=0)
    resolution_time_hours: float = Field(..., gt=0)
    is_active: bool = True


class SLAPolicyCreate(SLAPolicyBase):
    """Schema for SLA policy creation."""
    pass


class SLAPolicyUpdate(BaseModel):
    """Schema for SLA policy updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[SLAPriority] = None
    response_time_hours: Optional[float] = Field(None, gt=0)
    resolution_time_hours: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class SLAPolicyResponse(SLAPolicyBase):
    """Schema for SLA policy response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Search Schema
class TicketSearchParams(BaseModel):
    """Schema for advanced ticket search parameters."""
    query: Optional[str] = None  # Full-text search
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    category_id: Optional[int] = None
    assigned_to: Optional[int] = None
    created_by: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sla_breached: Optional[bool] = None
