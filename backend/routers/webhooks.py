"""Webhook management API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Webhook, WebhookLog
from schemas import WebhookCreate, WebhookUpdate, WebhookResponse, WebhookLogResponse
from auth import require_admin

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new webhook (admin only)."""
    webhook = Webhook(
        name=webhook_data.name,
        url=webhook_data.url,
        secret=webhook_data.secret,
        events=webhook_data.events,
        is_active=webhook_data.is_active,
        created_by=current_user.id
    )

    db.add(webhook)
    db.commit()
    db.refresh(webhook)

    return webhook


@router.get("", response_model=List[WebhookResponse])
async def list_webhooks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all webhooks (admin only)."""
    webhooks = db.query(Webhook).offset(skip).limit(limit).all()
    return webhooks


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get webhook by ID (admin only)."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    return webhook


@router.patch("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update webhook (admin only)."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Update fields
    update_data = webhook_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(webhook, field, value)

    db.commit()
    db.refresh(webhook)

    return webhook


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete webhook (admin only)."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    db.delete(webhook)
    db.commit()


@router.get("/{webhook_id}/logs", response_model=List[WebhookLogResponse])
async def get_webhook_logs(
    webhook_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get webhook delivery logs (admin only)."""
    webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    logs = db.query(WebhookLog).filter(
        WebhookLog.webhook_id == webhook_id
    ).order_by(WebhookLog.triggered_at.desc()).offset(skip).limit(limit).all()

    return logs
