"""SLA policy management API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, SLAPolicy
from schemas import SLAPolicyCreate, SLAPolicyUpdate, SLAPolicyResponse
from auth import require_admin

router = APIRouter(prefix="/api/sla", tags=["SLA Policies"])


@router.post("", response_model=SLAPolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_sla_policy(
    sla_data: SLAPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new SLA policy (admin only)."""
    # Check if policy name already exists
    existing = db.query(SLAPolicy).filter(SLAPolicy.name == sla_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="SLA policy name already exists"
        )

    sla_policy = SLAPolicy(
        name=sla_data.name,
        description=sla_data.description,
        priority=sla_data.priority,
        response_time_hours=sla_data.response_time_hours,
        resolution_time_hours=sla_data.resolution_time_hours,
        is_active=sla_data.is_active
    )

    db.add(sla_policy)
    db.commit()
    db.refresh(sla_policy)

    return sla_policy


@router.get("", response_model=List[SLAPolicyResponse])
async def list_sla_policies(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all SLA policies (admin only)."""
    query = db.query(SLAPolicy)

    if active_only:
        query = query.filter(SLAPolicy.is_active == True)

    sla_policies = query.offset(skip).limit(limit).all()
    return sla_policies


@router.get("/{sla_id}", response_model=SLAPolicyResponse)
async def get_sla_policy(
    sla_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get SLA policy by ID (admin only)."""
    sla_policy = db.query(SLAPolicy).filter(SLAPolicy.id == sla_id).first()

    if not sla_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SLA policy not found"
        )

    return sla_policy


@router.patch("/{sla_id}", response_model=SLAPolicyResponse)
async def update_sla_policy(
    sla_id: int,
    sla_data: SLAPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update SLA policy (admin only)."""
    sla_policy = db.query(SLAPolicy).filter(SLAPolicy.id == sla_id).first()

    if not sla_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SLA policy not found"
        )

    # Update fields
    update_data = sla_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(sla_policy, field, value)

    db.commit()
    db.refresh(sla_policy)

    return sla_policy


@router.delete("/{sla_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sla_policy(
    sla_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete SLA policy (admin only)."""
    sla_policy = db.query(SLAPolicy).filter(SLAPolicy.id == sla_id).first()

    if not sla_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SLA policy not found"
        )

    # Check if policy is in use
    if sla_policy.tickets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete SLA policy that is in use by tickets"
        )

    db.delete(sla_policy)
    db.commit()
