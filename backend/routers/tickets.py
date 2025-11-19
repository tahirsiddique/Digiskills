"""Ticket management API routes."""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from database import get_db
from models import User, Ticket, TicketStatus, TicketPriority, UserRole
from schemas import TicketCreate, TicketUpdate, TicketResponse
from auth import get_current_user, require_technician

router = APIRouter(prefix="/api/tickets", tags=["Tickets"])


def generate_ticket_number(db: Session) -> str:
    """Generate unique ticket number."""
    # Get the latest ticket number
    latest_ticket = db.query(Ticket).order_by(Ticket.id.desc()).first()

    if latest_ticket:
        # Extract number from ticket_number (e.g., "TKT-00001" -> 1)
        try:
            last_num = int(latest_ticket.ticket_number.split("-")[1])
            new_num = last_num + 1
        except (IndexError, ValueError):
            new_num = 1
    else:
        new_num = 1

    return f"TKT-{new_num:05d}"


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ticket."""
    ticket = Ticket(
        ticket_number=generate_ticket_number(db),
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        category_id=ticket_data.category_id,
        created_by=current_user.id,
        status=TicketStatus.NEW
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return ticket


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    skip: int = 0,
    limit: int = 100,
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    assigned_to_me: bool = False,
    created_by_me: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List tickets with filters."""
    query = db.query(Ticket)

    # Regular users can only see their own tickets
    if current_user.role == UserRole.USER:
        query = query.filter(
            or_(
                Ticket.created_by == current_user.id,
                Ticket.assigned_to == current_user.id
            )
        )
    else:
        # Technicians and admins can see all tickets or filter
        if assigned_to_me:
            query = query.filter(Ticket.assigned_to == current_user.id)
        if created_by_me:
            query = query.filter(Ticket.created_by == current_user.id)

    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)

    tickets = query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get ticket by ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id and ticket.assigned_to != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this ticket"
            )

    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Check permissions
    if current_user.role == UserRole.USER:
        if ticket.created_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this ticket"
            )
        # Regular users can't assign tickets or change certain fields
        ticket_data.assigned_to = None
        ticket_data.status = None

    # Update fields
    update_data = ticket_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            setattr(ticket, field, value)

    # Update timestamps based on status
    if ticket_data.status == TicketStatus.RESOLVED and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()
    elif ticket_data.status == TicketStatus.CLOSED and not ticket.closed_at:
        ticket.closed_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Delete ticket (technician/admin only)."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    db.delete(ticket)
    db.commit()


@router.post("/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: int,
    assignee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_technician)
):
    """Assign ticket to a technician."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )

    # Verify assignee exists and is a technician
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignee not found"
        )

    if assignee.role not in [UserRole.TECHNICIAN, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only assign to technicians or admins"
        )

    ticket.assigned_to = assignee_id
    ticket.status = TicketStatus.ASSIGNED

    db.commit()
    db.refresh(ticket)

    return ticket
