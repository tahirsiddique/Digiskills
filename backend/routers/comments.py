"""Comment management API routes."""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Ticket, TicketComment, UserRole
from schemas import CommentCreate, CommentResponse
from auth import get_current_user
from email_service import email_service

router = APIRouter(prefix="/api/comments", tags=["Comments"])


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on a ticket."""
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == comment_data.ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check if user has access to the ticket
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id and ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to comment on this ticket"
            )
        # Regular users cannot create internal comments
        if comment_data.is_internal:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create internal comments"
            )

    comment = TicketComment(
        ticket_id=comment_data.ticket_id,
        user_id=current_user.id,
        comment_text=comment_data.comment_text,
        is_internal=comment_data.is_internal
    )

    # Mark first response time for SLA tracking
    if not ticket.first_response_at:
        ticket.first_response_at = datetime.utcnow()

    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Send email notification to ticket creator and assignee (if not internal comment)
    if not comment_data.is_internal:
        # Notify creator if they didn't write the comment
        if ticket.created_by != current_user.id:
            creator = db.query(User).filter(User.id == ticket.created_by).first()
            if creator:
                await email_service.send_new_comment_notification(
                    ticket_number=ticket.ticket_number,
                    ticket_id=ticket.id,
                    title=ticket.title,
                    commenter_name=current_user.first_name or current_user.username,
                    comment_text=comment_data.comment_text,
                    recipient_email=creator.email,
                    recipient_name=creator.first_name or creator.username
                )

        # Notify assignee if they didn't write the comment and are not the creator
        if ticket.assigned_to and ticket.assigned_to != current_user.id and ticket.assigned_to != ticket.created_by:
            assignee = db.query(User).filter(User.id == ticket.assigned_to).first()
            if assignee:
                await email_service.send_new_comment_notification(
                    ticket_number=ticket.ticket_number,
                    ticket_id=ticket.id,
                    title=ticket.title,
                    commenter_name=current_user.first_name or current_user.username,
                    comment_text=comment_data.comment_text,
                    recipient_email=assignee.email,
                    recipient_name=assignee.first_name or assignee.username
                )

    return comment


@router.get("/ticket/{ticket_id}", response_model=List[CommentResponse])
async def list_ticket_comments(
    ticket_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all comments for a ticket."""
    # Verify ticket exists
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check if user has access to the ticket
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id and ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view comments on this ticket"
            )

    query = db.query(TicketComment).filter(TicketComment.ticket_id == ticket_id)

    # Regular users cannot see internal comments
    if current_user.role == UserRole.USER:
        query = query.filter(TicketComment.is_internal == False)

    comments = query.order_by(TicketComment.created_at.asc()).offset(skip).limit(limit).all()
    return comments


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment."""
    comment = db.query(TicketComment).filter(TicketComment.id == comment_id).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found"
        )

    # Only comment owner or admin can delete
    if comment.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment"
        )

    db.delete(comment)
    db.commit()
