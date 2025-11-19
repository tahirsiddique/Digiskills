"""Ticket template management API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, TicketTemplate
from schemas import TemplateCreate, TemplateUpdate, TemplateResponse
from auth import get_current_user, require_technician

router = APIRouter(prefix="/api/templates", tags=["Templates"])


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Create a new ticket template (technician/admin only)."""
    # Check if template name already exists
    existing = db.query(TicketTemplate).filter(TicketTemplate.name == template_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Template name already exists"
        )

    template = TicketTemplate(
        name=template_data.name,
        title=template_data.title,
        description=template_data.description,
        priority=template_data.priority,
        category_id=template_data.category_id,
        created_by=current_user.id
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all ticket templates."""
    templates = db.query(TicketTemplate).offset(skip).limit(limit).all()
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get template by ID."""
    template = db.query(TicketTemplate).filter(TicketTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    return template


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    template_data: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Update template (technician/admin only)."""
    template = db.query(TicketTemplate).filter(TicketTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    # Update fields
    update_data = template_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(template, field, value)

    db.commit()
    db.refresh(template)

    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Delete template (technician/admin only)."""
    template = db.query(TicketTemplate).filter(TicketTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )

    db.delete(template)
    db.commit()
