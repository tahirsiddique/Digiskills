"""Comment management API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User, Ticket, TicketComment, UserRole
from schemas import CommentCreate, CommentResponse
from auth import get_current_user

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

    db.add(comment)
    db.commit()
    db.refresh(comment)

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
